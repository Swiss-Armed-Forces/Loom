import logging

from celery import chain
from common.ai_context.ai_context_repository import AiContext
from common.dependencies import get_celery_app

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.ai.tasks import persist_processing_done, rag

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=AiContextProcessingTask, queue="celery.interactive")
def process_question_task(context: AiContext, question: str):
    logger.info("Processing question: '%s' for context: '%s", question, context.id_)
    chain(
        rag.signature(context, question),
        persist_processing_done.signature(context),
    ).delay().forget()
