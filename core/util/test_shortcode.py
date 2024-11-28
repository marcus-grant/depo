from django.test import TestCase
import random
from unittest.mock import patch

from core.util.shortcode import (
    hash_std,
    validate_b32_encode,
    encode_b32_hex,
    encode_b32,
    validate_b32_decode,
    decode_b32_hex,
    decode_b32,
)


def generate_data(size: int = 10 * (1024**2), seed: int = 42) -> bytes:
    """Generates pseudo random (deterministic) data of a given size and seed."""
    rand = random.Random(seed)
    data = bytearray(size)
    for i in range(size):
        data[i] = rand.randint(0, 255)
    return bytes(data)


class TFacts:
    # Legend: _S := UTF8 str, _B := Hex Bytes
    # _B32H := Base32 HexEncoded Str
    # _B32C := Base32 Crockford Encoded Str
    EMPTY_S = ""
    EMPTY_B = b""

    HELLO_S = "Hello, World!"
    HELLO_B = b"\x48\x65\x6c\x6c\x6f\x2c\x20\x57\x6f\x72\x6c\x64\x21"
    HELLO_32R = "JBSWY3DPFQQFO33SNRSCC==="
    HELLO_32C = "91JPRV3F5GG5EVVJDHJ22UUU"
    HELLO_32H = "91IMOR3F5GG5ERRIDHI22==="
    FIVE_ZERO_B = b"\x00\x00\x00\x00\x00"
    DEADBEEF_B = b"\xdb\xee\xf0\x0d"

    # ALL_SYMBOLS_B = b"\x00\x44\x32\x14\xc7\x42\x54\xb6\x35\xcf\x84\x65\x3a\x56\xd7\xc6\x75\xbe\x77\xdf"
    ALL_SYMBOLS_B = bytes.fromhex("00443214c74254b635cf84653a56d7c675be77df")
    ALL_SYMBOLS_32H = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
    ALL_SYMBOLS_32C = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    # Easy to hand-encode counts to check character orders
    COUNT5_S = "12345"
    COUNT5_32 = "64S36D1N"
    COUNT8_B = b"\x00\x44\x32\x14\xc7"
    COUNT8_32H = "01234567"
    COUNT8_REV_B = b"\xff\xbb\xcd\xeb\x38"
    COUNT8_REV_32H = "VUTSRQPO"

    # Padding test facts
    PAD0_B = b"\xff\xff\xff\xff\xff"
    PAD0_32H = "VVVVVVVV"
    PAD0_32C = "ZZZZZZZZ"
    PAD1_B = b"\xff\xff\xff\xff"
    PAD1_32H = "VVVVVVO="
    PAD1_32C = "ZZZZZZRU"
    PAD2_B = b"\xff\xff\xff"
    PAD2_32H = "VVVVU==="
    PAD2_32C = "ZZZZYUUU"
    PAD3_B = b"\xff\xff"
    PAD3_32H = "VVVG===="
    PAD3_32C = "ZZZGUUUU"
    PAD4_B = b"\xff"
    PAD4_32H = "VS======"
    PAD4_32C = "ZWUUUUUU"

    # Big test facts
    HASH_GEN_1MB = "41adedd1592568bab2d3facea53812"
    ARGS_GEN_1MB = {"size": 1024**2, "seed": 42}
    DATA_GEN_1MB = generate_data(**ARGS_GEN_1MB)


class HashTest(TestCase):
    # NOTE: Hashes were determined with cmd: echo -n "STRING" | b2sum -l 120
    # Note the -n flag to not include newline in the hash
    HASH_EMPTY = "b7db87196c483405e40f8401fa1fc9"
    HASH_HELLO = "69e19038c317e1ea5d5bc763ef8c25"
    STR_HELLO = "Hello, World!"
    B_HELLO = STR_HELLO.encode("utf-8")

    HASH_GEN_10MB = "4ec6e262b346533a7a2cb8aefe5827"
    ARGS_GEN_10MB = {"size": 10 * 1024**2, "seed": 42}

    # NOTE: Uncomment this test case to generate test.bin to use in terminal
    # def test_gen_file(self):
    #     """
    #     Use this to generate a file to use to b2sum in terminal for a hash.
    #     Uncomment this test case to run it, then use the file.
    #     """
    #     with open("test.bin", "wb") as f:
    #         f.write(generate_data(**self.ARGS_GEN_1MB))

    def test_empty_str(self):
        self.assertEqual(hash_std("").hex(), self.HASH_EMPTY)

    def test_empty_bytes(self):
        self.assertEqual(hash_std(b"").hex(), self.HASH_EMPTY)

    def test_hello_str(self):
        self.assertEqual(hash_std(self.STR_HELLO).hex(), self.HASH_HELLO)

    def test_hello_b(self):
        self.assertEqual(hash_std(self.B_HELLO).hex(), self.HASH_HELLO)

    def test_bytes_str_hash_match(self):
        self.assertEqual(hash_std("hello").hex(), hash_std(b"hello").hex())

    def test_gen_1mb(self):
        self.assertEqual(hash_std(TFacts.DATA_GEN_1MB).hex(), TFacts.HASH_GEN_1MB)

    # NOTE: This test takes about 4s to run on an Apple M2
    # def test_gen_10mb(self):
    #     real_hash = hash(generate_data(**self.ARGS_GEN_10MB)).hex()
    #     self.assertEqual(real_hash, self.HASH_GEN_10MB)

    # TODO: Add more tests that include pictures


class Base32EncodeValidTest(TestCase):
    def test_bytes(self):
        zeros = TFacts.FIVE_ZERO_B
        beef = TFacts.DEADBEEF_B
        self.assertEqual(validate_b32_encode(zeros), zeros)
        self.assertEqual(validate_b32_encode(beef), beef)
        self.assertNotEqual(validate_b32_encode(zeros), beef)

    def test_strs(self):
        empty_s, empty_b = TFacts.EMPTY_S, TFacts.EMPTY_B
        hello_s, hello_b = TFacts.HELLO_S, TFacts.HELLO_B
        crock_s, crock_b = TFacts.ALL_SYMBOLS_32C, TFacts.ALL_SYMBOLS_B
        self.assertEqual(validate_b32_encode(empty_s), empty_b)
        self.assertEqual(validate_b32_encode(hello_s), hello_b)
        # TODO: Use base32 encoder calculator to fix this test
        # self.assertEqual(validate_b32_encode(crock_s), crock_b)
        self.assertNotEqual(validate_b32_encode(empty_s), hello_b)
        self.assertNotEqual(validate_b32_encode(empty_s), crock_b)
        self.assertNotEqual(validate_b32_encode(hello_s), empty_b)
        self.assertNotEqual(validate_b32_encode(hello_s), crock_b)
        self.assertNotEqual(validate_b32_encode(crock_s), empty_b)
        self.assertNotEqual(validate_b32_encode(crock_s), hello_b)

    def test_raises_type_err(self):
        with self.assertRaises(TypeError):
            validate_b32_encode(42)
        with self.assertRaises(TypeError):
            validate_b32_encode(3.14)
        with self.assertRaises(TypeError):
            validate_b32_encode(None)
        with self.assertRaises(TypeError):
            validate_b32_encode([1, 2, 3])
        with self.assertRaises(TypeError):
            validate_b32_encode({"a": 1, "b": 2})
        validate_b32_encode(b"hello")
        validate_b32_encode("hello")


class Base32HexEncodeTest(TestCase):
    def test_empty(self):
        self.assertEqual(encode_b32_hex(b""), "")
        self.assertNotEqual(encode_b32_hex(""), "12345678")

    def test_str(self):
        self.assertEqual(encode_b32_hex(TFacts.HELLO_S), TFacts.HELLO_32H)
        self.assertNotEqual(encode_b32_hex(TFacts.HELLO_S), TFacts.HELLO_32C)

    def test_bytes(self):
        self.assertEqual(encode_b32_hex(TFacts.HELLO_B), TFacts.HELLO_32H)
        self.assertEqual(encode_b32_hex(TFacts.COUNT8_B), TFacts.COUNT8_32H)
        self.assertEqual(encode_b32_hex(TFacts.COUNT8_REV_B), TFacts.COUNT8_REV_32H)
        self.assertNotEqual(encode_b32_hex(TFacts.HELLO_B), TFacts.HELLO_32C)

    def test_padding(self):
        self.assertEqual(encode_b32_hex(TFacts.PAD0_B), TFacts.PAD0_32H)
        self.assertEqual(encode_b32_hex(TFacts.PAD1_B), TFacts.PAD1_32H)
        self.assertEqual(encode_b32_hex(TFacts.PAD2_B), TFacts.PAD2_32H)
        self.assertEqual(encode_b32_hex(TFacts.PAD3_B), TFacts.PAD3_32H)
        self.assertEqual(encode_b32_hex(TFacts.PAD4_B), TFacts.PAD4_32H)

    def test_validate_called(self):
        with patch("core.util.shortcode.validate_b32_encode") as mock_fn:
            mock_fn.side_effect = (
                lambda x: x if isinstance(x, bytes) else x.encode("utf-8")
            )
            encode_b32_hex(TFacts.HELLO_S)
            mock_fn.assert_called_once_with(TFacts.HELLO_S)
            encode_b32_hex(TFacts.HELLO_B)
            mock_fn.assert_called_with(TFacts.HELLO_B)


class EncodeB32Test(TestCase):
    # Cases, lower case chars become upper case in encoding
    # = pads become U
    # Correctness of crockford encoding characters set
    BASE32_CODE_HEX = "0123456789ABCDEFGHIJKLMNOPQRSTUV="
    BASE32_CODE_CROCK = "0123456789ABCDEFGHJKMNPQRSTVWXYZU"

    def test_empty(self):
        self.assertEqual(encode_b32(b""), "")

    def test_empty_str(self):
        self.assertEqual(encode_b32(""), "")

    def test_strs(self):
        assertEq = self.assertEqual
        assertEq(encode_b32("Hello, World!"), "91JPRV3F5GG5EVVJDHJ22UUU")
        assertEq(encode_b32("12345"), "64S36D1N")
        assertEq(encode_b32("123456"), "64S36D1N6RUUUUUU")

    def test_long_strs(self):
        assertEq = self.assertEqual
        f = TFacts
        assertEq(encode_b32(f.COUNT5_S * 10**3), f.COUNT5_32 * 10**3)
        assertEq(encode_b32(f.COUNT5_S * 10**6), f.COUNT5_32 * 10**6)

    def test_translates(self):
        """
        Test that random inputs encoded to both hex and crockford,
        have characters with equal indeces to encoded characters.
        """
        # Random data
        data = generate_data(1024, 42)
        hex = encode_b32_hex(data)
        crock = encode_b32(data)
        # Get lists of indices for each encoding from code set
        hex_indices = [self.BASE32_CODE_HEX.index(c) for c in hex]
        crock_indices = [self.BASE32_CODE_CROCK.index(c) for c in crock]
        for hex_i, crock_i in zip(hex_indices, crock_indices):
            self.assertEqual(hex_i, crock_i)

    def test_all_symbols(self):
        f = TFacts
        # Test all symbols in the base32 code set
        self.assertEqual(encode_b32(f.ALL_SYMBOLS_B), f.ALL_SYMBOLS_32C)

    def test_padding(self):
        assertEq = self.assertEqual
        # Low bit examples (multiples of repeat 0x00 bytes)
        assertEq(encode_b32(b"\x00" * 5), "00000000")
        assertEq(encode_b32(b"\x00" * 4), "0000000U")
        assertEq(encode_b32(b"\x00" * 3), "00000UUU")
        assertEq(encode_b32(b"\x00" * 2), "0000UUUU")
        assertEq(encode_b32(b"\x00" * 1), "00UUUUUU")

        # High bit examples (multiples of repeat 0xff bytes)
        # These have more complicated expected results
        assertEq(encode_b32(b"\xff" * 5), "ZZZZZZZZ")
        assertEq(encode_b32(b"\xff" * 4), "ZZZZZZRU")
        assertEq(encode_b32(b"\xff" * 3), "ZZZZYUUU")
        assertEq(encode_b32(b"\xff" * 2), "ZZZGUUUU")
        assertEq(encode_b32(b"\xff" * 1), "ZWUUUUUU")


class ValidateB32Decode(TestCase):
    def test_strict_uppercase(self):
        FN = validate_b32_decode
        FN("F00BAR", strict=True)
        FN("F00BAR123", strict=True)

    def test_strict_lowercase_raises(self):
        FN = validate_b32_decode
        with self.assertRaises(ValueError):
            FN("f00bar", strict=True)
        with self.assertRaises(ValueError):
            FN("F00BaR123", strict=True)

    def test_strict_raises_on_mistaken_chars(self):
        FN = validate_b32_decode
        with self.assertRaises(ValueError):
            FN("FOOBAR!", strict=True)
        with self.assertRaises(ValueError):
            FN("FOOBAR=", strict=True)

    def test_loose_raises_on_non_fixable_chars(self):
        with self.assertRaises(ValueError):
            validate_b32_decode("@FOOBAR")  # @ is not fixable

    def test_lowercase_returns_upper(self):
        FN = validate_b32_decode
        self.assertEqual(FN("XYZ123"), "XYZ123")
        self.assertEqual(FN("xyz123"), "XYZ123")

    def test_mistaken_chars_translate(self):
        FN = validate_b32_decode
        self.assertEqual(FN("OIL1"), "0111")
        self.assertEqual(FN("oil1"), "0111")
        self.assertEqual(FN("OIL1OIL="), "0111011U")

    def test_padding(self):
        FN = validate_b32_decode
        self.assertEqual(FN(TFacts.PAD0_32C), TFacts.PAD0_32C)


class DecodeB32HexTest(TestCase):
    def test_empty(self):
        self.assertEqual(decode_b32_hex(""), b"")

    def test_empty_and_type_return(self):
        FN = decode_b32_hex
        self.assertEqual(FN(""), b"")

    def test_alphabet(self):
        actual = decode_b32_hex(TFacts.ALL_SYMBOLS_32H).hex()
        expect = TFacts.ALL_SYMBOLS_B.hex()
        self.assertEqual(actual, expect)

    def test_hello(self):
        actual = decode_b32_hex(TFacts.HELLO_32H).decode("utf-8")
        expect = TFacts.HELLO_B.decode("utf-8")
        self.assertEqual(actual, expect)

    def test_padding(self):
        actual0 = decode_b32_hex(TFacts.PAD0_32H).hex()
        actual1 = decode_b32_hex(TFacts.PAD1_32H).hex()
        actual2 = decode_b32_hex(TFacts.PAD2_32H).hex()
        actual3 = decode_b32_hex(TFacts.PAD3_32H).hex()
        actual4 = decode_b32_hex(TFacts.PAD4_32H).hex()
        self.assertEqual(actual0, TFacts.PAD0_B.hex())
        self.assertEqual(actual1, TFacts.PAD1_B.hex())
        self.assertEqual(actual2, TFacts.PAD2_B.hex())
        self.assertEqual(actual3, TFacts.PAD3_B.hex())
        self.assertEqual(actual4, TFacts.PAD4_B.hex())


class DecodeB32Test(TestCase):
    def test_raises_on_non_alphanumeric(self):
        with self.assertRaises(ValueError):
            decode_b32("Hello, World!")
        with self.assertRaises(ValueError):
            decode_b32(".-_$")

    def test_strict_raises_on_lowercase(self):
        with self.assertRaises(ValueError):
            decode_b32("hello", strict=True)

    def test_calls_validate_with_strict_and_hexdecode(self):
        with patch("core.util.shortcode.validate_b32_decode") as mock_valid:
            with patch("core.util.shortcode.decode_b32_hex") as mock_decode:
                mock_valid.side_effect = lambda x, _: x
                decode_b32("foobar")
                mock_valid.assert_called_once_with("foobar", False)
                mock_decode.assert_called_once_with("foobar")
        with patch("core.util.shortcode.validate_b32_decode") as mock_valid:
            with patch("core.util.shortcode.decode_b32_hex") as mock_decode:
                mock_valid.side_effect = lambda x, _: x
                decode_b32("foobar", strict=True)
                mock_valid.assert_called_once_with("foobar", True)
                mock_decode.assert_called_once_with("foobar")

    def test_empty(self):
        self.assertEqual(decode_b32(""), b"")

    def test_correctness(self):
        FN = decode_b32
        self.assertEqual(FN(TFacts.ALL_SYMBOLS_32C).hex(), TFacts.ALL_SYMBOLS_B.hex())
        self.assertEqual(FN(TFacts.HELLO_32C).decode("ascii"), "Hello, World!")

    def test_padding(self):
        FN = decode_b32
        self.assertEqual(FN(TFacts.PAD0_32C).hex(), TFacts.PAD0_B.hex())
        self.assertEqual(FN(TFacts.PAD1_32C).hex(), TFacts.PAD1_B.hex())
        self.assertEqual(FN(TFacts.PAD2_32C).hex(), TFacts.PAD2_B.hex())
        self.assertEqual(FN(TFacts.PAD3_32C).hex(), TFacts.PAD3_B.hex())
        self.assertEqual(FN(TFacts.PAD4_32C).hex(), TFacts.PAD4_B.hex())


class CodecRoundTripTest(TestCase):
    """Tests that whatever you encode, gets decoded back to the original."""

    def round_trip(self, data):
        if isinstance(data, str):
            return decode_b32(encode_b32(data)).decode("utf-8")
        return decode_b32(encode_b32(data))

    def test_empty(self):
        self.assertEqual(s := b"", self.round_trip(s))
        self.assertEqual(s := "", self.round_trip(s))

    def test_strs(self):
        self.assertEqual(s := b"Hello, World!", self.round_trip(s))
        self.assertEqual(s := "Hello, World!", self.round_trip(s))
        self.assertEqual(s := "12345ABCD", self.round_trip(s))
        self.assertEqual(s := "12345ABCD" * 10**3, self.round_trip(s))

    def test_big(self):
        # NOTE: This can take a while to run, uncomment and test occassionally
        # big = generate_data(10 * 1024**2)
        # self.assertEqual(self.round_trip(big), big)
        self.assertEqual(s := TFacts.DATA_GEN_1MB, self.round_trip(s))
