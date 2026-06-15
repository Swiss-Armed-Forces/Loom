from common.dependencies import init as init_common_dependencies
from fastapi import FastAPI

from api.api import init_api
from api.dependencies import init

init_common_dependencies()
init()
app: FastAPI = init_api(collect_metrics=True)
