"""ESC/POS command builder for thermal receipt printers."""


class ESCPOSBuilder:
    """Builds ESC/POS command byte sequences for the Nucoun VCP-8370."""

    # Command constants
    ESC = b'\x1b'
    GS = b'\x1d'
    LF = b'\x0a'

    # Initialize printer
    INIT = b'\x1b\x40'

    # Text formatting
    BOLD_ON = b'\x1b\x45\x01'
    BOLD_OFF = b'\x1b\x45\x00'
    UNDERLINE_ON = b'\x1b\x2d\x01'
    UNDERLINE_OFF = b'\x1b\x2d\x00'
    DOUBLE_HEIGHT_ON = b'\x1b\x21\x10'
    DOUBLE_WIDTH_ON = b'\x1b\x21\x20'
    DOUBLE_HW_ON = b'\x1b\x21\x30'
    NORMAL_SIZE = b'\x1b\x21\x00'

    # Text alignment
    ALIGN_LEFT = b'\x1b\x61\x00'
    ALIGN_CENTER = b'\x1b\x61\x01'
    ALIGN_RIGHT = b'\x1b\x61\x02'

    # Font selection
    FONT_A = b'\x1b\x4d\x00'  # 12x24
    FONT_B = b'\x1b\x4d\x01'  # 9x17
    FONT_C = b'\x1b\x4d\x02'  # 9x24

    # Paper cutting
    FULL_CUT = b'\x1d\x56\x00'
    PARTIAL_CUT = b'\x1d\x56\x01'

    # Line spacing
    DEFAULT_LINE_SPACING = b'\x1b\x32'

    def __init__(self):
        self._buffer = bytearray()

    def reset(self):
        """Reset buffer and initialize printer."""
        self._buffer = bytearray()
        self._buffer.extend(self.INIT)
        return self

    def text(self, content):
        """Add text to the buffer."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        self._buffer.extend(content)
        return self

    def newline(self, count=1):
        """Add line feed(s)."""
        self._buffer.extend(self.LF * count)
        return self

    def feed(self, lines=1):
        """Feed paper by number of lines."""
        self._buffer.extend(b'\x1b\x64' + bytes([lines]))
        return self

    def bold(self, on=True):
        """Set bold mode."""
        self._buffer.extend(self.BOLD_ON if on else self.BOLD_OFF)
        return self

    def underline(self, on=True):
        """Set underline mode."""
        self._buffer.extend(self.UNDERLINE_ON if on else self.UNDERLINE_OFF)
        return self

    def align(self, alignment='left'):
        """Set text alignment: 'left', 'center', or 'right'."""
        commands = {
            'left': self.ALIGN_LEFT,
            'center': self.ALIGN_CENTER,
            'right': self.ALIGN_RIGHT,
        }
        self._buffer.extend(commands.get(alignment, self.ALIGN_LEFT))
        return self

    def font(self, name='A'):
        """Set font: 'A' (12x24), 'B' (9x17), or 'C' (9x24)."""
        fonts = {
            'A': self.FONT_A,
            'B': self.FONT_B,
            'C': self.FONT_C,
        }
        self._buffer.extend(fonts.get(name.upper(), self.FONT_A))
        return self

    def size(self, width=1, height=1):
        """Set character size (1-8x for width and height)."""
        if not (1 <= width <= 8 and 1 <= height <= 8):
            width = max(1, min(8, width))
            height = max(1, min(8, height))
        size_byte = ((width - 1) << 4) | (height - 1)
        self._buffer.extend(b'\x1d\x21' + bytes([size_byte]))
        return self

    def separator(self, char='-', width=48):
        """Print a separator line."""
        self._buffer.extend((char * width).encode('utf-8'))
        self._buffer.extend(self.LF)
        return self

    def two_columns(self, left, right, width=48):
        """Print text in two columns (left-aligned and right-aligned)."""
        space = width - len(left) - len(right)
        if space < 1:
            space = 1
        line = left + (' ' * space) + right
        self.text(line)
        self.newline()
        return self

    def barcode(self, data, barcode_type=73, height=80, width=2):
        """Print a 1D barcode.

        barcode_type: 65=UPC-A, 66=UPC-E, 67=EAN13, 68=EAN8,
                      69=CODE39, 70=ITF, 71=CODABAR, 72=CODE93, 73=CODE128
        """
        # Set barcode height
        self._buffer.extend(b'\x1d\x68' + bytes([height]))
        # Set barcode width
        self._buffer.extend(b'\x1d\x77' + bytes([width]))
        # Set HRI (Human Readable Interpretation) below barcode
        self._buffer.extend(b'\x1d\x48\x02')
        # Print barcode
        if isinstance(data, str):
            data = data.encode('utf-8')
        self._buffer.extend(b'\x1d\x6b' + bytes([barcode_type, len(data)]) + data)
        return self

    def qr_code(self, data, size=6, error_correction=49):
        """Print a QR code.

        size: 1-16 (module size)
        error_correction: 48=L, 49=M, 50=Q, 51=H
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        length = len(data) + 3
        pl = length % 256
        ph = length // 256

        # QR model 2
        self._buffer.extend(b'\x1d\x28\x6b\x04\x00\x31\x41\x32\x00')
        # QR size
        self._buffer.extend(b'\x1d\x28\x6b\x03\x00\x31\x43' + bytes([size]))
        # QR error correction
        self._buffer.extend(b'\x1d\x28\x6b\x03\x00\x31\x45' + bytes([error_correction]))
        # Store QR data
        self._buffer.extend(b'\x1d\x28\x6b' + bytes([pl, ph]) + b'\x31\x50\x30' + data)
        # Print QR code
        self._buffer.extend(b'\x1d\x28\x6b\x03\x00\x31\x51\x30')
        return self

    def cut(self, partial=False):
        """Cut paper (full or partial)."""
        self.feed(3)
        self._buffer.extend(self.PARTIAL_CUT if partial else self.FULL_CUT)
        return self

    def build(self):
        """Return the accumulated command buffer as bytes."""
        return bytes(self._buffer)

    def __len__(self):
        return len(self._buffer)
