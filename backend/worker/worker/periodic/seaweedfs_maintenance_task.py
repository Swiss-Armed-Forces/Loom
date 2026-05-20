import logging

from common.dependencies import get_celery_app, get_celery_inspect_service

from worker.dependencies import get_seaweedfs_shell_service
from worker.periodic.infra.periodic_task import PeriodicTask
from worker.services.seaweedfs_shell_service import WeedShellCommand

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def seaweedfs_maintenance_task(
    command: WeedShellCommand,
    command_args: list[str] | None = None,
    check_idle: bool = True,
):
    """Execute a SeaweedFS maintenance command.

    Args:
        command: The weed shell command to execute.
        command_args: Optional arguments for the command.
        check_idle: If True, only run when queues are idle.
    """
    if check_idle and not get_celery_inspect_service().is_idle(called_from_task=True):
        logger.info("Celery not idle: do nothing")
        return

    logger.info("Running SeaweedFS %s", command)
    service = get_seaweedfs_shell_service()
    result = service.execute_command(command, args=command_args, with_lock=True)
    logger.info(
        "SeaweedFS %s completed: %s",
        command,
        result.stdout[:1000] if result.stdout else "(no output)",
    )
