from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SummaryOut(BaseModel):
    claim: str
    bullet_summary: str  # raw JSON string
    detailed_explanation: str
    eli5_explanation: str
    limitations: str
    model_used: str
    created_at: datetime

    class Config:
        from_attributes = True


class TagOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class NoteOut(BaseModel):
    id: int
    note_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class ItemOut(BaseModel):
    id: int
    title: str
    source_type: str
    source_url: Optional[str]
    extracted_text: str
    created_at: datetime
    summary: Optional[SummaryOut]
    tags: List[TagOut]
    notes: List[NoteOut]

    class Config:
        from_attributes = True


class ItemListOut(BaseModel):
    id: int
    title: str
    source_type: str
    source_url: Optional[str]
    created_at: datetime
    summary: Optional[SummaryOut]
    tags: List[TagOut]

    class Config:
        from_attributes = True
