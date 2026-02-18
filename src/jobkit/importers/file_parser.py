"""Parse resume files (PDF, DOCX, TXT)."""

import io
import re
from pathlib import Path
from typing import Optional

# Optional dependencies for file parsing
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class FileParser:
    """Parse resume files in various formats."""

    @staticmethod
    def parse(file_path: Path = None, file_bytes: bytes = None, filename: str = None) -> dict:
        """
        Parse a file and extract text content plus contact info.

        Args:
            file_path: Path to file on disk
            file_bytes: Raw file bytes (for uploads)
            filename: Original filename (needed for file_bytes to determine type)

        Returns:
            Dict with 'text', 'name', 'email', 'phone'
        """
        if file_path:
            filename = file_path.name
            file_bytes = file_path.read_bytes()

        if not file_bytes or not filename:
            raise ValueError("Must provide either file_path or (file_bytes and filename)")

        ext = Path(filename).suffix.lower()

        if ext == ".txt":
            raw_text = FileParser._parse_txt(file_bytes)
        elif ext == ".pdf":
            raw_text = FileParser._parse_pdf(file_bytes)
        elif ext in [".docx", ".doc"]:
            raw_text = FileParser._parse_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported: .txt, .pdf, .docx")

        # Extract contact info
        contact = FileParser._extract_contact_info(raw_text)

        # Format the text
        formatted_text = FileParser._format_resume_text(raw_text)

        return {
            "text": formatted_text,
            "name": contact.get("name", ""),
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
        }

    @staticmethod
    def _parse_txt(file_bytes: bytes) -> str:
        """Parse plain text file."""
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                return file_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not decode text file")

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> str:
        """Parse PDF file with better text extraction."""
        if not HAS_PYPDF:
            raise ImportError("pypdf package not installed. Run: pip install pypdf")

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text_parts = []

        for page in reader.pages:
            # Extract with layout preservation if possible
            text = page.extract_text()
            if text:
                text_parts.append(text)

        raw_text = "\n".join(text_parts)

        # Fix common PDF extraction issues
        raw_text = FileParser._fix_pdf_spacing(raw_text)

        return raw_text

    @staticmethod
    def _fix_pdf_spacing(text: str) -> str:
        """Fix common PDF text extraction spacing issues."""
        lines = text.split('\n')
        fixed_lines = []
        buffer = ""

        for line in lines:
            line = line.rstrip()

            # Skip empty lines - they're usually intentional section breaks
            if not line.strip():
                if buffer:
                    fixed_lines.append(buffer.strip())
                    buffer = ""
                fixed_lines.append("")
                continue

            # Check if this line looks like a continuation of the previous
            # (starts with lowercase, or previous line doesn't end with punctuation)
            is_continuation = (
                buffer and
                line and
                line[0].islower() and
                not buffer.rstrip().endswith(('.', '!', '?', ':', ';'))
            )

            # Check if line is very short (likely a header or broken line)
            is_short_fragment = len(line.strip()) < 40 and not line.strip().endswith(('.', '!', '?', ':'))

            # Check if this looks like a section header
            section_headers = [
                'EXPERIENCE', 'EDUCATION', 'SKILLS', 'SUMMARY', 'OBJECTIVE',
                'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EMPLOYMENT',
                'CERTIFICATIONS', 'PROJECTS', 'AWARDS', 'PUBLICATIONS',
                'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'QUALIFICATIONS',
                'PROFESSIONAL SUMMARY', 'CAREER SUMMARY', 'CONTACT', 'ABOUT'
            ]
            is_header = (
                line.strip().upper() in section_headers or
                any(line.strip().upper().startswith(h) for h in section_headers)
            )

            # Check if line starts with bullet point
            is_bullet = line.strip().startswith(('•', '-', '*', '–', '►', '○', '■', '●'))

            # Check if line looks like a job title/company line
            has_date = bool(re.search(r'\b(19|20)\d{2}\b', line))

            if is_header or is_bullet or has_date:
                # Start a new line
                if buffer:
                    fixed_lines.append(buffer.strip())
                    buffer = ""
                fixed_lines.append(line.strip())
            elif is_continuation and not is_header:
                # Join with previous
                buffer = buffer.rstrip() + " " + line.strip()
            else:
                # Start fresh
                if buffer:
                    fixed_lines.append(buffer.strip())
                buffer = line

        # Don't forget the last buffer
        if buffer:
            fixed_lines.append(buffer.strip())

        return '\n'.join(fixed_lines)

    @staticmethod
    def _extract_contact_info(text: str) -> dict:
        """Extract name, email, phone from resume text."""
        contact = {"name": "", "email": "", "phone": ""}

        # Extract email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            contact["email"] = email_match.group(0)

        # Extract phone - various formats
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (555) 123-4567, 555-123-4567
            r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 555 123 4567
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                contact["phone"] = phone_match.group(0)
                break

        # Extract name - look for a line that looks like a person's name
        # Names typically: 2-4 words, title case or caps, letters/hyphens/apostrophes only
        lines = text.strip().split('\n')

        # Words that indicate this is NOT a name
        skip_words = [
            'summary', 'experience', 'education', 'skills', 'objective', 'resume',
            'cv', 'profile', 'contact', 'about', 'professional', 'career', 'work',
            'phone', 'email', 'address', 'linkedin', 'github', 'portfolio',
            'senior', 'junior', 'lead', 'manager', 'director', 'engineer', 'developer',
            'analyst', 'consultant', 'specialist', 'coordinator', 'associate'
        ]

        for line in lines[:15]:  # Check first 15 lines
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Skip lines with email, phone, URLs
            if '@' in line or re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', line):
                continue
            if re.search(r'https?://|www\.|linkedin|github', line, re.I):
                continue

            # Skip lines with too many words (likely a sentence/description)
            words = line.split()
            if len(words) > 5 or len(words) < 1:
                continue

            # Skip if contains skip words
            line_lower = line.lower()
            if any(skip_word in line_lower for skip_word in skip_words):
                continue

            # Skip if has numbers (except maybe in suffixes like "III")
            if re.search(r'\d', line) and not re.search(r'\b(II|III|IV|Jr|Sr)\b', line, re.I):
                continue

            # Check if it looks like a name: mostly letters, maybe hyphens/apostrophes
            # Remove common suffixes/credentials first
            clean_line = re.sub(r',?\s*(CPA|MBA|PhD|MD|JD|PE|PMP|CFA|CISSP|PH\.?D|M\.?S|B\.?S|B\.?A)\.?', '', line, flags=re.I)
            clean_line = clean_line.strip(' ,.')

            # Name should be mostly alphabetic with spaces/hyphens
            if re.match(r"^[A-Za-z][A-Za-z\s\-'\.]+[A-Za-z]$", clean_line):
                # Good candidate - check word count again after cleaning
                clean_words = clean_line.split()
                if 1 <= len(clean_words) <= 4:
                    contact["name"] = clean_line
                    break

        return contact

    @staticmethod
    def _format_resume_text(text: str) -> str:
        """Clean up and format extracted resume text."""
        lines = text.split('\n')
        formatted_lines = []
        prev_line_empty = False

        section_headers = [
            'EXPERIENCE', 'EDUCATION', 'SKILLS', 'SUMMARY', 'OBJECTIVE',
            'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EMPLOYMENT',
            'CERTIFICATIONS', 'PROJECTS', 'AWARDS', 'PUBLICATIONS',
            'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'QUALIFICATIONS',
            'PROFESSIONAL SUMMARY', 'CAREER SUMMARY', 'CONTACT', 'ABOUT'
        ]

        for line in lines:
            line = line.strip()

            # Handle empty lines
            if not line:
                if not prev_line_empty:
                    formatted_lines.append("")
                    prev_line_empty = True
                continue

            prev_line_empty = False

            # Check if section header
            is_header = (
                line.upper() in section_headers or
                any(line.upper().startswith(h) for h in section_headers)
            )

            if is_header:
                if formatted_lines and formatted_lines[-1] != "":
                    formatted_lines.append("")
                formatted_lines.append(line.upper())
            else:
                formatted_lines.append(line)

        result = '\n'.join(formatted_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        """Parse DOCX file."""
        if not HAS_DOCX:
            raise ImportError("python-docx package not installed. Run: pip install python-docx")

        doc = docx.Document(io.BytesIO(file_bytes))
        text_parts = []

        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        return "\n\n".join(text_parts)
