"""Safe PSD/PSB template downloads from Google Drive and the optional CDN.

Uses Google Drive's media API when a key is configured. Public file links are
tried as well, including Google's large-file confirmation form. Downloaded
bytes are validated before replacing an installed template.
"""
from __future__ import annotations

import logging
import os
import tempfile
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urljoin, urlparse

import requests
from py7zr import SevenZipFile

_logger = logging.getLogger(__name__)
_MAGIC_PSD = b"8BPS"
_MAGIC_7Z = b"7z\xbc\xaf\x27\x1c"
_GOOGLE_HOSTS = {"drive.google.com", "drive.usercontent.google.com", "docs.google.com"}


class _DownloadForm(HTMLParser):
    """Extract a Google Drive download-confirmation form, if present."""

    def __init__(self) -> None:
        super().__init__()
        self.forms: list[tuple[str, dict[str, str]]] = []
        self._action: str | None = None
        self._fields: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "form":
            action = values.get("action") or ""
            # Only consider forms that are plainly Drive download forms.
            self._action = action if "download" in action or values.get("id") == "download-form" else None
            self._fields = {}
        elif tag == "input" and self._action is not None:
            if values.get("name") and values.get("type", "hidden") == "hidden":
                self._fields[str(values["name"])] = str(values.get("value") or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._action is not None:
            self.forms.append((self._action, self._fields.copy()))
            self._action = None
            self._fields = {}


def _validate_download(path: Path, intended_suffix: str) -> None:
    with path.open("rb") as f:
        prefix = f.read(6)
    if intended_suffix.lower() == ".7z":
        if not prefix.startswith(_MAGIC_7Z):
            raise ValueError("Google Drive returned a page or invalid archive, not a 7z template")
    elif prefix[:4] != _MAGIC_PSD or prefix[4:6] not in {b"\x00\x01", b"\x00\x02"}:
        raise ValueError("Google Drive returned a page or invalid data, not a PSD/PSB template")
    if path.stat().st_size < 32:
        raise ValueError("Downloaded template was incomplete")


def _get_with_confirmation(
    session: requests.Session,
    url: str,
    params: dict[str, str] | None,
    temp: Path,
    suffix: str,
    callback: Callable[[int, int], None] | None,
) -> None:
    """Download streaming data; follow at most two real Drive confirm forms."""
    for attempt in range(3):
        with session.get(url, params=params, stream=True, timeout=(15, 180)) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            chunks = response.iter_content(chunk_size=256 * 1024)
            first = next(chunks, b"")
            if not first:
                raise ValueError("Google Drive returned an empty response")
            # A confirmation/permission/quota HTML page must never be saved as a PSD.
            looks_html = "text/html" in content_type or first.lstrip().lower().startswith((b"<!doctype html", b"<html"))
            if looks_html:
                if attempt == 2:
                    raise ValueError("Google Drive returned an HTML page instead of template data (access, quota, or confirmation)")
                # Confirm forms are small; bound read to avoid unbounded HTML.
                html = (first + response.raw.read(1024 * 1024)).decode("utf-8", errors="replace")
                parser = _DownloadForm()
                parser.feed(html)
                if not parser.forms:
                    raise ValueError("Google Drive did not offer a public download (sharing or quota may block it)")
                action, fields = parser.forms[0]
                next_url = urljoin(response.url, action)
                if urlparse(next_url).hostname not in _GOOGLE_HOSTS:
                    raise ValueError("Google Drive confirmation pointed to an unexpected host")
                url, params = next_url, fields
                continue

            total = int(response.headers.get("content-length", "0") or 0)
            received = 0
            with temp.open("wb") as output:
                output.write(first)
                received += len(first)
                if callback:
                    callback(received, total)
                for chunk in chunks:
                    if chunk:
                        output.write(chunk)
                        received += len(chunk)
                        if callback:
                            callback(received, total)
            # For non-content-encoded transfers, mismatch indicates a truncated file.
            if total and not response.headers.get("content-encoding") and received != total:
                raise ValueError(f"Truncated download: {received} of {total} bytes")
            _validate_download(temp, suffix)
            return
    raise ValueError("Exceeded Google Drive confirmation steps")


def _install_archive(temp_archive: Path, expected_psd: Path) -> None:
    """Extract only a matching PSD/PSB to a staging folder, then atomically install."""
    with TemporaryDirectory(prefix="proxystudio-template-", dir=expected_psd.parent) as tmp:
        scratch = Path(tmp)
        with SevenZipFile(temp_archive, "r") as archive:
            names = archive.getnames()
            for name in names:
                member = Path(name.replace("\\", "/"))
                if member.is_absolute() or ".." in member.parts or ":" in name:
                    raise ValueError("7z archive contains unsafe paths")
            matches = [name for name in names if Path(name.replace("\\", "/")).name.casefold() == expected_psd.name.casefold()]
            if len(matches) != 1:
                raise ValueError(f"7z does not contain the expected template {expected_psd.name}")
            archive.extract(path=scratch, targets=matches)
        candidate = scratch / Path(matches[0].replace("\\", "/"))
        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError("7z archive did not contain a regular PSD/PSB file")
        _validate_download(candidate, expected_psd.suffix)
        os.replace(candidate, expected_psd)


def download_template_file(
    *,
    file_id: str | None,
    api_key: str,
    download_path: Path,
    expected_psd: Path,
    fallback_url: object | None = None,
    callback: Callable[[int, int], None] | None = None,
) -> bool:
    """Download and install one template; never overwrite an existing file on failure.

    Download preference: Google Drive API, public Google Drive direct download,
    original Google Drive public URL, optional CloudFront mirror. Errors from
    any source are logged and do not prevent later sources from being tried.
    """
    download_path = Path(download_path)
    expected_psd = Path(expected_psd)
    suffix = download_path.suffix.lower()
    if suffix not in {".psd", ".psb", ".7z"}:
        _logger.error("Unsafe template extension: %s", suffix)
        return False
    if expected_psd.suffix.lower() not in {".psd", ".psb"}:
        _logger.error("Expected template must be a PSD or PSB: %s", expected_psd)
        return False

    expected_psd.parent.mkdir(parents=True, exist_ok=True)
    sources: list[tuple[str, str, dict[str, str] | None]] = []
    if file_id:
        if api_key:
            sources.append(("Google Drive API", f"https://www.googleapis.com/drive/v3/files/{file_id}", {"alt": "media", "key": api_key}))
        sources.append(("Google Drive direct", "https://drive.usercontent.google.com/download", {"id": file_id, "export": "download", "confirm": "t"}))
        sources.append(("Google Drive web", "https://drive.google.com/uc", {"export": "download", "id": file_id}))
    if fallback_url:
        sources.append(("CloudFront mirror", str(fallback_url), None))

    if not sources:
        _logger.error("No download source for template: %s", expected_psd.name)
        return False

    for source_name, url, params in sources:
        fd, temp_name = tempfile.mkstemp(prefix=".proxystudio-template-", suffix=".part", dir=expected_psd.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            _logger.info("Downloading %s from %s", expected_psd.name, source_name)
            with requests.Session() as session:
                _get_with_confirmation(session, url, params, temp, suffix, callback)
            if suffix == ".7z":
                _install_archive(temp, expected_psd)
            else:
                # Atomic replace: previously installed templates survive failed updates.
                os.replace(temp, expected_psd)
            _logger.info("Installed %s using %s", expected_psd.name, source_name)
            return True
        except (requests.RequestException, OSError, ValueError, EOFError) as exc:
            _logger.warning("%s failed for %s: %s", source_name, expected_psd.name, exc)
        except Exception:
            _logger.exception("Unexpected %s failure for %s", source_name, expected_psd.name)
        finally:
            temp.unlink(missing_ok=True)
    _logger.error("All template download sources failed for %s", expected_psd.name)
    return False
