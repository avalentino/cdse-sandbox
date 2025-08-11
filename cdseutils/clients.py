"""Client classes for CDSE services."""

import re
import pathlib

from tqdm.auto import tqdm

from .cdseauth import CdseSession, TokenType


class CdseODataClient:
    """OData client for CDSE."""

    DEFAULT_CHUNK_SIZE = 8192

    def __init__(self, token: TokenType | None = None):
        self.session = CdseSession(token)

    @staticmethod
    def _get_filename_from_headers(headers) -> str:
        content_disposition = headers.get("Content-Disposition", str)
        if not content_disposition:
            return ""

        mobj = re.match(
            r"attachment;"
            r"\s*"
            r"""filename=(?P<quote>['"])?(?P<filename>.*)(?P=quote)?""",
            content_disposition,
        )
        if not mobj:
            return ""
        return mobj.group("filename")

    # https://documentation.dataspace.copernicus.eu/APIs/OData.html#product-download
    def download(
        self,
        url: str,
        outfile: str | None = None,
        *,
        chunk_size: int | None = DEFAULT_CHUNK_SIZE,
        disable_progress: bool | None = None,
    ):
        """Download the file at the specified URL.

        The file is stored at the path specified in `outfile`.

        If the `outfile` is not specified the name of the output file is
        deduced by the HTTP(S) response.
        If it is not possible an error is raised.

        If the output file already exists a `FileExistsError` exception is
        raised.
        """
        if outfile:
            if pathlib.Path(outfile).exists():
                raise FileExistsError(
                    f"File or directory already exists: '{outfile}'"
                )

        response = self.session.get(url, stream=True)
        response.raise_for_status()

        # Check if the request was successful
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download file. Status code: {response.status_code}"
            )

        if not outfile:
            outfile = self._get_filename_from_headers(response.headers)
            if not outfile:
                raise ValueError(
                    "'outfile' parameter not specified and "
                    "it is not possible to derive it from the request headers"
                )
            if pathlib.Path(outfile).exists():
                raise FileExistsError(
                    f"File or directory already exists: '{outfile}'"
                )

        data_size = int(response.headers.get("Content-Length", 0))
        pbar = tqdm(
            desc=str(outfile),
            total=data_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            disable=disable_progress,
        )
        with open(outfile, "wb") as fd, pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # filter out keep-alive new chunks
                    size = fd.write(chunk)
                    pbar.update(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def __del__(self):
        self.session.close()
