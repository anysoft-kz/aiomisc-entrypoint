import typing as t
import abc

from aiomisc import Service, entrypoint as Entrypoint  # noqa


class AbstractEntrypointProxy(abc.ABC):
    @property
    @abc.abstractmethod
    def services(self) -> tuple[Service]: ...

    @abc.abstractmethod
    def add_processor(self, processor: 'AbstractEntrypointProcessor'): ...

    @abc.abstractmethod
    def run_until_complete(self, coro: t.Awaitable): ...

    @abc.abstractmethod
    def run_forever(self): ...


class AbstractEntrypointProcessor(abc.ABC):

    def __init__(self):
        self._entrypoint_proxy: t.Optional[AbstractEntrypointProxy] = None

    def set_entrypoint_proxy(self, proxy: AbstractEntrypointProxy):
        self._entrypoint_proxy = proxy

    async def pre_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]): ...

    async def post_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]): ...

    async def pre_stop(self, entrypoint: Entrypoint): ...

    async def post_stop(self, entrypoint: Entrypoint): ...