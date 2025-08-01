# https://forum.dataspace.copernicus.eu/t/how-do-we-use-the-refresh-token-value-in-the-response-to-a-keycloak-token-request/331
# see also
# https://documentation.dataspace.copernicus.eu/APIs/S3.html#example-script-to-download-product-using-python

import weakref
import datetime
import warnings
from typing import Union

import requests

from .auth import (
    get_auth_from_env,
    get_auth_from_netrc,
    AuthData,
    CredentialsNotFoundError,
)


DEFAULT_AUTH_SERVER_URL: str = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)
DEFAULT_S3_KEY_SERVER_URL: str = (
    "https://s3-keys-manager.cloudferro.com/api/user/credentials"
)


class AuthenticationError(RuntimeError):
    """Authentication error."""


class CdseToken:
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        auth_server_url: str = DEFAULT_AUTH_SERVER_URL,
    ):
        if (username, password).count(None) == 1:
            raise ValueError(
                "both 'username' and 'password' input parameters are needed"
            )

        if username is not None and password is not None:
            auth = AuthData(username=username, password=password)
        else:
            try:
                auth = get_auth_from_env(app_prefix="CDSE_")
            except CredentialsNotFoundError:
                auth = get_auth_from_netrc(url=auth_server_url)

        self._auth_server_url: str = auth_server_url
        self._auth_data = auth
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._access_expiration_time = datetime.datetime.now(tz=datetime.UTC)
        self._refresh_expiration_time = self._access_expiration_time

        self._get_access_token(
            self._auth_data.username, self._auth_data.password
        )

    def _core_get_access_token(self, auth_data: dict[str, str]):
        now = datetime.datetime.now(tz=datetime.UTC)
        try:
            response = requests.post(
                self._auth_server_url,
                data=auth_data,
                verify=True,
                allow_redirects=False,
            )
            response.raise_for_status()
        except requests.HTTPError:
            raise AuthenticationError(
                f"unable to get the access token from {self._auth_server_url}"
            )

        data = response.json()

        expires_in = int(data["expires_in"])
        refresh_expires_in = int(data["refresh_expires_in"])

        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        margin = 1  # second
        self._access_expiration_time = now + datetime.timedelta(
            seconds=expires_in - margin
        )
        self._refresh_expiration_time = now + datetime.timedelta(
            seconds=refresh_expires_in - margin
        )

    def _get_access_token(self, username: str, password: str):
        """Retrieve an access token from the authentication server.

        This token is used for subsequent API calls.
        """
        auth_data = {
            "client_id": "cdse-public",
            "grant_type": "password",
            "username": username,
            "password": password,
        }
        self._core_get_access_token(auth_data=auth_data)

    def _refresh_access_token(self):
        """Refresh an access token from the authentication server."""
        auth_data = {
            "client_id": "cdse-public",
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }
        self._core_get_access_token(auth_data=auth_data)

    def get(self):
        now = datetime.datetime.now(tz=datetime.UTC)
        if now < self._access_expiration_time:
            return self._access_token
        if now < self._refresh_expiration_time:
            self._refresh_access_token()
            return self._access_token
        self._get_access_token()
        return self._access_token

    def __str__(self) -> str:
        return self.get()


TokenType = Union[str, CdseToken]


class CdseS3Credentials:
    def __init__(
        self,
        token: CdseToken,
        key_server_url: str = DEFAULT_S3_KEY_SERVER_URL,
    ):
        self._key_server_url = key_server_url
        self._token = token
        credentials, expiration_date = self._get_s3_auth(key_server_url, token)
        self._credentials = credentials
        self._expiration_date = expiration_date

        # NOTE: weackref.finalize is used instead of `__del__` because the
        # `__del__` is not guaranteed to be called if the object still exists
        # when the interpreter exits.
        # See https://docs.python.org/3/reference/datamodel.html#object.__del__
        self._finalizer = weakref.finalize(
            self,
            CdseS3Credentials._delete_s3_credentials,
            self._key_server_url,
            self._credentials,
            self._token,
        )

    @property
    def access_id(self) -> str:
        return self._credentials.username

    @property
    def secret(self) -> str:
        return self._credentials.password

    @property
    def expiration_date(self) -> datetime.datetime:
        return self._expiration_date

    @staticmethod
    def _get_headers(token: TokenType) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    @staticmethod
    def _get_s3_auth(
        key_server_url: str, token: TokenType
    ) -> tuple[AuthData, datetime.datetime]:
        """Create S3 credentials via S3 keys manager API."""
        headers = CdseS3Credentials._get_headers(token)
        response = requests.post(key_server_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print(data)

        expiration_date = datetime.datetime.fromisoformat(
            data["expiration_date"]
        )

        return AuthData(data["access_id"], data["secret"]), expiration_date

    @staticmethod
    def _delete_s3_credentials(
        key_server_url: str, auth: AuthData, token: TokenType
    ) -> None:
        """Delete the S3 credentials via S3 keys manager API."""
        url = f"{key_server_url}/access_id/{auth.username}"
        headers = CdseS3Credentials._get_headers(token)

        response = requests.delete(url, headers=headers)
        if response.status_code != 204:
            warnings.warn(
                f"Failed to delete S3 credentials {auth.username}. "
                f"Status code: {response.status_code}",
                stacklevel=3,
            )

    def _delete(self):
        if self._finalizer.alive:
            self._finalizer()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._delete()

    def is_valid(self) -> bool:
        now = datetime.datetime.now(tz=datetime.UTC)
        return self._finalizer.alive and (now < self._expiration_date)

    def get(self) -> AuthData:
        if not self.is_valid():
            raise RuntimeError(f"invalid {self.__class__.__name__} object")
        return self._credentials
