"""Client classes for CDSE services."""

import re
import enum
import logging
import pathlib
import warnings

from tqdm.auto import tqdm

from .cdseauth import CdseSession, TokenType

_log = logging.getLogger(__name__)


class ESaveMode(enum.StrEnum):
    """Mode for saving a file in case it already exists."""

    OVERWRITE = "OVERWRITE"
    NOT_OVERWRITE = "NO_OVERWRITE"
    RAISE = "RAISE"


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
            raise ValueError(
                "no output file name specified and it is not possible to "
                "derive it from the request headers"
            )

        return mobj.group("filename")

    @staticmethod
    def _new_path(
        outfile: str,
        outdir: str | None = None,
        save_mode: ESaveMode = ESaveMode.RAISE,
    ) -> pathlib.Path:
        assert outfile is not None
        if outdir is not None:
            if pathlib.Path(outfile).is_absolute():
                warnings.warn(
                    "an absolute path has been provided as input "
                    f"('{outfile}'), the 'outdir parameter' ('{outdir}') "
                    "will be ignored",
                    stacklevel=3,
                )
            path = pathlib.Path(outdir) / outfile
        else:
            path = pathlib.Path(outfile)

        if path.exists() and save_mode is ESaveMode.RAISE:
            raise FileExistsError(
                f"File or directory already exists: '{path}'"
            )

        return path

    # https://documentation.dataspace.copernicus.eu/APIs/OData.html#product-download
    def download(
        self,
        url: str,
        outfile: str | None = None,
        *,
        outdir: str | None = None,
        chunk_size: int | None = DEFAULT_CHUNK_SIZE,
        disable_progress: bool | None = None,
        save_mode: ESaveMode = ESaveMode.NOT_OVERWRITE,
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
            self._new_path(outfile, outdir=outdir, save_mode=save_mode)

        response = self.session.get(url, stream=True)
        response.raise_for_status()

        # Check if the request was successful
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download file. Status code: {response.status_code}"
            )

        if not outfile:
            outfile = self._get_filename_from_headers(response.headers)

        outpath = self._new_path(outfile, outdir=outdir, save_mode=save_mode)
        if outpath.exists() and save_mode is ESaveMode.NOT_OVERWRITE:
            _log.info("file '%s' already exists, skip download", outpath)
            return

        outpath.parent.mkdir(exist_ok=True, parents=True)

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
