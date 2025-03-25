from common.dependencies import init
from fastapi import FastAPI

from api.api import init_api

init(init_elasticsearch_documents=True)
app: FastAPI = init_api()
