"""Upload service - handles all upload business logic"""

import logging
from dataclasses import dataclass
from typing import Optional

import core.util.types as types
from core.models.item import Item

# from core.models.pic import PicItem
# from core.util.files import save_upload
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


def _invalid_content_result() -> UploadResult:
    return UploadResult(success=False, error_type="invalid_content_type", item=None)


def handle_file_upload(content: Optional[types.Content]) -> UploadResult:
    """
    Process file upload with full validation and storage.
    Returns UploadResult with success/failure details.
    """
    # 1st pass alidation, check size is ok, validators separate to give different err types
    if content_too_big(content):  # Check maxsize 1st avoiding DDOS attempts
        return UploadResult(success=False, error_type="file_too_big", item=None)
    if content_empty(content) or content is None:  # Here to coerce away None
        return UploadResult(success=False, error_type="empty_file", item=None)

    # Classify content - return invalid content result if not valid
    content_class = classify_content(content)
    if content_class.ctype is None:  # Ctype = None means invalid content
        return _invalid_content_result()

    # Normalize content to just bytes or strings
    content = read_content_if_file(content)  # Now content is bytes or str
    if content_class.b64 and isinstance(content, str):
        # Convert base64 string to bytes
        content = decode_base64(content)
    return UploadResult(success=False, error_type="not_implemented", item=None)

    # TODO: Old un-refactored work - DELETEME as functionality gets replaced
    # # Create PicItem and save file
    # pic_item = PicItem.ensure(content)
    # try:
    #     saved = save_upload(pic_item.filename, file_data)
    #     if saved:
    #         logger.info(f"Successfully saved file {pic_item.filename}")
    #     else:
    #         logger.info(f"File {pic_item.filename} already exists, skipping write")
    #     return UploadResult(success=True, error_type="", item=pic_item)
    # except OSError as e:
    #     logger.error(f"Failed to save file {pic_item.filename}: {e}")
    #     return UploadResult(success=False, error_type="storage_error", item=None)
