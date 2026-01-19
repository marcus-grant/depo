# src/depo/model/enums.py
from enum import StrEnum


class ItemKind(StrEnum):
    TEXT = "txt"
    LINK = "url"
    PICTURE = "pic"


class Visibility(StrEnum):
    UNLISTED = "unl"
    PRIVATE = "prv"
    PUBLIC = "pub"


class PayloadKind(StrEnum):
    BYTES = "byte"
    FILE = "file"
