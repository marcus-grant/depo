# tests/service/test_ingest.py
"""
Tests for service/ingest.py IngestService.

Author: Marcus Grant
Date: 2026-01-23
License: Apache-2.0
"""

import time
from pathlib import Path

import pytest
from tests.factories import gen_image

from depo.model.enums import ContentFormat, ItemKind, PayloadKind
from depo.service.ingest import IngestService
from depo.util.shortcode import hash_full_b32


class TestIngestServiceInit:
    """Tests IngestService constructor"""

    @pytest.mark.parametrize(
        "min_len,max_size,max_url",
        [(2, 2**10, 2048), (4, 2**20, 1024), (8, 2**30, 4096)],
    )
    def test_accepts_valid_configs(self, min_len, max_size, max_url):
        """Accepts min_code_length & max_size_bytes as config"""
        result = IngestService(
            min_code_length=min_len, max_size_bytes=max_size, max_url_len=max_url
        )
        assert isinstance(result, IngestService)
        assert result.min_code_length == min_len
        assert result.max_size_bytes == max_size
        assert result.max_url_len == max_url


class TestIngestServiceValidation:
    """Tests IngestService.build_plan input validation."""

    def test_if_no_payload(self):
        """Raises ValueError if both payload_{bytes,path} are empty"""
        with pytest.raises(ValueError, match=r"(?i)one of.*payload"):
            ingest = IngestService()
            ingest.build_plan()

    def test_if_both_payload_given(self):
        """Raises ValueError if both payload_{bytes,path} are given"""
        with pytest.raises(ValueError, match=r"(?i)one of.*payload"):
            ingest = IngestService()
            ingest.build_plan(payload_bytes=b"\xff", payload_path=Path("/tmp"))

    def test_if_payload_file_max_size_exceeded(self, tmp_path):
        """Raises ValueError if max_size_bytes is exceeded by payload_path"""
        big_file = tmp_path / "big.txt"
        big_file.write_bytes(b"x" * 1001)
        ingest = IngestService(max_size_bytes=1000)
        with pytest.raises(ValueError, match=r"1001 bytes.*exceeds.*1000"):
            ingest.build_plan(payload_path=big_file)

    def test_if_payload_bytes_max_size_exceeded(self):
        """Raises ValueError if max_size_bytes is exceeded by payload_bytes"""
        ingest = IngestService(max_size_bytes=1000)
        with pytest.raises(ValueError, match=r"1001 bytes.*exceeds.*1000"):
            ingest.build_plan(payload_bytes=(b"\xff" * 1001))

    def test_if_payload_empty(self, tmp_path):
        """Raises ValueError if max_size_bytes is exceeded by payload_bytes"""
        ingest = IngestService(max_size_bytes=1000)
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        with pytest.raises(ValueError, match=r"(?i)(empty|zero)"):
            ingest.build_plan(payload_path=empty_file)
        with pytest.raises(ValueError, match=r"(?i)(empty|zero)"):
            ingest.build_plan(payload_bytes=b"")


class TestIngestServiceHashing:
    """Tests IngestService.build_plan hashing integration."""

    @pytest.mark.parametrize("data", [b"\xff" * 999, b"\xde\xad\xbe\xef\x01\x23"])
    def test_writeplan_has_hash_from_hash_full_b32(self, tmp_path, data):
        """Returns WritePlan with hash_full same as hash_full_b32"""
        # With bytes
        kwargs = {"payload_bytes": data, "requested_format": ContentFormat.PLAINTEXT}
        assert IngestService().build_plan(**kwargs).hash_full == hash_full_b32(data)
        # With file
        f = tmp_path / "file.txt"
        f.write_bytes(data)
        kwargs = {"payload_path": f, "requested_format": ContentFormat.PLAINTEXT}
        assert IngestService().build_plan(**kwargs).hash_full == hash_full_b32(data)


class TestIngestServiceClassify:
    """Tests IngestService.build_plan classification integration."""

    def test_writeplan_has_kind_and_format_from_classify(self):
        """Returns WritePlan with kind and format from classify."""
        # requested_format bypasses content inspection
        plan = IngestService().build_plan(
            payload_bytes=b"anything",
            requested_format=ContentFormat.MARKDOWN,
        )
        assert plan.format == ContentFormat.MARKDOWN
        assert plan.kind == ItemKind.TEXT

    def test_classify_uses_filename_hint(self):
        """Passes filename to classify for extension-based detection."""
        plan = IngestService().build_plan(
            payload_bytes=b"no magic bytes here",
            filename="notes.json",
        )
        assert plan.format == ContentFormat.JSON

    def test_classify_uses_declared_mime_hint(self):
        """Passes declared_mime to classify."""
        plan = IngestService().build_plan(
            payload_bytes=b"no magic bytes here",
            declared_mime="application/yaml",
        )
        assert plan.format == ContentFormat.YAML

    def test_raises_if_classify_fails(self):
        """Raises ValueError if content cannot be classified."""
        with pytest.raises(ValueError, match=r"(?i)(classify|unsupport)"):
            IngestService().build_plan(
                payload_bytes=b"\xff\xfe\xfd",
                filename="no_extension",
            )


class TestIngestServiceImage:
    """Tests IngestService.build_plan image medatata integration"""

    def test_writeplan_with_image_info_for_pic_kind(self):
        plan = IngestService().build_plan(payload_bytes=gen_image("PNG", 320, 240))
        assert plan.kind == ItemKind.PICTURE
        assert plan.format == ContentFormat.PNG
        assert plan.width == 320
        assert plan.height == 240

    def test_writeplan_without_image_info_for_text_kind(self):
        """Returns WritePlan without width, or height for non ItemKind.PICTURE"""
        kwargs = {"payload_bytes": b"\x00", "requested_format": ContentFormat.PLAINTEXT}
        assert IngestService().build_plan(**kwargs).width is None
        assert IngestService().build_plan(**kwargs).height is None

    def test_raises_if_image_data_corrupt(self):
        """Raises ValueError if image metadata extraction fails"""
        # Prefer the JPEG EXIF magic bytes since EXIF expected
        with pytest.raises(ValueError, match=r"(?i)(invalid|corrupt)"):
            IngestService().build_plan(payload_bytes=b"\xff\xd8\xff\xe1")


class TestIngestServiceLink:
    """Tests for build_plan() with URL content classified as LINK."""

    def test_writeplan_fields_for_url_payload(self):
        """URL payload_bytes classes as LINK with BYTES payload_kind & right hash"""
        plan = IngestService().build_plan(payload_bytes=b"http://a.eu")
        assert plan.kind == ItemKind.LINK
        assert plan.payload_kind == PayloadKind.BYTES
        assert plan.hash_full == hash_full_b32(bytes("http://a.eu", encoding="utf-8"))

    def test_raises_if_url_exceeds_max_url_len(self):
        """Raises ValueError if classified URL payload exceeds max_url_len."""
        with pytest.raises(ValueError, match=r"(?i)url.*(siz|len).*exceed"):
            IngestService(max_url_len=4).build_plan(payload_bytes=b"http://a.eu")


class TestIngestServiceAssembly:
    """Tests IngestService.build_plan WritePlan assembly."""

    def test_writeplan_has_payload_kind_bytes(self):
        """Returns WritePlan with payload_kind=BYTES for payload_bytes input."""
        plan = IngestService().build_plan(
            payload_bytes=b"hello",
            requested_format=ContentFormat.PLAINTEXT,
        )
        assert plan.payload_kind == PayloadKind.BYTES

    def test_writeplan_has_payload_kind_file(self, tmp_path):
        """Returns WritePlan with payload_kind=FILE for payload_path input."""
        f = tmp_path / "test.txt"
        f.write_bytes(b"hello")
        plan = IngestService().build_plan(
            payload_path=f,
            requested_format=ContentFormat.PLAINTEXT,
        )
        assert plan.payload_kind == PayloadKind.FILE

    def test_writeplan_has_size_b(self):
        """Returns WritePlan with size_b from len(data)."""
        plan = IngestService().build_plan(
            payload_bytes=b"Hello, World!",
            requested_format=ContentFormat.PLAINTEXT,
        )
        assert plan.size_b == len(b"Hello, World!")

    def test_writeplan_has_upload_at(self):
        """Returns WritePlan with upload_at as current timestamp."""
        before = int(time.time())
        plan = IngestService().build_plan(
            payload_bytes=b"hello",
            requested_format=ContentFormat.PLAINTEXT,
        )
        after = int(time.time())
        assert before <= plan.upload_at <= after

    def test_writeplan_has_code_min_len_from_config(self):
        """Returns WritePlan with code_min_len from IngestService config."""
        plan = IngestService(min_code_length=12).build_plan(
            payload_bytes=b"hello",
            requested_format=ContentFormat.PLAINTEXT,
        )
        assert plan.code_min_len == 12

    # TODO: These two payload tests need changing when PayloadKind.FILE is supported
    def test_writeplan_has_payload_bytes_from_bytes(self):
        """WritePlan.payload_bytes populated from payload_bytes input."""
        data = b"hello world"
        plan = IngestService().build_plan(
            payload_bytes=data,
            requested_format=ContentFormat.PLAINTEXT,
        )
        assert plan.payload_bytes == data

    def test_writeplan_has_payload_bytes_from_path(self, tmp_path):
        """WritePlan.payload_bytes populated from payload_path input."""
        f = tmp_path / "test.txt"
        data = b"hello world"
        f.write_bytes(data)
        plan = IngestService().build_plan(
            payload_path=f,
            requested_format=ContentFormat.PLAINTEXT,
        )
        assert plan.payload_bytes == data
