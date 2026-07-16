from fastapi import APIRouter, HTTPException
from app.data_loader import load_json
from app.schemas import RecommendationRequest
from app.services.recommendation import calculate_district_scores
from app.services.scoring_config import get_default_priorities


router = APIRouter(tags=["Districts"])

def resolve_priorities(request: RecommendationRequest) -> list[dict]:
    if request.priorities:
        return [item.model_dump() for item in request.priorities]
    return get_default_priorities(request.child_age)

@router.get("/districts")
def get_districts():
    return load_json("districts.json")


@router.post("/recommendations")
def get_recommendations(request: RecommendationRequest):
    scores = calculate_district_scores([item.model_dump() for item in request.priorities])
    return {"recommendations": scores[:request.recommendation_count], "all_scores": scores}


@router.post("/districts/scores")
def get_district_scores(request: RecommendationRequest):
    return calculate_district_scores(resolve_priorities(request))


@router.get("/districts/{district_code}")
def get_district(district_code: str):
    district = next((item for item in load_json("districts.json") if item["district_code"] == district_code), None)
    if not district:
        raise HTTPException(status_code=404, detail="자치구를 찾을 수 없습니다.")
    return district
