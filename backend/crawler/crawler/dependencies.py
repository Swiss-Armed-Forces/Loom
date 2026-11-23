import logging
from types import NoneType
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.dependencies import DependencyException
from common.llm.agent import build_system_one_agent
from common.llm.return_types import IndexingUrgency
from common.settings import settings
from pydantic_ai import Agent

logger = logging.getLogger(__name__)

# Agents
_llm_index_prioritization_so_agent: Agent[None, IndexingUrgency] | None = None


def init():
    # pylint: disable=global-statement
    common_dependencies.init()
    logger.info("Initialize crawler dependencies")

    # Built here rather than in `common`, which every pod initialises: this is the one
    # question only the crawler asks, and a client built everywhere is an httpx client
    # nobody closes plus a pod that refuses to start on a block it never reads.
    global _llm_index_prioritization_so_agent
    _llm_index_prioritization_so_agent = build_system_one_agent(
        IndexingUrgency,
        settings.llm_system_one.index_prioritization,
        (
            "Given the following path/filename and file size, how important is it to "
            "analyze the content of the corresponding document ?"
        ),
    )


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()

    global _llm_index_prioritization_so_agent
    _llm_index_prioritization_so_agent = MagicMock(
        spec=Agent[NoneType, IndexingUrgency]
    )


def get_llm_index_prioritization_so_agent() -> Agent[None, IndexingUrgency]:
    if _llm_index_prioritization_so_agent is None:
        raise DependencyException("LLM index prioritization agent missing")
    return _llm_index_prioritization_so_agent
