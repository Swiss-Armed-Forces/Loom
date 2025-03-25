from typing import Any

import celery
from celery import Celery, chord
from celery import group as original_group
from celery.canvas import Signature


def patch_group(app: Celery):
    """Patch the behavior of celery of group/chain nesting.

    See: https://github.com/celery/celery/issues/8182
    """

    def patched_group(*signatures: Signature[Any], **options: Any) -> Signature[Any]:
        """A patch for celery.group This is required, because celery does not work as
        expected when using a mixture of nested groups & chains."""
        return chord(original_group(*signatures, **options), __completer.s())

    @app.task(queue="celery.__meta")
    def __completer(results):
        """Task that does nothing, can be used in a chord to complete the chord."""
        return results

    celery.group = patched_group  # type: ignore[misc, assignment]
