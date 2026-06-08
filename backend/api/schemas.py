from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    top_k: int = 5
    similarity_threshold: float = 0.0
    temperature: float = 0.3
    mode: str = "ai"
    source_file: str | None = None


class QuizGenerateRequest(BaseModel):
    num_questions: int = 5
    source_file: str | None = None
