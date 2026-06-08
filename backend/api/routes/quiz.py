from fastapi import APIRouter

from api.schemas import QuizGenerateRequest
from services.quiz_service import quiz_service


router = APIRouter()


@router.post("/quiz/generate")
async def generate_quiz(request: QuizGenerateRequest):
    return await quiz_service.generate_quiz(request)
