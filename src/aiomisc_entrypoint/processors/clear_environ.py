import typing as t
import os

from .base import EntrypointProcessor, Entrypoint, Service


class ClearEnviron(EntrypointProcessor):

    def __init__(self, filter_func: t.Callable[[str], bool] = None):
        self.__items = filter(filter_func or (lambda x: True), tuple(os.environ))

    async def pre_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]):
        for name in self.__items:
            os.environ.pop(name, None)
