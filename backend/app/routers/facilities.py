from fastapi import APIRouter, Query

from app.data_loader import load_json

router = APIRouter(prefix="/facilities", tags=["Facilities"])

FILE_BY_TYPE = {
    "CHILDCARE": "childcare.json",
    "PARK": "playgrounds.json",
    "HOSPITAL": "hospitals.json",
    "SCHOOL": "schools.json",
    "CULTURE": "culture_centers.json",
}

@router.get("")
def get_facilities(
    facility_type: str = Query(alias="type"),
    district: str | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    filename = FILE_BY_TYPE.get(facility_type)

    print("요청 타입:", facility_type)
    print("읽을 파일:", filename)

    if not filename:
        return {"items": [], "total": 0, "page": page, "size": size}

    loaded_data = load_json(filename)

    print("읽은 데이터 타입:", type(loaded_data))
    print("읽은 데이터 개수:", len(loaded_data) if hasattr(loaded_data, "__len__") else "길이 없음")

    items = list(loaded_data)

    print("변환 후 개수:", len(items))

    if items:
        print("첫 번째 데이터:", items[0])

    if district and district != "전체":
        items = [
            item
            for item in items
            if item.get("district") == district
        ]

    if keyword and keyword.strip():
        word = keyword.strip().lower()

        items = [
            item
            for item in items
            if (
                word in str(item.get("name", "")).lower()
                or word in str(item.get("address", "")).lower()
                or word in str(item.get("category", "")).lower()
            )
        ]

    total = len(items)
    start = (page - 1) * size

    return {
        "items": items[start:start + size],
        "total": total,
        "page": page,
        "size": size,
    }