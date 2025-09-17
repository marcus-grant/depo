"""Upload service - handles all upload business logic"""

import logging
from dataclasses import dataclass
from typing import Optional

import core.util.types as types
from core.models.pic import PicItem
from core.util.files import save_upload
from core.util.validator import content_empty, content_too_big  # , file_type
from core.util.classifier import classify_content
from core.util.content import read_content_if_file

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of file upload processing"""

    success: bool
    error_type: Optional[str] = None
    item: Optional[Item] = None
    # TODO: Refactor to derive file type from item.format property
    # Future: When FileItem base is added, all file-backed items will have format


def handle_file_upload(content: Optional[types.Content]) -> UploadResult:
    """
    Process file upload with full validation and storage.
    Returns UploadResult with success/failure details.
    """
    # First pass of validation - check if size is ok
    if content_too_big(content):  # Check maxsize 1st avoiding DDOS attempts
        return UploadResult(success=False, error_type="file_too_big", item=None)

    if not file_type(file_data):
        return UploadResult(success=False, error_type="invalid_file_type", item=None)

    # Create PicItem and save file
    pic_item = PicItem.ensure(file_data)

    try:
        saved = save_upload(pic_item.filename, file_data)
        if saved:
            logger.info(f"Successfully saved file {pic_item.filename}")
        else:
            logger.info(f"File {pic_item.filename} already exists, skipping write")
        return UploadResult(success=True, error_type="", item=pic_item)
    except OSError as e:
        logger.error(f"Failed to save file {pic_item.filename}: {e}")
        return UploadResult(success=False, error_type="storage_error", item=None)
