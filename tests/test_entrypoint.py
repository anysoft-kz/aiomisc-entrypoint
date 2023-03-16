import asyncio
import os
import platform
import pwd
import typing
from threading import Timer

import pytest
from aiomisc import entrypoint as EP, Service, get_context
from aiomisc_entrypoint import Entrypoint
from aiomisc_entrypoint.abstractions import AbstractEntrypointProcessor


def test_entrypoint_signals():
    result = list()

    async def test_coro():
        result.append('coro success')

    class TestService(Service):

        async def start(self):
            result.append('service start success')

        async def stop(self, exception=None):
            result.append('service stop success')

    class TestProcessor(AbstractEntrypointProcessor):

        async def pre_start(self, entrypoint: EP, services: typing.Iterable[Service]):
            result.append('pre_start success')

        async def post_start(self, entrypoint: EP, services=typing.Iterable[Service]):
            result.append('post_start success')

        async def pre_stop(self, entrypoint: Entrypoint):
            result.append('pre_stop success')

        async def post_stop(self, entrypoint: Entrypoint):
            result.append('post_stop success')

    ep = Entrypoint(TestService())
    ep.add_processor(TestProcessor())
    ep.run_until_complete(test_coro())
    assert result == [
        'pre_start success',
        'service start success',
        'post_start success',
        'coro success',
        'pre_stop success',
        'service stop success',
        'post_stop success',
    ]


def background_system_signal_listener(queue):
    from os import getpid
    ep = Entrypoint()
    ep.system_signals_listener()
    Timer(0.1, lambda: queue.put(getpid())).start()
    ep.run_forever()
    queue.put('Success')


def test_system_signal_listener():
    from multiprocessing import Queue, Process
    from os import kill
    from signal import SIGINT, SIGTERM

    q = Queue()
    p = Process(target=background_system_signal_listener, args=(q,))
    p.start()
    pid = q.get()
    kill(pid, SIGINT)
    result = q.get()
    p.join()
    assert result == 'Success'

    p = Process(target=background_system_signal_listener, args=(q,))
    p.start()
    pid = q.get()
    kill(pid, SIGTERM)
    result = q.get()
    p.join()
    assert result == 'Success'

    async def coro():
        pass

    ep = Entrypoint()
    ep.system_signals_listener()
    ep.run_until_complete(coro())


def test_clear_environ_entrypoint_handler():
    import os
    os.environ['__TEST__ENTRYPOINT'] = 'test'
    os.environ['__TEST2__ENTRYPOINT'] = 'test2'

    result = os.environ.get('__TEST__ENTRYPOINT')
    assert result == 'test'

    result = os.environ.get('__TEST2__ENTRYPOINT')
    assert result == 'test2'

    async def coro():
        pass

    ep = Entrypoint()
    ep.clear_environ(lambda x: str(x).startswith('__TEST__'))
    ep.run_until_complete(coro())
    result = os.environ.get('__TEST__ENTRYPOINT')
    assert result is None
    result = os.environ.get('__TEST2__ENTRYPOINT')
    assert result == 'test2'

    ep = Entrypoint()
    ep.clear_environ()
    ep.run_until_complete(coro())
    result = os.environ.get('__TEST2__ENTRYPOINT')
    assert result is None


def background_change_user(queue):
    async def coro():
        queue.put({
            'uid': os.getuid(),
            'gid': os.getgid()
        })

    ep = Entrypoint()
    ep.change_user('nobody')
    ep.run_until_complete(coro())


@pytest.mark.skipif(platform.system() == 'Windows' or pwd.getpwuid(os.getuid()).pw_name != 'root',
                    reason='Only root user can run this')
def test_change_user_entrypoint_processor():
    from multiprocessing import Queue, Process

    q = Queue()
    p = Process(target=background_change_user, args=(q,))
    p.start()
    result = q.get()
    p.join()
    nobody = pwd.getpwnam('nobody')
    assert result['uid'] == nobody.pw_uid
    assert result['gid'] == nobody.pw_gid


def test_register_service_in_context_entrypoint_processor():
    class TestService(Service):
        async def start(self):
            pass

    services = {}

    async def test_coro():
        services['svc1'] = await get_context()['service__svc1']
        services['svc2'] = await get_context()['service__svc2']
        services['svc4'] = await get_context()['service__svc4']

    svc1 = TestService(context_name='svc1')
    svc2 = TestService(context_name='svc2')
    svc3 = TestService()
    svc4 = TestService(context_name='svc4')
    ep = Entrypoint(svc1, svc2, svc3, svc4)
    ep.register_services_in_context()
    ep.run_until_complete(test_coro())

    assert svc1 == services['svc1']
    assert svc2 == services['svc2']
    assert svc4 == services['svc4']


def test_service_dependency_entrypoint_handler():
    start_list = []
    stop_list = []

    class TestService(Service):
        start_sleep: float
        stop_sleep: float
        context_name: str

        async def start(self):
            await asyncio.sleep(self.start_sleep)
            start_list.append(self.context_name)

        async def stop(self, *args, **kwargs):
            await asyncio.sleep(self.stop_sleep)
            stop_list.append(self.context_name)

    async def test_coro():
        pass

    svc1 = TestService(context_name='svc1', start_sleep=0.4, stop_sleep=0.1)
    svc2 = TestService(context_name='svc2', start_sleep=0.3, stop_sleep=0.2)
    svc3 = TestService(context_name='svc3', start_sleep=0.2, stop_sleep=0.3)
    svc4 = TestService(context_name='svc4', start_sleep=0.1, stop_sleep=0.4)
    ep = Entrypoint(svc1, svc2, svc3, svc4)
    ep.first_start_last_stop()
    ep.run_until_complete(test_coro())

    assert start_list == ['svc1', 'svc2', 'svc3', 'svc4']
    assert stop_list == ['svc4', 'svc3', 'svc2', 'svc1']
