from functools import wraps


def noop_decorator(*_, **__):
    def wrap(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return wrap
