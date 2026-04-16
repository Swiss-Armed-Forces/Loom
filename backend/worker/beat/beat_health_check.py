import logging
import os
import shelve
import sys
from datetime import timedelta
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)

TOLERANCE_IN_MINUTES = 3
CB_SCHEDULE = "celerybeat-schedule"


def beat_health(cb_schedule: str = CB_SCHEDULE) -> bool:
    if not os.path.exists(cb_schedule):
        logger.info("Schedule file not yet created, beat is still starting up.")
        return True

    healthy = True

    with NamedTemporaryFile() as temp_file:
        with open(cb_schedule, "rb") as src:
            temp_file.write(src.read())

        with shelve.open(temp_file.name, flag="r") as file_data:
            for task_name, task in file_data["entries"].items():
                if task.is_due():
                    if task.schedule.remaining_estimate(task.last_run_at) < timedelta(
                        minutes=-TOLERANCE_IN_MINUTES
                    ):
                        logger.error("Task: %s is critically overdue", task_name)
                        healthy = False
                    else:
                        logger.warning("Task: %s is overdue", task_name)

    return healthy


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    BEAT_HEALTH_RC = beat_health()
    logger.info("Health check complete.")
    sys.exit(0 if BEAT_HEALTH_RC else 1)
