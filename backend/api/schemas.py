from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None
    top_k: int = 5
    similarity_threshold: float = 0.0
    temperature: float = 0.3
    mode: str = "ai"
    source_file: str | None = None


class SystemCompareRequest(BaseModel):
    message: str
    conversation_id: int | None = None
    top_k: int = 5
    similarity_threshold: float = 0.0
    temperature: float = 0.3
    source_file: str | None = None


class ConversationUpdateRequest(BaseModel):
    title: str


class QuizGenerateRequest(BaseModel):
    num_questions: int = 5
    source_file: str | None = None
