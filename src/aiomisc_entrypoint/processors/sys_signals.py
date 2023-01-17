import asyncio
import logging
import typing as t
from asyncio import CancelledError
from contextlib import suppress
from signal import SIGINT, SIGTERM

from .base import EntrypointProcessor, Entrypoint, Service

logger = logging.getLogger('aiomisc_entrypoint')


class SysSignalListener(EntrypointProcessor):

    _signal_listener: asyncio.Task

    def __init__(self, *stop_signals: t.Sequence[int]):
        if len(stop_signals) == 0:
            stop_signals = (SIGTERM, SIGINT)
        self._processed_signals = stop_signals

    async def pre_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]):

        stop_entrypoint_signal = asyncio.Event()

        async def listener():
            with suppress(CancelledError):
                await stop_entrypoint_signal.wait()
                entrypoint.loop.call_soon(entrypoint.loop.stop)

        self._signal_listener = entrypoint.loop.create_task(listener())
        for signal in self._processed_signals:
            def stop_entrypoint(*args, **kwargs):
                logger.info("Received signal %s", signal)
                stop_entrypoint_signal.set()

            entrypoint.loop.add_signal_handler(signal, stop_entrypoint)

    async def post_stop(self, entrypoint: Entrypoint):
        if not self._signal_listener.done():
            self._signal_listener.cancel()
            await self._signal_listener
