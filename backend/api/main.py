from fastapi import FastAPI

from api.api import init_api
from api.dependencies import init

init()
app: FastAPI = init_api(collect_metrics=True)
