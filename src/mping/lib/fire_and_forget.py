from typing import Callable


def fire_and_forget(func: Callable, *args, **kwargs):
    """ fire and forget decorator thread """
    from threading import Thread

    def wrapper(*args, **kwargs):
        th = Thread(target=func, args=(*args, *kwargs,), daemon=True)
        th.start()
        return th
    return wrapper


def fire_and_forget_asyncio(func: Callable, *args, **kwargs):
    """ fire and forget decorator asyncio """
    from asyncio import get_event_loop

    def wrapper(*args, **kwargs):
        loop = get_event_loop()
        return loop.run_in_executor(None, func, *args, **kwargs)
    return wrapper

