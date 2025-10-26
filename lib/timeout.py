import concurrent.futures
import functools
from typing import Callable


def with_timeout(timeout: float):
    """
    Decorator to return a default value if the function takes longer than `timeout` seconds.

    Args:
        timeout: Maximum allowed time (in seconds) for the function to complete.
        default: Value to return if timeout occurs.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(
                        f"Function '{func.__name__}' timed out after {timeout} seconds."
                    )

        return wrapper

    return decorator
