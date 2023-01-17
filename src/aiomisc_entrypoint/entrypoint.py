import asyncio
import typing as t

from aiomisc import entrypoint, Service
from aiomisc_log import LogFormat

from .processors import (
    EntrypointProcessor,
    SysSignalListener,
    ClearEnviron,
    ChangeUser,
    RegisterServiceInContext,
    ServiceStartDependency,
)


class Entrypoint:

    def __init__(self, *services: Service,
                 loop: t.Optional[asyncio.AbstractEventLoop] = None,
                 pool_size: t.Optional[int] = None,
                 log_level: t.Union[int, str] = None,
                 log_format: t.Union[str, LogFormat] = None,
                 log_buffering: bool = None,
                 log_buffer_size: int = None,
                 log_flush_interval: float = None,
                 log_config: bool = False,
                 policy: asyncio.AbstractEventLoopPolicy = None,
                 debug: bool = None,
                 ):
        kwargs = dict(
            loop=loop,
            pool_size=pool_size,
            log_config=log_config,
        )
        if policy is not None:
            kwargs['policy'] = policy
        if debug is not None:
            kwargs['debug'] = debug
        if log_level is not None:
            kwargs['log_level'] = log_level
        if log_format is not None:
            kwargs['log_format'] = log_format
        if log_buffering is not None:
            kwargs['log_buffering'] = log_buffering
        if log_buffer_size is not None:
            kwargs['log_buffer_size'] = log_buffer_size
        if log_flush_interval is not None:
            kwargs['log_flush_interval'] = log_flush_interval

        self._entrypoint = entrypoint(*services, **kwargs)

    def add_processor(self, processor: EntrypointProcessor):
        self._entrypoint.pre_start.connect(processor.pre_start)
        self._entrypoint.post_start.connect(processor.post_start)
        self._entrypoint.pre_stop.connect(processor.pre_stop)
        self._entrypoint.post_stop.connect(processor.post_stop)

    def run_until_complete(self, coro: t.Awaitable):
        with self._entrypoint as loop:
            loop.run_until_complete(coro)

    def run_forever(self):
        with self._entrypoint as loop:
            loop.run_forever()

    def system_signals_listener(self, *signals: int):
        processor = SysSignalListener(*signals)
        self.add_processor(processor)

    def clear_environ(self, filter: t.Callable[[str], bool] = None):
        processor = ClearEnviron(filter)
        self.add_processor(processor)

    def change_user(self, username: str = None):
        processor = ChangeUser(username)
        self.add_processor(processor)

    def register_services_in_context(self):
        processor = RegisterServiceInContext()
        self.add_processor(processor)

    def first_start_last_stop(self):
        processor = ServiceStartDependency()
        self.add_processor(processor)
