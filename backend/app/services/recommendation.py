from app.data_loader import load_json

CATEGORY_LABELS = {
    "CHILDCARE": "어린이집", "PARK": "공원·놀이터", "MEDICAL": "병원·소아과",
    "SAFETY": "안전", "AIR": "대기환경", "SCHOOL": "초등학교", "CULTURE": "문화센터",
}

DEFAULT_SCORE = 50.0

def calculate_district_scores(priorities: list[dict]) -> list[dict]:
    source = load_json("district_scores.json")
    selected = [item for item in priorities if item["weight"] > 0]
    if not selected:
        selected = [{"category": "CHILDCARE", "weight": 1}]
    weight_sum = sum(item["weight"] for item in selected)
    results = []

    for district in source:
        name = district["district_name"]
        base_scores = district["base_scores"]

        weighted_total = 0.0
        category_scores = {}

        for item in selected:
            category = item["category"]
            score = base_scores.get(category, DEFAULT_SCORE)
            category_scores[category] = score
            weighted_total += score * item["weight"]

        
        total_score = round(weighted_total / weight_sum, 1)

        ranked = sorted(
            selected,
            key=lambda item: (category_scores.get(item["category"], DEFAULT_SCORE), item["weight"]),
            reverse=True,
        )

        reasons = []
        for item in ranked[:3]:
            category = item["category"]
            label = CATEGORY_LABELS[category]
            score = category_scores[category]
            reasons.append({
                "category": category,
                "title": f"{label} 환경이 상대적으로 좋아요",
                "description": (
                    f"{name}의 {label} 점수는 {score}점입니다 "
                    f"(서울 25개 자치구 내 상대 순위 기준)."
                ),
            })

        results.append({
                "district_code": district["district_code"],
                "district_name": name,
                "total_score": total_score,
                "category_scores": category_scores,
                "reasons": reasons,
            })

    results.sort(key=lambda item: item["total_score"], reverse=True)
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank

    return results
