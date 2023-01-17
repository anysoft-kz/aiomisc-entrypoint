import asyncio
import typing as t
from .base import EntrypointProcessor, Entrypoint, Service


class RegisterServiceInContext(EntrypointProcessor):

    def __init__(self):
        self.__tasks = []

    async def pre_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]):
        for service in services:
            if hasattr(service, 'context_name'):
                service.start = self._start_decorator(service)

    async def post_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]):
        if self.__tasks:
            await asyncio.gather(*self.__tasks)
            for svc in entrypoint.services:
                if 'start' in svc.__dict__:
                    del svc.start

    def _start_decorator(self, service: Service):

        async def set_service_id():
            await service.start_event.wait()
            if hasattr(service, 'context_name'):
                service.context[f'service__{service.context_name}'] = service

        start_coro = service.start

        async def wrapper() -> None:
            if hasattr(service, 'context_name'):
                self.__tasks.append(service.loop.create_task(set_service_id()))
            await start_coro()

        return wrapper


