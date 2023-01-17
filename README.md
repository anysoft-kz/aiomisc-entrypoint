# Aiomisc Entrypoint

Alternative way to run [aiomisc entrypoint](https://aiomisc.readthedocs.io/en/latest/entrypoint.html#entrypoint) with processors
added behavior to start and stop events of entrypoint and custom query logger.


## Basic usage
```python
from aiomisc_entrypoint import Entrypoint

ep = Entrypoint()
ep.clear_environ()
ep.change_user()
ep.system_signals_listener()
ep.register_services_in_context()
ep.first_start_last_stop()

ep.run_forever()
```


## Extended usage

```python
from signal import SIGINT, SIGTERM, SIGKILL
from aiomisc import Service
from aiomisc_entrypoint import Entrypoint

class TestService(Service):
    
    async def start(self):
        ...

    
async def main():
    ...


services = (
    TestService(context_name='svc1'),
    TestService(context_name='svc2'),
)
    
ep = Entrypoint(*services)
ep.clear_environ(lambda x: x.startwith('APP_'))
ep.change_user('user')
ep.system_signals_listener(SIGINT, SIGTERM, SIGKILL)
ep.register_services_in_context()
ep.first_start_last_stop()

ep.run_until_complete(main())
```


Release Notes:

v1.0.1
- fix error with set loop for `asyncio.Event` in `SysSignalListener`

