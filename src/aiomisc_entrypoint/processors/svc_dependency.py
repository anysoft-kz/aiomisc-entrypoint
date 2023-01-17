import asyncio
import typing as t
from collections import defaultdict, namedtuple

from .base import EntrypointProcessor, Entrypoint, Service


__all__ = ['ServiceStartDependency']

DependencyItem = namedtuple('DependencyItem', ('start', 'stop'))


class ServiceStartDependency(EntrypointProcessor):

    async def pre_start(self, entrypoint: Entrypoint, services: t.Sequence[Service]):
        if len(services) > 1:
            _inject_decorators(services)

    async def post_stop(self, entrypoint: Entrypoint):
        for svc in entrypoint.services:
            if 'start' in svc.__dict__:
                del svc.start
            if 'stop' in svc.__dict__:
                del svc.stop


def _start_decorator(service: Service, dependency_service):

    start_coro = service.start

    async def wrapper() -> None:
        if dependency_service:
            await dependency_service.start_event.wait()
        await start_coro()

    return wrapper


def _stop_decorator(service: Service,
                    stop_event: asyncio.Event, dependency_event: t.Optional[asyncio.Event]):
    stop_coro = service.stop

    async def wrapper(*args, **kwargs) -> None:
        if dependency_event:
            await dependency_event.wait()
        await stop_coro(*args, **kwargs)
        service.loop.call_soon(stop_event.set)

    return wrapper


def _make_dependency_map(services: t.Sequence[Service]):
    dep: dict[Service, DependencyItem] = dict()
    svc_count = len(services)
    dep[services[0]] = DependencyItem(None, services[1])
    for index, svc in enumerate(services):
        if index == 0:
            dep[svc] = DependencyItem(None, services[index+1])
        elif index < (svc_count-1):
            dep[svc] = DependencyItem(services[index-1], services[index+1])
        else:
            dep[svc] = DependencyItem(services[index-1], None)

    return dep


def _inject_decorators(services: t.Sequence[Service]):
    dependencies_map = _make_dependency_map(services)
    stop_events: dict[Service, asyncio.Event] = defaultdict(asyncio.Event)
    for svc, dp_item in dependencies_map.items():
        svc.start = _start_decorator(svc, dp_item.start)
        svc.stop = _stop_decorator(
            svc, stop_event=stop_events[svc],
            dependency_event=stop_events[dp_item.stop] if dp_item.stop else None)

