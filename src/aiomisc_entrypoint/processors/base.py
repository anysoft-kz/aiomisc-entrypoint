import typing as t
from aiomisc import Service
from aiomisc.entrypoint import Entrypoint


class EntrypointProcessor:

    async def pre_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]): ...

    async def post_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]): ...

    async def pre_stop(self, entrypoint: Entrypoint): ...

    async def post_stop(self, entrypoint: Entrypoint): ...
