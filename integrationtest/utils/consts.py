from pathlib import Path

from utils.settings import settings

ASSETS_DIR = (Path(__file__).parent.parent / "assets").absolute()
FILES_ENDPOINT = f"{settings.api_host}v1/files"
QUEUES_ENDPOINT = f"{settings.api_host}v1/queues"
TAGS_ENDPOINT = f"{settings.api_host}v1/files/tags"
ARCHIVE_ENDPOINT = f"{settings.api_host}v1/archive"
TRANSLATION_ENDPOINT = f"{settings.api_host}v1/files/translation"
INDEX_ENDPOINT = f"{settings.api_host}v1/files/index"
CACHING_ENDPOINT = f"{settings.api_host}v1/caching"
WEBSOCKET_ENDPOINT = f"{settings.ws_host}v1/websocket"
SUMMARIZATION_ENDPOINT = f"{settings.api_host}v1/files/summarization"
AI_ENDPOINT = f"{settings.api_host}v1/ai"
REQUEST_TIMEOUT = 10
