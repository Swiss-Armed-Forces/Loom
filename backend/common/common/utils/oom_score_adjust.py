import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def adjust_oom_score(score: int):
    """Set OOM score for current process (0-1000, higher = more likely to be killed)"""
    pid = os.getpid()
    oom_score_path = Path(f"/proc/{pid}/oom_score_adj")
    oom_score_path.write_text(str(score), encoding="utf-8")
    logger.debug("OOM score for process %s set to %s", pid, score)
