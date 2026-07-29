import argparse
import sys
from pathlib import Path
from sqlite3 import Connection

from ._constants import FILES_INDEX
from ._db import _resolve_and_load


def _list_translations(translations: list[dict[str, object]]) -> None:
    for t in translations:
        lang = t.get("language") or ""
        confidence = t.get("confidence")
        conf_str = (
            f"  (confidence: {confidence:.2f})" if isinstance(confidence, float) else ""
        )
        print(f"{lang}{conf_str}")


def cmd_translate(
    args: argparse.Namespace,
    *,
    db: Connection,
    index_dir: Path = FILES_INDEX,
    cwd: str | None = None,
) -> None:
    resolved = _resolve_and_load(args.name, db=db, index_dir=index_dir, cwd=cwd)
    translations: list[dict[str, object]] = resolved.meta.get("translations") or []

    if not translations:
        print("No translations available for this file.", file=sys.stderr)
        sys.exit(1)

    if args.language is None:
        _list_translations(translations)
        return

    translation = next(
        (t for t in translations if t.get("language") == args.language), None
    )
    if translation is None:
        available = [str(t.get("language") or "") for t in translations]
        print(f"Error: no '{args.language}' translation available", file=sys.stderr)
        print(f"Available: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    print(translation.get("text") or "")
