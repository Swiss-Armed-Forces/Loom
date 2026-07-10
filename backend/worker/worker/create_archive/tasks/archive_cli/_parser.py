from ._commands import _dispatch, build_parser
from ._constants import ARCHIVE_ROOT
from ._db import open_shell_db
from ._shell import cmd_shell


def main() -> None:
    db = open_shell_db(ARCHIVE_ROOT)

    parser = build_parser()
    args = parser.parse_args()

    if args.command is None or args.command == "shell":
        cmd_shell(args, db=db)
        return

    if args.command == "help":
        parser.print_help()
        return

    _dispatch(args, db=db)


if __name__ == "__main__":
    main()
