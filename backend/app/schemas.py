from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class PaperIn(BaseModel):
    title: str
    subject: str
    year: int
    duration_minutes: int = 120
    positive_marks: float = 3
    negative_marks: float = 1
    published: bool = False

class QuestionIn(BaseModel):
    number: int
    body: str
    options: List[str] = Field(default_factory=list)
    answer: Optional[str] = None
    solution: Optional[str] = None
    reviewed: bool = False

class SubmitIn(BaseModel):
    student: str = 'Student'
    answers: Dict[str, str]
    time_taken_seconds: int = 0
