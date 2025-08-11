"""Authentication helpers."""

import os
import netrc
import pathlib
from typing import NamedTuple, Union
from urllib.parse import urlparse
from urllib.parse import ParseResult as Url

PathType = Union[str, os.PathLike[str]]
UrlType = Union[str, Url]


class CredentialsNotFoundError(RuntimeError):
    """Unable to get credentials."""


class AuthData(NamedTuple):
    """Authorization data."""

    username: str
    password: str

    def __repr__(self) -> str:
        klass = self.__class__.__name__
        return f"{klass}(username='{self.username}', password='*****')"


def get_auth_from_env(
    dafault_username: str | None = None,
    dafault_password: str | None = None,
    app_prefix: str = "",
) -> AuthData:
    """Get authentication information form the OS environment variables.

    THe environment variables "USERNAME" and "PASSWORD" (optionally
    prefixed by the content of `app_prefix`) are checked.

    Example
    -------
    If `app_prefix` is set to "APP_" (note the final underscore) then the
    following environment variables are inspected to get the username and
    password respectively:

    * APP_USERNAME
    * APP_PASSWORD

    """
    if app_prefix:
        username_key = f"{app_prefix}_USERNAME"
        password_key = f"{app_prefix}_PASSWORD"
    else:
        username_key = "USERNAME"
        password_key = "PASSWORD"

    username = os.environ.get(username_key, dafault_username)
    password = os.environ.get(password_key, dafault_password)

    if username is None or password is None:
        raise CredentialsNotFoundError(
            "unable to retrieve username and password from "
            "environment variables"
        )

    return AuthData(username, password)


def get_auth_from_netrc(
    url: UrlType, netrc_path: PathType | None = None
) -> AuthData:
    """Retrieve authentication credentials from the "netrc" file.

    The function returns credentials for the `url` specified in input.

    The location of the authentication database files in "netrc" format
    1. can be specified directly as a parameter of the function
    2. can be specified by setting the "NETRCFILE" environment variable
       with the relevant path
    3. is assumed to be "~/.netrc" (i.e. the ".netrc" file in the user home
       directory) if none of the above two options is used.

    The above three options are evaluated in order.
    """
    if netrc_path is None:
        netrc_path = os.environ.get("NETRCFILE", "~/.netrc")

    netrc_path = pathlib.Path(netrc_path).expanduser()
    if not netrc_path.is_file():
        raise FileExistsError(f"'{netrc_path}' does not exists")

    auth_db = netrc.netrc(netrc_path)
    if isinstance(url, str):
        url = urlparse(url)

    if url.geturl() in auth_db.hosts:
        key = url.geturl()
    elif url.hostname in auth_db.hosts:
        key = url.hostname
    else:
        raise CredentialsNotFoundError(
            f"unable to get authentication credential for {url.geturl()}"
        )
    authdata = auth_db.authenticators(key)
    if authdata is not None:
        user, _, password = authdata
    else:
        raise CredentialsNotFoundError(
            f"unable to get authentication credential for {url.geturl()}"
        )

    return AuthData(user, password)
