# core/util/types.py
# Type definitions
from django.core.files.uploadedfile import InMemoryUploadedFile
import typing

# All expected forms of uploaded content behind 'content' headers
Content = typing.Union[InMemoryUploadedFile, str, bytes]
# Content types as specified by Item model 'ctype' field
CTypes = typing.Literal["txt", "url", "pic"]
# Valid Extensions for file-based content
ValidExtensions = typing.Literal["png", "jpg", "gif"]
