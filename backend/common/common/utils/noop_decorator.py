from functools import wraps


def noop_decorator(*_, **__):
    def wrap(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.name = f"{func.__module__}.{func.__qualname__}"  # type: ignore[attr-defined]
        return wrapper

    return wrap
