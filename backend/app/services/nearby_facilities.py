import json
import math
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FACILITY_FILES = {
    "CHILDCARE": "childcare.json",
    "PARK": "playgrounds.json",
    "HOSPITAL": "hospitals.json",
    "SCHOOL": "schools.json",
    "CULTURE": "culture_centers.json",
}

FACILITY_LABELS = {
    "CHILDCARE": "어린이집",
    "PARK": "공원·놀이터",
    "HOSPITAL": "병원·소아과",
    "SCHOOL": "초등학교",
    "CULTURE": "문화시설",
}

FACILITY_KEYWORDS = {
    "CHILDCARE": [
        "어린이집",
        "유치원",
        "보육시설",
        "보육",
    ],
    "PARK": [
        "공원",
        "놀이터",
        "산책",
    ],
    "HOSPITAL": [
        "병원",
        "소아과",
        "의원",
        "의료",
    ],
    "SCHOOL": [
        "초등학교",
        "학교",
    ],
    "CULTURE": [
        "문화센터",
        "문화시설",
        "문화공간",
    ],
}


def _load_json(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return []

    return data


def _extract_facility_type(message: str) -> str | None:
    """
    사용자 질문에서 시설 종류를 찾는다.
    """

    for facility_type, keywords in FACILITY_KEYWORDS.items():
        if any(keyword in message for keyword in keywords):
            return facility_type

    return None


def _extract_location_text(
    message: str,
    facility_type: str,
) -> str:
    """
    질문에서 시설 관련 단어와 요청 표현을 제거해 장소명만 남긴다.

    예:
    '강남역에서 가까운 어린이집 추천해줘'
    → '강남역'
    """

    location = message.strip()

    for keyword in FACILITY_KEYWORDS[facility_type]:
        location = location.replace(keyword, " ")

    remove_words = [
        "에서",
        "근처",
        "주변",
        "가까운",
        "가장",
        "추천해줘",
        "추천해주세요",
        "추천",
        "알려줘",
        "알려주세요",
        "찾아줘",
        "찾아주세요",
        "어디야",
        "어디",
        "있어",
        "있는",
        "좀",
    ]

    for word in remove_words:
        location = location.replace(word, " ")

    location = re.sub(r"\s+", " ", location).strip()

    return location


def _search_place_coordinates(
    location: str,
) -> dict[str, Any]:
    """
    카카오 로컬 API로 장소명을 검색하고 첫 번째 결과의 좌표를 반환한다.
    """

    api_key = os.getenv("KAKAO_REST_API_KEY")

    if not api_key:
        raise RuntimeError(
            "KAKAO_REST_API_KEY가 없습니다. backend/.env를 확인해주세요."
        )

    params = urlencode(
        {
            "query": location,
            "size": 1,
        }
    )

    url = f"https://dapi.kakao.com/v2/local/search/keyword.json?{params}"

    request = Request(
        url,
        headers={
            "Authorization": f"KakaoAK {api_key}",
        },
    )

    with urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))

    documents = result.get("documents", [])

    if not documents:
        raise ValueError(
            f"'{location}'의 위치를 찾지 못했습니다."
        )

    place = documents[0]

    return {
        "name": place.get("place_name", location),
        "address": (
            place.get("road_address_name")
            or place.get("address_name")
            or ""
        ),
        "latitude": float(place["y"]),
        "longitude": float(place["x"]),
    }


def _calculate_distance_km(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    """
    두 좌표 사이의 직선거리를 Haversine 공식으로 계산한다.
    """

    earth_radius_km = 6371.0

    lat1 = math.radians(latitude1)
    lon1 = math.radians(longitude1)
    lat2 = math.radians(latitude2)
    lon2 = math.radians(longitude2)

    latitude_difference = lat2 - lat1
    longitude_difference = lon2 - lon1

    value = (
        math.sin(latitude_difference / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(longitude_difference / 2) ** 2
    )

    central_angle = 2 * math.atan2(
        math.sqrt(value),
        math.sqrt(1 - value),
    )

    return earth_radius_km * central_angle


def find_nearby_facilities(
    message: str,
    limit: int = 3,
) -> dict[str, Any]:
    """
    사용자 질문을 분석하고 가까운 시설을 반환한다.
    """

    facility_type = _extract_facility_type(message)

    if not facility_type:
        return {
            "reply": (
                "찾고 싶은 시설 종류를 함께 말씀해주세요. "
                "예: 강남역 근처 어린이집 추천해줘"
            ),
            "location": None,
            "facility_type": None,
            "items": [],
        }

    location_text = _extract_location_text(
        message,
        facility_type,
    )

    if not location_text:
        return {
            "reply": (
                "기준이 되는 장소를 함께 입력해주세요. "
                "예: 잠실역 근처 공원 추천해줘"
            ),
            "location": None,
            "facility_type": facility_type,
            "items": [],
        }

    location = _search_place_coordinates(location_text)

    filename = FACILITY_FILES[facility_type]
    facilities = _load_json(filename)

    results = []

    for facility in facilities:
        latitude = facility.get("latitude")
        longitude = facility.get("longitude")

        if latitude is None or longitude is None:
            continue

        try:
            distance = _calculate_distance_km(
                location["latitude"],
                location["longitude"],
                float(latitude),
                float(longitude),
            )
        except (TypeError, ValueError):
            continue

        results.append(
            {
                "id": facility.get("id"),
                "name": facility.get("name", "이름 없음"),
                "type": facility.get("type", facility_type),
                "district": facility.get("district", ""),
                "address": facility.get("address", ""),
                "phone": facility.get("phone", ""),
                "category": facility.get("category", ""),
                "latitude": float(latitude),
                "longitude": float(longitude),
                "distance_km": round(distance, 2),
            }
        )

    results.sort(key=lambda item: item["distance_km"])
    selected = results[:limit]

    label = FACILITY_LABELS[facility_type]

    if not selected:
        reply = (
            f"{location['name']} 주변에서 위치 정보가 있는 "
            f"{label}을 찾지 못했어요."
        )
    else:
        reply_lines = [
            f"{location['name']}에서 가까운 {label}을 알려드릴게요."
        ]

        for index, item in enumerate(selected, start=1):
            phone_text = (
                f" · {item['phone']}"
                if item["phone"]
                else ""
            )

            reply_lines.append(
                f"{index}. {item['name']} "
                f"({item['distance_km']}km)\n"
                f"   {item['address']}{phone_text}"
            )

        reply = "\n".join(reply_lines)

    return {
        "reply": reply,
        "location": location,
        "facility_type": facility_type,
        "items": selected,
    }