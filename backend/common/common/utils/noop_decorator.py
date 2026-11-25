from functools import wraps

from celery.canvas import Signature


def noop_decorator(*_, **__):
    def wrap(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        name = f"{func.__module__}.{func.__qualname__}"
        wrapper.name = name  # type: ignore[attr-defined]
        # A task that dispatches a canvas calls `.s()` on its stages, so the stand-in
        # has to answer with something a chain or chord can be built from. The
        # signature is never sent anywhere, and building one needs no app.
        wrapper.s = lambda *a, **kw: Signature(  # type: ignore[attr-defined]
            task=name, args=a, kwargs=kw
        )
        return wrapper

    return wrap
