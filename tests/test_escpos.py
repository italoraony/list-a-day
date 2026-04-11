"""Tests for ESC/POS command builder."""

import pytest
from lib.escpos import ESCPOSBuilder


class TestESCPOSBuilderInit:
    def test_empty_buffer_on_init(self):
        b = ESCPOSBuilder()
        assert len(b) == 0
        assert b.build() == b""

    def test_reset_adds_init_command(self):
        b = ESCPOSBuilder()
        b.reset()
        assert b.build() == b"\x1b\x40"

    def test_reset_clears_previous_data(self):
        b = ESCPOSBuilder()
        b.text("hello")
        b.reset()
        assert b.build() == b"\x1b\x40"


class TestESCPOSBuilderText:
    def test_text_string(self):
        b = ESCPOSBuilder()
        b.text("Hello")
        assert b.build() == b"Hello"

    def test_text_bytes(self):
        b = ESCPOSBuilder()
        b.text(b"raw bytes")
        assert b.build() == b"raw bytes"

    def test_text_utf8_encoding(self):
        b = ESCPOSBuilder()
        b.text("café")
        assert b.build() == "café".encode("utf-8")

    def test_text_empty_string(self):
        b = ESCPOSBuilder()
        b.text("")
        assert b.build() == b""

    def test_text_chaining(self):
        b = ESCPOSBuilder()
        result = b.text("a").text("b").text("c")
        assert result is b
        assert b.build() == b"abc"


class TestESCPOSBuilderNewlineAndFeed:
    def test_single_newline(self):
        b = ESCPOSBuilder()
        b.newline()
        assert b.build() == b"\x0a"

    def test_multiple_newlines(self):
        b = ESCPOSBuilder()
        b.newline(3)
        assert b.build() == b"\x0a\x0a\x0a"

    def test_feed_one_line(self):
        b = ESCPOSBuilder()
        b.feed(1)
        assert b.build() == b"\x1b\x64\x01"

    def test_feed_five_lines(self):
        b = ESCPOSBuilder()
        b.feed(5)
        assert b.build() == b"\x1b\x64\x05"


class TestESCPOSBuilderFormatting:
    def test_bold_on(self):
        b = ESCPOSBuilder()
        b.bold(True)
        assert b.build() == b"\x1b\x45\x01"

    def test_bold_off(self):
        b = ESCPOSBuilder()
        b.bold(False)
        assert b.build() == b"\x1b\x45\x00"

    def test_underline_on(self):
        b = ESCPOSBuilder()
        b.underline(True)
        assert b.build() == b"\x1b\x2d\x01"

    def test_underline_off(self):
        b = ESCPOSBuilder()
        b.underline(False)
        assert b.build() == b"\x1b\x2d\x00"

    def test_bold_default_is_on(self):
        b = ESCPOSBuilder()
        b.bold()
        assert b.build() == b"\x1b\x45\x01"

    def test_underline_default_is_on(self):
        b = ESCPOSBuilder()
        b.underline()
        assert b.build() == b"\x1b\x2d\x01"


class TestESCPOSBuilderAlignment:
    def test_align_left(self):
        b = ESCPOSBuilder()
        b.align("left")
        assert b.build() == b"\x1b\x61\x00"

    def test_align_center(self):
        b = ESCPOSBuilder()
        b.align("center")
        assert b.build() == b"\x1b\x61\x01"

    def test_align_right(self):
        b = ESCPOSBuilder()
        b.align("right")
        assert b.build() == b"\x1b\x61\x02"

    def test_align_invalid_defaults_to_left(self):
        b = ESCPOSBuilder()
        b.align("invalid")
        assert b.build() == b"\x1b\x61\x00"

    def test_align_default_is_left(self):
        b = ESCPOSBuilder()
        b.align()
        assert b.build() == b"\x1b\x61\x00"


class TestESCPOSBuilderFont:
    def test_font_a(self):
        b = ESCPOSBuilder()
        b.font("A")
        assert b.build() == b"\x1b\x4d\x00"

    def test_font_b(self):
        b = ESCPOSBuilder()
        b.font("B")
        assert b.build() == b"\x1b\x4d\x01"

    def test_font_c(self):
        b = ESCPOSBuilder()
        b.font("C")
        assert b.build() == b"\x1b\x4d\x02"

    def test_font_lowercase(self):
        b = ESCPOSBuilder()
        b.font("b")
        assert b.build() == b"\x1b\x4d\x01"

    def test_font_invalid_defaults_to_a(self):
        b = ESCPOSBuilder()
        b.font("Z")
        assert b.build() == b"\x1b\x4d\x00"

    def test_font_default_is_a(self):
        b = ESCPOSBuilder()
        b.font()
        assert b.build() == b"\x1b\x4d\x00"


class TestESCPOSBuilderSize:
    def test_size_1x1(self):
        b = ESCPOSBuilder()
        b.size(1, 1)
        # size_byte = ((1-1) << 4) | (1-1) = 0x00
        assert b.build() == b"\x1d\x21\x00"

    def test_size_2x2(self):
        b = ESCPOSBuilder()
        b.size(2, 2)
        # size_byte = ((2-1) << 4) | (2-1) = 0x11
        assert b.build() == b"\x1d\x21\x11"

    def test_size_8x8(self):
        b = ESCPOSBuilder()
        b.size(8, 8)
        # size_byte = ((8-1) << 4) | (8-1) = 0x77
        assert b.build() == b"\x1d\x21\x77"

    def test_size_clamps_high_values(self):
        b = ESCPOSBuilder()
        b.size(10, 10)
        # Clamped to 8x8 = 0x77
        assert b.build() == b"\x1d\x21\x77"

    def test_size_clamps_low_values(self):
        b = ESCPOSBuilder()
        b.size(0, 0)
        # Clamped to 1x1 = 0x00
        assert b.build() == b"\x1d\x21\x00"

    def test_size_asymmetric(self):
        b = ESCPOSBuilder()
        b.size(3, 1)
        # size_byte = ((3-1) << 4) | (1-1) = 0x20
        assert b.build() == b"\x1d\x21\x20"


class TestESCPOSBuilderSeparator:
    def test_default_separator(self):
        b = ESCPOSBuilder()
        b.separator()
        expected = (b"-" * 48) + b"\x0a"
        assert b.build() == expected

    def test_custom_separator(self):
        b = ESCPOSBuilder()
        b.separator("=", 10)
        expected = (b"=" * 10) + b"\x0a"
        assert b.build() == expected


class TestESCPOSBuilderTwoColumns:
    def test_two_columns_basic(self):
        b = ESCPOSBuilder()
        b.two_columns("Left", "Right", 20)
        result = b.build()
        assert b"Left" in result
        assert b"Right" in result
        # Total width should produce: "Left" + spaces + "Right" + LF
        text_part = result.rstrip(b"\x0a")
        assert len(text_part) == 20

    def test_two_columns_overflow(self):
        b = ESCPOSBuilder()
        b.two_columns("A" * 10, "B" * 10, 15)
        result = b.build()
        # space should be at least 1 even if overflow
        assert b"A" * 10 in result
        assert b"B" * 10 in result


class TestESCPOSBuilderBarcode:
    def test_barcode_string_data(self):
        b = ESCPOSBuilder()
        b.barcode("12345", barcode_type=73, height=80, width=2)
        result = b.build()
        # Should contain height, width, HRI, and barcode commands
        assert b"\x1d\x68\x50" in result  # height = 80
        assert b"\x1d\x77\x02" in result  # width = 2
        assert b"\x1d\x48\x02" in result  # HRI below
        assert b"12345" in result

    def test_barcode_bytes_data(self):
        b = ESCPOSBuilder()
        b.barcode(b"ABC", barcode_type=69)
        result = b.build()
        assert b"ABC" in result


class TestESCPOSBuilderQRCode:
    def test_qr_code_string_data(self):
        b = ESCPOSBuilder()
        b.qr_code("https://example.com")
        result = b.build()
        assert b"https://example.com" in result
        # Should contain model, size, error correction, store, print commands
        assert b"\x1d\x28\x6b" in result

    def test_qr_code_bytes_data(self):
        b = ESCPOSBuilder()
        b.qr_code(b"test")
        result = b.build()
        assert b"test" in result

    def test_qr_code_custom_size(self):
        b = ESCPOSBuilder()
        b.qr_code("data", size=10)
        result = b.build()
        # Size command: \x1d\x28\x6b\x03\x00\x31\x43 + size_byte
        assert b"\x1d\x28\x6b\x03\x00\x31\x43\x0a" in result


class TestESCPOSBuilderCut:
    def test_full_cut(self):
        b = ESCPOSBuilder()
        b.cut()
        result = b.build()
        assert result.endswith(b"\x1d\x56\x00")
        # Should contain feed before cut
        assert b"\x1b\x64\x03" in result

    def test_partial_cut(self):
        b = ESCPOSBuilder()
        b.cut(partial=True)
        result = b.build()
        assert result.endswith(b"\x1d\x56\x01")


class TestESCPOSBuilderChaining:
    def test_fluent_interface(self):
        b = ESCPOSBuilder()
        result = (
            b.reset()
            .bold(True)
            .align("center")
            .text("Title")
            .newline()
            .bold(False)
            .cut()
        )
        assert result is b
        data = b.build()
        assert len(data) > 0
        assert data.startswith(b"\x1b\x40")  # INIT
        assert b"Title" in data
        assert data.endswith(b"\x1d\x56\x00")  # FULL_CUT

    def test_build_returns_bytes(self):
        b = ESCPOSBuilder()
        b.text("test")
        assert isinstance(b.build(), bytes)

    def test_len_matches_build(self):
        b = ESCPOSBuilder()
        b.reset().text("hello").newline()
        assert len(b) == len(b.build())
