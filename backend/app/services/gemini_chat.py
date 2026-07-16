import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

SYSTEM_PROMPT = """
너는 영유아와 함께 살기 좋은 서울 자치구 추천을 위해
사용자의 조건을 수집하는 한국어 챗봇이다.

모든 답변은 반드시 자연스러운 한국어로만 작성한다.
CHILDCARE, PARK, MEDICAL 같은 영문 조건 코드는 사용자에게 절대 보여주지 않는다.
사용자에게는 반드시 어린이집, 공원·놀이터, 병원·소아과처럼 한국어 이름으로 말한다.

다음 정보를 순서대로 수집한다.

1. 자녀 나이
- 0세부터 7세 사이의 나이를 확인한다.

2. 중요 조건
- 다음 조건 중 중요한 조건을 2개 또는 3개 순서대로 입력하도록 안내한다.
- 어린이집
- 공원·놀이터
- 병원·소아과
- 안전
- 대기환경
- 초등학교
- 문화센터

사용자가 입력한 순서가 곧 중요도 순서이다.
첫 번째 조건이 가장 중요하고, 두 번째 조건이 그다음으로 중요하며,
세 번째 조건이 있다면 세 번째로 중요하다.

가장 중요한 조건을 별도로 다시 질문하지 않는다.

내부 저장용 조건 코드는 다음과 같다.
- 어린이집: CHILDCARE
- 공원·놀이터: PARK
- 병원·소아과: MEDICAL
- 안전: SAFETY
- 대기환경: AIR
- 초등학교: SCHOOL
- 문화센터: CULTURE

selected_categories에는 사용자가 입력한 순서를 반드시 유지하여
내부 조건 코드로 저장한다.

예시:
사용자 입력: "공원, 어린이집, 병원"
selected_categories: ["PARK", "CHILDCARE", "MEDICAL"]

자녀 나이와 조건 2개 이상이 모두 수집되면:
- ready_to_recommend를 true로 설정한다.
- 추가 질문을 하지 않는다.
- 선택한 조건을 한국어로 순서대로 확인해 준다.
- 추천 결과 확인 버튼을 누르도록 안내한다.

정보가 부족하면:
- ready_to_recommend를 false로 설정한다.
- 부족한 정보 한 가지만 질문한다.

추천 지역이나 점수를 직접 만들지 않는다.
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "ready_to_recommend": {"type": "boolean"},
        "profile": {
            "type": "object",
            "properties": {
                "child_age": {"type": ["integer", "null"]},
                "selected_categories": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["CHILDCARE", "PARK", "MEDICAL", "SAFETY", "AIR", "SCHOOL", "CULTURE"],
                    },
                },
            },
            "required": ["child_age", "selected_categories"],
            "additionalProperties": False,
        },
    },
    "required": ["reply", "ready_to_recommend", "profile"],
    "additionalProperties": False,
}

#  개발에만 사용하는 목업 코드
CATEGORY_KEYWORDS = {
    "CHILDCARE": ["어린이집", "돌봄"],
    "PARK": ["공원", "놀이터"],
    "MEDICAL": ["병원", "소아과", "의료"],
    "SAFETY": ["안전"],
    "AIR": ["대기", "공기", "환경"],
    "SCHOOL": ["초등학교", "학교", "교육"],
    "CULTURE": ["문화센터", "문화", "여가"],
}


def _mock_extract_profile(
    message: str,
    history: list[dict[str, str]],
) -> dict[str, Any]:
    """목업 모드에서 사용자 메시지를 간단히 파싱해 profile을 채운다."""

    full_text = message + " " + " ".join(
        item["content"] for item in history
    )

    age_match = (
        re.search(r"(\d)\s*살", full_text)
        or re.search(r"(\d)\s*세", full_text)
    )
    child_age = int(age_match.group(1)) if age_match else None

    # 사용자가 입력한 문자열에서 실제 등장한 위치를 기준으로 정렬
    found_categories = []

    for code, keywords in CATEGORY_KEYWORDS.items():
        positions = [
            full_text.find(keyword)
            for keyword in keywords
            if keyword in full_text
        ]

        if positions:
            found_categories.append((min(positions), code))

    found_categories.sort(key=lambda item: item[0])

    selected_categories = [
        code for _, code in found_categories
    ]

    ready = (
        child_age is not None
        and len(selected_categories) >= 2
    )

    category_labels = {
        "CHILDCARE": "어린이집",
        "PARK": "공원·놀이터",
        "MEDICAL": "병원·소아과",
        "SAFETY": "안전",
        "AIR": "대기환경",
        "SCHOOL": "초등학교",
        "CULTURE": "문화센터",
    }

    selected_labels = [
        category_labels[code]
        for code in selected_categories
    ]

    if child_age is None:
        reply = "안녕하세요! 아이가 몇 살인지 알려주세요."

    elif len(selected_categories) < 2:
        reply = (
            f"{child_age}살이군요! "
            "어린이집, 공원·놀이터, 병원·소아과, 안전, "
            "대기환경, 초등학교, 문화센터 중에서 "
            "중요한 조건을 순서대로 2개 또는 3개 입력해주세요."
        )

    else:
        reply = (
            f"확인했어요. 중요도 순서는 "
            f"{', '.join(selected_labels)}입니다. "
            "아래의 추천 결과 확인하기 버튼을 눌러주세요."
        )

    return {
        "reply": reply,
        "ready_to_recommend": ready,
        "profile": {
            "child_age": child_age,
            "selected_categories": selected_categories,
        },
    }

# --------------- 목업 코드 (삭제하고 아래 코드로 교체) ---------------
def create_chat_response(message: str, history: list[dict[str, str]]) -> dict[str, Any]:
    if os.getenv("CHAT_MOCK_MODE", "false").lower() == "true":
        return _mock_extract_profile(message, history)

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 없습니다. backend/.env를 확인해주세요.")

    client = genai.Client(api_key=api_key)
    conversation = "\n".join(
        f"{'사용자' if item['role'] == 'user' else '챗봇'}: {item['content']}"
        for item in history[-12:]
    )
    prompt = f"""{SYSTEM_PROMPT}\n\n이전 대화:\n{conversation or '없음'}\n\n현재 사용자 메시지:\n{message}"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=RESPONSE_SCHEMA,
            temperature=0.2,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini 응답이 비어 있습니다.")
    return json.loads(response.text)

# def create_chat_response(message: str, history: list[dict[str, str]]) -> dict[str, Any]:
#     api_key = os.getenv("GEMINI_API_KEY")
#     model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
#     if not api_key:
#         raise RuntimeError("GEMINI_API_KEY가 없습니다. backend/.env를 확인해주세요.")

#     client = genai.Client(api_key=api_key)
#     conversation = "\n".join(
#         f"{'사용자' if item['role'] == 'user' else '챗봇'}: {item['content']}"
#         for item in history[-12:]
#     )
#     prompt = f"""{SYSTEM_PROMPT}\n\n이전 대화:\n{conversation or '없음'}\n\n현재 사용자 메시지:\n{message}"""

#     response = client.models.generate_content(
#         model=model_name,
#         contents=prompt,
#         config=types.GenerateContentConfig(
#             response_mime_type="application/json",
#             response_json_schema=RESPONSE_SCHEMA,
#             temperature=0.2,
#         ),
#     )
#     if not response.text:
#         raise RuntimeError("Gemini 응답이 비어 있습니다.")
#     return json.loads(response.text)
