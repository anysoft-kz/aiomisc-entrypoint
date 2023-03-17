import typing as t
import os
from aiomisc_entrypoint.abstractions import AbstractEntrypointProcessor
from aiomisc import Service, entrypoint as Entrypoint  # noqa


class ClearEnviron(AbstractEntrypointProcessor):

    def __init__(self, filter_func: t.Callable[[str], bool] = None):
        super().__init__()
        self.__items = filter(filter_func or (lambda x: True), tuple(os.environ))

    async def pre_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]):
        for name in self.__items:
            os.environ.pop(name, None)
