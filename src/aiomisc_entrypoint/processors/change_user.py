import os
import typing as t

from .base import EntrypointProcessor, Entrypoint, Service


class ChangeUser(EntrypointProcessor):

    def __init__(self, username: str = None):
        if username is None:
            username = 'nobody'
        try:
            import pwd
            nobody = pwd.getpwnam(username)
            self.__uid = nobody.pw_uid
            self.__gid = nobody.pw_gid
            self.__current_user_name = pwd.getpwuid(os.getuid()).pw_name
        except ImportError:
            self.__uid = None
            self.__gid = None

    async def post_start(self, entrypoint: Entrypoint, services: t.Iterable[Service]):

        if self.__uid is not None and self.__current_user_name == 'root':
            os.setgid(self.__gid)
            os.setuid(self.__uid)
