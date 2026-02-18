"""PDF export functionality using pure Python (no system dependencies)."""

from pathlib import Path
import re

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False


def check_dependencies():
    """Check if required dependencies are installed."""
    if not HAS_FPDF:
        raise ImportError(
            "PDF export requires: fpdf2. "
            "Install with: pip install fpdf2"
        )


def clean_special_chars(text: str) -> str:
    """Replace problematic unicode characters with ASCII equivalents."""
    if not text:
        return ""

    # Comprehensive replacements for common special characters
    replacements = {
        # Quotes
        '\u2019': "'", '\u2018': "'", '\u201b': "'",
        '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u201f': '"',
        '\u0060': "'", '\u00b4': "'",
        # Dashes
        '\u2013': '-', '\u2014': '-', '\u2015': '-',
        '\u2212': '-', '\u2010': '-', '\u2011': '-',
        # Bullets and symbols
        '\u2022': '-',  # bullet
        '\u2023': '-',  # triangular bullet
        '\u2043': '-',  # hyphen bullet
        '\u00b7': '-',  # middle dot
        '\u25cf': '-',  # black circle
        '\u25cb': '-',  # white circle
        '\u25aa': '-',  # black square
        '\u25ab': '-',  # white square
        '\u25a0': '-',  # black square
        '\u25a1': '-',  # white square
        '\u2219': '-',  # bullet operator
        '\u00b0': ' degrees ',  # degree symbol
        '\uf0b7': '-',  # private use bullet (Word)
        '\uf0a7': '-',  # private use bullet (Word)
        # Spaces
        '\u00a0': ' ',  # non-breaking space
        '\u2003': ' ',  # em space
        '\u2002': ' ',  # en space
        '\u2009': ' ',  # thin space
        # Other
        '\u2026': '...',  # ellipsis
        '\u00ae': '(R)',  # registered
        '\u00a9': '(C)',  # copyright
        '\u2122': '(TM)',  # trademark
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Final pass: encode to latin-1 and replace any remaining problematic chars
    result = []
    for char in text:
        try:
            char.encode('latin-1')
            result.append(char)
        except UnicodeEncodeError:
            result.append('-')  # Replace with dash as safe fallback

    return ''.join(result)


class ResumePDF(FPDF):
    """Custom PDF with markdown-like formatting support."""

    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_margins(25, 20, 25)
        self.add_page()
        self.set_auto_page_break(auto=True, margin=20)
        self.text_width = 215.9 - 50  # Letter width minus margins

    def write_markdown_line(self, text: str, base_size: int = 10, auto_bold: bool = True):
        """Write text with inline **bold** support and auto-bolding of key patterns."""
        text = clean_special_chars(text)

        # First check for explicit **bold** markers
        if '**' in text:
            parts = re.split(r'(\*\*[^*]+\*\*)', text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    bold_text = clean_special_chars(part[2:-2])
                    self.set_font('Helvetica', 'B', base_size)
                    self.write(5, bold_text)
                    self.set_font('Helvetica', '', base_size)
                else:
                    clean = clean_special_chars(part)
                    if clean:
                        self.set_font('Helvetica', '', base_size)
                        self.write(5, clean)
        elif auto_bold and ':' in text:
            # Auto-bold text before colon (like "Skills: Python, SQL")
            colon_pos = text.find(':')
            before = text[:colon_pos].strip()
            after = text[colon_pos:].strip()

            # Only bold if the part before colon is short (likely a label)
            if len(before) < 40 and before:
                self.set_font('Helvetica', 'B', base_size)
                self.write(5, before)
                self.set_font('Helvetica', '', base_size)
                self.write(5, after)
            else:
                self.write(5, text)
        else:
            # Regular text
            clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # links
            clean = re.sub(r'`(.+?)`', r'\1', clean)  # inline code
            clean = clean_special_chars(clean)
            if clean:
                self.set_font('Helvetica', '', base_size)
                self.write(5, clean)

    def add_heading1(self, text: str):
        """Add H1 heading with underline."""
        self.ln(4)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(25, 60, 120)  # Dark blue
        text = clean_special_chars(text)
        self.set_x(25)
        self.multi_cell(self.text_width, 8, text, align='L')
        # Add colored underline
        y = self.get_y()
        self.set_draw_color(37, 99, 180)
        self.set_line_width(0.5)
        self.line(25, y, 190, y)
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def add_heading2(self, text: str):
        """Add H2 heading."""
        self.ln(5)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(40, 80, 140)  # Medium blue
        text = clean_special_chars(text)
        self.set_x(25)
        self.multi_cell(self.text_width, 7, text, align='L')
        self.ln(1)
        self.set_text_color(0, 0, 0)

    def add_heading3(self, text: str):
        """Add H3 heading."""
        self.ln(3)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(60, 60, 60)
        text = clean_special_chars(text)
        self.set_x(25)
        self.multi_cell(self.text_width, 6, text, align='L')
        self.set_text_color(0, 0, 0)

    def add_bullet(self, text: str):
        """Add bullet point."""
        self.set_font('Helvetica', '', 10)
        self.set_x(30)
        self.set_text_color(37, 99, 180)  # Blue bullet
        self.write(5, "- ")
        self.set_text_color(0, 0, 0)
        self.write_markdown_line(text, base_size=10)
        self.ln(5)

    def add_numbered(self, num: str, text: str):
        """Add numbered item."""
        self.set_font('Helvetica', 'B', 10)
        self.set_x(30)
        self.set_text_color(37, 99, 180)
        self.write(5, f"{num}. ")
        self.set_text_color(0, 0, 0)
        self.set_font('Helvetica', '', 10)
        self.write_markdown_line(text, base_size=10)
        self.ln(5)

    def add_paragraph(self, text: str):
        """Add regular paragraph with inline formatting."""
        self.set_x(25)
        self.write_markdown_line(text, base_size=10)
        self.ln(5)


def clean_markdown_line(line: str) -> str:
    """Remove stray markdown header characters from a line (but keep bold markers)."""
    # Remove stray ## or ### at start (with possible spaces)
    line = re.sub(r'^#+\s*', '', line)
    # Don't remove ** markers - they're used for bold formatting
    return line.strip()


def export_to_pdf(markdown_content: str, output_path: Path = None) -> bytes:
    """Convert markdown content to PDF."""
    check_dependencies()

    # Clean the entire content first
    markdown_content = clean_special_chars(markdown_content)

    pdf = ResumePDF()
    lines = markdown_content.split('\n')

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            pdf.ln(2)
            continue

        # Skip markdown artifacts
        if line in ['```', '```markdown', '---', '***', '===']:
            continue

        # H1: # Header (but not ##)
        if re.match(r'^#\s+[^#]', line):
            pdf.add_heading1(line[1:].strip().lstrip('#').strip())

        # H2: ## Header (but not ###)
        elif re.match(r'^##\s+[^#]', line) or re.match(r'^##\s*$', line) is None and line.startswith('## '):
            pdf.add_heading2(line[2:].strip().lstrip('#').strip())

        # H3: ### Header
        elif line.startswith('### '):
            pdf.add_heading3(line[3:].strip().lstrip('#').strip())

        # Bullet point
        elif line.startswith('- ') or line.startswith('* '):
            pdf.add_bullet(line[2:].strip())

        # Numbered list
        elif re.match(r'^\d+[\.\)]\s', line):
            match = re.match(r'^(\d+)[\.\)]\s*(.*)$', line)
            if match:
                num, text = match.groups()
                pdf.add_numbered(num, text)

        # Line that's just "##" or similar - skip it
        elif re.match(r'^#+\s*$', line):
            continue

        # Check if line is ALL CAPS (likely a section header)
        elif line.isupper() and len(line) < 50 and len(line.split()) <= 5:
            pdf.add_heading2(line)

        # Regular paragraph - clean any stray markdown
        else:
            cleaned = clean_markdown_line(line)
            if cleaned:
                pdf.add_paragraph(cleaned)

    if output_path:
        pdf.output(output_path)
        return output_path.read_bytes()
    else:
        return pdf.output()
