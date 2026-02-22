"""
Azure Storage tools — uses DefaultAzureCredential for all authentication.
"""

import logging
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

_credential = DefaultAzureCredential()


def _get_blob_service_client(account_name: str) -> BlobServiceClient:
    account_url = f"https://{account_name}.blob.core.windows.net"
    return BlobServiceClient(account_url, credential=_credential)


def list_containers(account_name: str) -> str:
    """Return a formatted list of all containers in the storage account."""
    client = _get_blob_service_client(account_name)
    containers = list(client.list_containers())

    if not containers:
        return f"No containers found in storage account '{account_name}'."

    lines = [f"Containers in '{account_name}' ({len(containers)} total):\n"]
    for c in containers:
        lines.append(f"  - {c['name']}")
    return "\n".join(lines)


def list_blobs(account_name: str,
               container_name: Optional[str] = None,
               prefix: Optional[str] = None,
               max_results: int = 50) -> str:
    """
    Return a formatted list of blobs in a container.
    If container_name is omitted, lists blobs across ALL containers.
    """
    client = _get_blob_service_client(account_name)

    if container_name:
        return _list_blobs_in_container(client, container_name, prefix, max_results)

    containers = list(client.list_containers())
    if not containers:
        return "No containers found."

    return "\n\n".join(
        _list_blobs_in_container(client, c["name"], prefix, max_results)
        for c in containers
    )


def _list_blobs_in_container(client: BlobServiceClient,
                              container_name: str,
                              prefix: Optional[str],
                              max_results: int) -> str:
    container_client = client.get_container_client(container_name)
    blobs = []
    for blob in container_client.list_blobs(name_starts_with=prefix):
        blobs.append(blob)
        if len(blobs) >= max_results:
            break

    if not blobs:
        return f"Container '{container_name}': (empty)"

    total_size = sum(b.size for b in blobs)
    lines = [f"Container '{container_name}' — {len(blobs)} blob(s), {_fmt_size(total_size)} total:\n"]
    for b in blobs:
        lines.append(f"  {b.name}  ({_fmt_size(b.size)},  modified {b.last_modified:%Y-%m-%d %H:%M})")

    if len(blobs) >= max_results:
        lines.append(f"\n  ... showing first {max_results} blobs (there may be more)")
    return "\n".join(lines)


def _fmt_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
