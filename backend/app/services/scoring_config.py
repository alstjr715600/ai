# 나이대별 기본 우선순위 (0~5 스케일, 팀이 정한 순위를 그대로 반영)
AGE_DEFAULT_PRIORITIES: dict[str, dict[str, int]] = {
    "0-3": {  # 의료 > 환경=돌봄 > 여가/자연 > 교육
        "MEDICAL": 5, "AIR": 4, "CHILDCARE": 4,
        "PARK": 3, "CULTURE": 3, "SCHOOL": 2, "SAFETY": 0,
    },
    "3-5": {  # 여가/자연 > 의료 > 환경 > 돌봄=교육
        "PARK": 5, "CULTURE": 5, "MEDICAL": 4,
        "AIR": 3, "CHILDCARE": 2, "SCHOOL": 2, "SAFETY": 0,
    },
    "5-7": {  # 돌봄 > 교육 > 여가/자연 > 의료 > 환경
        "CHILDCARE": 5, "SCHOOL": 4, "PARK": 3,
        "CULTURE": 3, "MEDICAL": 2, "AIR": 1, "SAFETY": 0,
    },
}

def age_to_tier(child_age: int) -> str:
    if child_age <= 3:
        return "0-3"
    if child_age <= 5:
        return "3-5"
    return "5-7"

def get_default_priorities(child_age: int) -> list[dict]:
    tier = age_to_tier(child_age)
    return [
        {"category": cat, "weight": w}
        for cat, w in AGE_DEFAULT_PRIORITIES[tier].items()
    ]