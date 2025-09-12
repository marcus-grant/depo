# core/util/types.py
# Type definitions
from django.core.files.uploadedfile import InMemoryUploadedFile
import typing

# All expected forms of uploaded content behind 'content' headers
Content = typing.Union[InMemoryUploadedFile, str, bytes]
