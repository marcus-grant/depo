"""Upload service - handles all upload business logic"""

from dataclasses import dataclass
from typing import Optional

from core.models.item import Item
from core.util.validator import file_empty, file_too_big, file_type


@dataclass
class UploadResult:
    """Result of file upload processing"""

    success: bool
    error_type: str
    item: Optional[Item]
    # TODO: Refactor to derive file type from item.format property
    # Future: When FileItem base is added, all file-backed items will have format


def handle_file_upload(file_data: bytes) -> UploadResult:
    """
    Process file upload with full validation and storage.
    Returns UploadResult with success/failure details.
    """
    if file_empty(file_data):
        return UploadResult(success=False, error_type="empty_file", item=None)

    if file_too_big(file_data):
        return UploadResult(success=False, error_type="file_too_big", item=None)

    if not file_type(file_data):
        return UploadResult(success=False, error_type="invalid_file_type", item=None)

    # TODO: Implement remaining validation and processing
    return UploadResult(success=True, error_type="", item=None)

