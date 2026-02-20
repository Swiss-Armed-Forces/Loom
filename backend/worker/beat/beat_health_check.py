import logging
import shelve
import sys
from datetime import timedelta
from tempfile import NamedTemporaryFile

TOLERANCE_IN_MINUTES = 3


def beat_health(cb_schedule: str = "celerybeat-schedule"):

    with NamedTemporaryFile() as temp_file:
        with open(cb_schedule, "rb") as src:
            temp_file.write(src.read())

        temp_filename = temp_file.name

        file_data = shelve.open(temp_filename, flag="r")

        for task_name, task in file_data["entries"].items():
            if task.is_due():
                if task.schedule.remaining_estimate(task.last_run_at) < timedelta(
                    minutes=-TOLERANCE_IN_MINUTES
                ):
                    logging.error("Task: %s is critically overdue", task_name)
                    sys.exit(1)
                logging.warning("Task: %s is overdue", task_name)


if __name__ == "__main__":
    beat_health()
    logging.info("Health check complete.")
