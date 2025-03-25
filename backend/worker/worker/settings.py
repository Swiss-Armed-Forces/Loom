from common.settings import Settings as CommonSettings


class Settings(CommonSettings):
    """All settings for the worker service."""

    skip_translate_while_indexing: bool = False
    skip_summarize_while_indexing: bool = False
    min_language_detection_confidence: float = 95.0
    persist_success_tasks: bool = False
    persist_retry_tasks: bool = True


settings = Settings()
