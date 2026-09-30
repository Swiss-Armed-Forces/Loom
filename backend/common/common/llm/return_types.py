from pydantic import BaseModel


class ImageDescriptionResult(BaseModel):
    description: str


class ElasticsearchQuery(BaseModel):
    query_string: str


class TranslationResult(BaseModel):
    text: str


class DetectedLanguage(BaseModel, frozen=True):
    confidence: float
    language: str


class SummarizationResult(BaseModel):
    text: str
