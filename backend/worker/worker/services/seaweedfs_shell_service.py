"""Service for executing SeaweedFS shell commands."""

import logging
import shlex
import subprocess
from dataclasses import dataclass
from typing import Literal

from pydantic import AnyHttpUrl

logger = logging.getLogger(__name__)


class SeaweedFSShellError(Exception):
    """Exception raised when a weed shell command fails."""

    command: str
    return_code: int
    stdout: str
    stderr: str

    def __init__(self, message: str):
        super().__init__(message)
        self.command = ""
        self.return_code = 0
        self.stdout = ""
        self.stderr = ""


class SeaweedFSShellTimeoutError(SeaweedFSShellError):
    """Exception raised when a weed shell command times out."""


@dataclass
class ShellCommandResult:
    """Result of a weed shell command execution."""

    command: str
    return_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.return_code == 0


WeedShellCommand = Literal[
    "volume.fix.replication",
    "volume.balance",
    "volume.vacuum",
]

DEFAULT_MASTER_PORT = 9333


class SeaweedFSShellService:
    """Service for executing SeaweedFS weed shell commands."""

    def __init__(self, master_host: AnyHttpUrl, timeout: int):
        # weed shell expects host:port, not a full URL
        port = master_host.port or DEFAULT_MASTER_PORT
        self.master_address = f"{master_host.host}:{port}"
        self.timeout = timeout

    def execute_command(
        self,
        command: WeedShellCommand,
        args: list[str] | None = None,
        with_lock: bool = False,
    ) -> ShellCommandResult:
        """Execute a weed shell command.

        Args:
            command: The weed shell command to execute.
            args: Optional arguments for the command.
            with_lock: If True, wrap command with lock/unlock in same session.
        """
        # Build the command with properly escaped arguments
        if args:
            escaped_args = " ".join(shlex.quote(arg) for arg in args)
            full_command = f"{command} {escaped_args}"
        else:
            full_command = command

        # Wrap with lock/unlock if requested
        if with_lock:
            shell_input = f"lock\n{full_command}\nunlock"
        else:
            shell_input = full_command

        cmd = ["weed", "shell", f"-master={self.master_address}"]

        logger.info("Executing SeaweedFS command: %s", full_command)

        try:
            proc = subprocess.run(
                cmd,
                input=shell_input,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            result = ShellCommandResult(
                command=full_command,
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )

            if not result.success:
                err = SeaweedFSShellError(
                    f"Command '{full_command}' failed: {proc.stderr}"
                )
                err.command = full_command
                err.return_code = proc.returncode
                err.stdout = proc.stdout
                err.stderr = proc.stderr
                raise err

            logger.info("SeaweedFS command completed: %s", full_command)
            return result

        except subprocess.TimeoutExpired as e:
            stdout_val = ""
            if hasattr(e, "stdout") and e.stdout:
                stdout_val = (
                    e.stdout if isinstance(e.stdout, str) else e.stdout.decode()
                )
            err = SeaweedFSShellTimeoutError(
                f"Command '{full_command}' timed out after {self.timeout}s"
            )
            err.command = full_command
            err.return_code = -1
            err.stdout = stdout_val
            err.stderr = f"Command timed out after {self.timeout} seconds"
            raise err from e
