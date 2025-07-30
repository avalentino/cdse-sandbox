# https://forum.dataspace.copernicus.eu/t/how-do-we-use-the-refresh-token-value-in-the-response-to-a-keycloak-token-request/331
# see also
# https://documentation.dataspace.copernicus.eu/APIs/S3.html#example-script-to-download-product-using-python

import logging
import datetime

import requests

from .auth import (
    get_auth_from_env,
    get_auth_from_netrc,
    AuthData,
    CredentialsNotFoundError,
)


_log = logging.getLogger(__name__)


DEFAULT_AUTH_SERVER_URL: str = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)
DEFAULT_S3_KEY_SERVER_URL: str = (
    "https://s3-keys-manager.cloudferro.com/api/user/credentials"
)


class AuthenticationError(RuntimeError):
    """Authentication error"""


class CdseTokenAuth:
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

        if password is None:
            try:
                auth = get_auth_from_env(app_prefix="CDSE_")
            except CredentialsNotFoundError:
                auth = get_auth_from_netrc(url=auth_server_url)
        else:
            auth = AuthData(username=username, password=password)

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
        self._access_expiration_time = (
            now + datetime.timedelta(seconds=expires_in - margin)
        )
        self._refresh_expiration_time = (
            now + datetime.timedelta(seconds=refresh_expires_in - margin)
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


def get_s3_credentials(
    token: str, key_server_url: str = DEFAULT_S3_KEY_SERVER_URL
) -> str:
    """Create temporary S3 credentials via S3 keys manager API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    response = requests.post(key_server_url, headers=headers)
    response.raise_for_status()

    data = response.json()

    return AuthData(data["access_id"], data["secret"])
