from django.db import models
from typing import Optional, Union, Literal, TypedDict, TYPE_CHECKING

from core.util.shortcode import hash_b32, SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN

if TYPE_CHECKING:
    from core.link.models import LinkItem

CTYPE = Literal["url", "txt", "pic", "xyz"]
Content = Union[str, bytes]


# TODO: Consider making timestamps their own TypedDict
# class TStampContext(TypedDict):
#     iso: str
#     year: int
#     month: int
#     day: int
#     min: int
#     sec: int


class ItemContext(TypedDict):
    code: str
    hash: str
    ctype: CTYPE
    btime: str
    mtime: str


# TODO: Add 'context' method to all item based models
# Will be used to pass into views/templates to standardize data shape to to use
class Item(models.Model):
    CONTENT_TYPES = [
        ("xyz", "Mock type, DNE"),
        ("url", "URL"),
        ("txt", "Text"),
        ("pic", "Picture"),
    ]

    code = models.CharField(primary_key=True, max_length=SHORTCODE_MAX_LEN)
    hash = models.CharField(max_length=SHORTCODE_MAX_LEN)  # Remaining hash minus code
    ctype = models.CharField(max_length=3, choices=CONTENT_TYPES)
    btime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    # TODO: Refactor mtime to ctime because like POSIX, ctime is metadata change
    # mtime in POSIX implies content change, which never happens here.

    # NOTE: Good memoization candidate
    @classmethod
    def search_shortcode(cls, shortcode: str) -> Optional["Item"]:
        """
        Lookup an Item by its shortcode.

        Args:
            shortcode (str): The shortcode to lookup.

        Returns:
            Optional[Item]: The Item if found, else None.
        """
        try:
            return cls.objects.get(code=shortcode)
        except cls.DoesNotExist:
            return None

    # TODO: Move out shortcode len logic to other method
    # TODO: Add either extra method usage of get_or_create of the model instance
    # TODO: Make content the only required parameter, add kwargs to signature with validation
    # NOTE: Add explicit and implicit ctype detection later
    # Implicit will use magic bytes encoded to b32 to determine content type if bytes
    # Will also analyze strs to determine if urls or text
    @classmethod
    def ensure(cls, content: Content, ctype: CTYPE = "url") -> "Item":
        """
        Ensure that a shortcode item hashed to the given content exists.
        If it exists, retrieve its model instance.
        If not, create a new Item instance and return it.

        Args:
            content (Union[str, bytes]): The content to hash and ensure existence.

        Returns:
            Item: The existing or newly created Item.
        """
        # First validate the ctype
        if ctype not in dict(Item.CONTENT_TYPES):
            raise TypeError(f"Invalid ctype in Item.ensure: {ctype}.")

        # Generate all possible code prefixes from SHORTCODE_MIN_LEN to the length of full_hash
        full_hash = hash_b32(content)
        likely_lens = range(SHORTCODE_MIN_LEN, len(full_hash) + 1)
        likely_codes = [full_hash[:length] for length in likely_lens]

        # Fetch all existing items with codes that are prefixes of full_hash
        select = Item.objects.filter
        current_items = select(code__in=likely_codes).only("code", "hash")

        # Create a set for faster lookup
        current_codes = {item.code: item.hash for item in current_items}

        # TODO: Pull functionality into own function/method
        # Iterate through possible codes to find the shortest unique one
        for code in likely_codes:
            hash_rem = full_hash[len(code) :]  # Remaining hash after code
            existing_hash = current_codes.get(code)

            if existing_hash is None:
                # Code is unique; create and return the new item
                fields = {
                    "code": code,
                    "hash": hash_rem,
                    "ctype": ctype,
                }
                new_item = Item(**fields)
                new_item.save()
                return new_item
            elif existing_hash == hash_rem:
                # Exact match found; return the existing item
                return Item.objects.get(code=code)

        # If all possible prefixes are taken, raise an exception
        raise ValueError("Unable to generate a unique shortcode with the given hash.")

    # TODO: Add other content types in Union
    # TODO: Rename since it's composition and not inheritance
    def get_child(self) -> Union["Item", "LinkItem"]:
        for rel in self._meta.get_fields():
            if isinstance(rel, models.OneToOneRel):
                child = getattr(self, rel.get_accessor_name(), None)
                if child:
                    return child
        return self

    def context(self) -> ItemContext:
        return {
            "code": self.code,
            "hash": self.code + self.hash,
            "ctype": self.ctype,
            "btime": self.btime.isoformat(),
            "mtime": self.mtime.isoformat(),
        }
