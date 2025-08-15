"""Support tools for OAuth API."""

import requests

CDSE_OAUTH_BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"


def get_collections() -> list[str]:
    """Return the list of collections available on CDSE via Odata API."""
    url = f"{CDSE_OAUTH_BASE_URL}/Attributes"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return list(data.keys())
