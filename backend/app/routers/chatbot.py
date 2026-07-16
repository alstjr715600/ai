from fastapi import APIRouter, HTTPException

from app.schemas import (
    ChatRequest,
    ChatResponse,
    NearbyChatRequest,
    NearbyChatResponse,
)
from app.services.gemini_chat import create_chat_response
from app.services.nearby_facilities import find_nearby_facilities

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatResponse)
def send_message(request: ChatRequest):
    try:
        result = create_chat_response(
            request.message,
            [item.model_dump() for item in request.history],
        )
        return ChatResponse(
            reply=result["reply"],
            extracted_profile=result["profile"],
            ready_to_recommend=result["ready_to_recommend"],
        )
    except Exception as error:
        print("Gemini API 오류:", repr(error))
        raise HTTPException(status_code=503, detail="챗봇 응답을 생성하지 못했습니다.") from error

@router.post(
    "/nearby",
    response_model=NearbyChatResponse,
)
def search_nearby_facilities(
    request: NearbyChatRequest,
):
    try:
        result = find_nearby_facilities(
            message=request.message,
            limit=request.limit,
        )

        return NearbyChatResponse(**result)

    except ValueError as error:
        return NearbyChatResponse(
            reply=str(error),
            location=None,
            facility_type=None,
            items=[],
        )

    except Exception as error:
        print("주변 시설 검색 오류:", repr(error))

        raise HTTPException(
            status_code=503,
            detail="주변 시설을 검색하지 못했습니다.",
        ) from error