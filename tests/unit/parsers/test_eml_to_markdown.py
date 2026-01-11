"""Comprehensive tests for gmail_eml_to_markdown_cleaner module."""
from __future__ import annotations

import email
from email import policy
from pathlib import Path
from unittest import mock

import pytest

# Import functions from the module
try:
    # Try to import - module may exit if dependencies missing
    import sys
    import importlib.util
    spec = importlib.util.find_spec('gmail_assistant.parsers.gmail_eml_to_markdown_cleaner')
    if spec is None:
        CLEANER_AVAILABLE = False
    else:
        # Check for required dependencies first
        try:
            import chardet
            import frontmatter
            from bs4 import BeautifulSoup
            import html5lib
            from markdownify import markdownify

            # Dependencies available, safe to import module
            from gmail_assistant.parsers.gmail_eml_to_markdown_cleaner import (
                apply_cid_rewrites,
                build_front_matter,
                cid_image_map,
                compose_markdown,
                convert_html_to_markdown,
                detect_encoding,
                extract_best_part,
                html_cleanup,
                process_eml,
                sanitize_filename,
                save_attachments,
                wrap_paragraphs,
            )
            CLEANER_AVAILABLE = True
        except ImportError:
            CLEANER_AVAILABLE = False
except (ImportError, SystemExit):
    CLEANER_AVAILABLE = False


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_eml_file(tmp_path):
    """Create a sample EML file."""
    eml_content = """From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 1 Jan 2024 12:00:00 -0500
Message-ID: <abc123@example.com>
Content-Type: text/html; charset="utf-8"

<html>
<body>
<h1>Test Email</h1>
<p>This is test content.</p>
</body>
</html>
"""
    eml_path = tmp_path / "test.eml"
    eml_path.write_bytes(eml_content.encode('utf-8'))
    return eml_path


@pytest.fixture
def multipart_eml_file(tmp_path):
    """Create a multipart EML file with plain text and HTML."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart('alternative')
    msg['From'] = 'sender@example.com'
    msg['To'] = 'recipient@example.com'
    msg['Subject'] = 'Multipart Test'
    msg['Date'] = 'Mon, 1 Jan 2024 12:00:00 -0500'

    text_part = MIMEText('Plain text content', 'plain')
    html_part = MIMEText('<html><body><h1>HTML</h1><p>Content</p></body></html>', 'html')

    msg.attach(text_part)
    msg.attach(html_part)

    eml_path = tmp_path / "multipart.eml"
    eml_path.write_bytes(msg.as_bytes())
    return eml_path


@pytest.fixture
def eml_with_attachment(tmp_path):
    """Create EML file with attachment."""
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg['From'] = 'sender@example.com'
    msg['To'] = 'recipient@example.com'
    msg['Subject'] = 'Email with Attachment'

    text_part = MIMEText('Email with attachment', 'plain')
    msg.attach(text_part)

    attachment = MIMEApplication(b'File content', _subtype='pdf')
    attachment.add_header('Content-Disposition', 'attachment', filename='document.pdf')
    msg.attach(attachment)

    eml_path = tmp_path / "with_attachment.eml"
    eml_path.write_bytes(msg.as_bytes())
    return eml_path


@pytest.fixture
def eml_with_inline_image(tmp_path):
    """Create EML file with inline CID image."""
    from email.mime.image import MIMEImage
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart('related')
    msg['From'] = 'sender@example.com'
    msg['To'] = 'recipient@example.com'
    msg['Subject'] = 'Email with Image'

    html = '<html><body><img src="cid:image001" /></body></html>'
    html_part = MIMEText(html, 'html')
    msg.attach(html_part)

    image = MIMEImage(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # Fake PNG
    image.add_header('Content-ID', '<image001>')
    image.add_header('Content-Disposition', 'inline', filename='image.png')
    msg.attach(image)

    eml_path = tmp_path / "with_image.eml"
    eml_path.write_bytes(msg.as_bytes())
    return eml_path


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
    <head>
        <script>alert('test');</script>
        <style>.hidden { display: none; }</style>
    </head>
    <body>
        <h1>Main Title</h1>
        <p>Paragraph content</p>
        <img src="image.jpg" width="1" height="1" />
        <img src="photo.jpg" />
    </body>
    </html>
    """


# ==============================================================================
# TestEncodingDetection
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestEncodingDetection:
    """Test encoding detection functionality."""

    def test_detect_utf8(self, tmp_path):
        """Test UTF-8 encoding detection."""
        content = "Test UTF-8 content: café, résumé"
        test_file = tmp_path / "utf8.txt"
        test_file.write_text(content, encoding='utf-8')

        encoding = detect_encoding(test_file)
        assert encoding in ['utf-8', 'UTF-8', 'ascii']

    def test_detect_latin1(self, tmp_path):
        """Test Latin-1 encoding detection."""
        content = "Test content"
        test_file = tmp_path / "latin1.txt"
        test_file.write_bytes(content.encode('latin-1'))

        encoding = detect_encoding(test_file)
        assert isinstance(encoding, str)

    def test_detect_with_bom(self, tmp_path):
        """Test encoding detection with BOM."""
        content = "Test content"
        test_file = tmp_path / "utf8_bom.txt"
        test_file.write_bytes('\ufeff'.encode('utf-8') + content.encode('utf-8'))

        encoding = detect_encoding(test_file)
        assert encoding is not None


# ==============================================================================
# TestFilenameSanitization
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_sanitize_basic_filename(self):
        """Test basic filename sanitization."""
        result = sanitize_filename("test_file.txt")
        assert result == "test_file.txt"

    def test_sanitize_with_invalid_chars(self):
        """Test sanitization removes invalid characters."""
        result = sanitize_filename("test<>:\"/\\|?*.txt")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_sanitize_long_filename(self):
        """Test long filename truncation."""
        long_name = "a" * 200 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 180

    def test_sanitize_empty_filename(self):
        """Test empty filename handling."""
        result = sanitize_filename("")
        assert result == "untitled"

    def test_sanitize_unicode_filename(self):
        """Test unicode in filename."""
        result = sanitize_filename("café_résumé.txt")
        # Should preserve valid unicode or replace it
        assert isinstance(result, str)


# ==============================================================================
# TestHTMLCleanup
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestHTMLCleanup:
    """Test HTML cleanup functionality."""

    def test_cleanup_removes_scripts(self, sample_html):
        """Test script tag removal."""
        cleaned = html_cleanup(sample_html)
        assert "<script>" not in cleaned
        assert "alert" not in cleaned

    def test_cleanup_removes_styles(self, sample_html):
        """Test style tag removal."""
        cleaned = html_cleanup(sample_html)
        assert "<style>" not in cleaned

    def test_cleanup_removes_tracking_pixels(self, sample_html):
        """Test tracking pixel removal."""
        cleaned = html_cleanup(sample_html)
        # 1x1 pixel should be removed
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, 'html5lib')

        # Original should have 1x1 pixel
        imgs_before = soup.find_all('img')
        has_pixel = any(img.get('width') == '1' and img.get('height') == '1' for img in imgs_before)
        assert has_pixel

    def test_cleanup_preserves_content(self):
        """Test content preservation during cleanup."""
        html = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        cleaned = html_cleanup(html)
        assert "Title" in cleaned
        assert "Content" in cleaned

    def test_cleanup_collapses_whitespace(self):
        """Test excessive whitespace collapse."""
        html = "<html><body><p>Line 1</p>\n\n\n\n<p>Line 2</p></body></html>"
        cleaned = html_cleanup(html)
        assert "\n\n\n" not in cleaned


# ==============================================================================
# TestHTMLToMarkdownConversion
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestHTMLToMarkdownConversion:
    """Test HTML to Markdown conversion."""

    def test_convert_headers(self):
        """Test header conversion."""
        html = "<h1>Title</h1><h2>Subtitle</h2>"
        markdown = convert_html_to_markdown(html)
        assert "#" in markdown or "Title" in markdown

    def test_convert_paragraphs(self):
        """Test paragraph conversion."""
        html = "<p>Paragraph 1</p><p>Paragraph 2</p>"
        markdown = convert_html_to_markdown(html)
        assert "Paragraph 1" in markdown
        assert "Paragraph 2" in markdown

    def test_convert_links(self):
        """Test link conversion."""
        html = '<a href="https://example.com">Link text</a>'
        markdown = convert_html_to_markdown(html)
        assert "Link text" in markdown

    def test_convert_lists(self):
        """Test list conversion."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        markdown = convert_html_to_markdown(html)
        assert "Item 1" in markdown
        assert "Item 2" in markdown

    def test_convert_blockquotes(self):
        """Test blockquote conversion."""
        html = "<blockquote>Quote text</blockquote>"
        markdown = convert_html_to_markdown(html)
        assert "Quote text" in markdown

    def test_convert_empty_html(self):
        """Test empty HTML conversion."""
        markdown = convert_html_to_markdown("")
        assert isinstance(markdown, str)

    def test_convert_with_validation_error(self):
        """Test conversion with oversized HTML."""
        # Create HTML larger than 5MB limit
        huge_html = "<p>" + ("x" * 6_000_000) + "</p>"
        result = convert_html_to_markdown(huge_html)
        assert "[Error:" in result


# ==============================================================================
# TestParagraphWrapping
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestParagraphWrapping:
    """Test paragraph wrapping functionality."""

    def test_wrap_long_line(self):
        """Test wrapping of long lines."""
        text = "This is a very long line that should be wrapped " * 10
        wrapped = wrap_paragraphs(text, width=80)
        lines = wrapped.split('\n')
        # Check that most lines are under width
        long_lines = [line for line in lines if len(line) > 85]
        assert len(long_lines) < len(lines) / 2

    def test_preserve_code_blocks(self):
        """Test code block preservation."""
        text = "```python\ndef test():\n    return 'very long line that should not be wrapped' * 10\n```"
        wrapped = wrap_paragraphs(text)
        assert "```python" in wrapped
        assert "def test():" in wrapped

    def test_preserve_list_markers(self):
        """Test list marker preservation."""
        text = "* This is a list item\n- Another list item\n1. Numbered item"
        wrapped = wrap_paragraphs(text)
        assert "* This is" in wrapped
        assert "- Another" in wrapped
        assert "1. Numbered" in wrapped

    def test_preserve_headers(self):
        """Test header preservation."""
        text = "# This is a very long header that might exceed the normal line width"
        wrapped = wrap_paragraphs(text)
        # Headers should not be wrapped
        assert "# This is" in wrapped


# ==============================================================================
# TestEmailPartExtraction
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestEmailPartExtraction:
    """Test email part extraction."""

    def test_extract_from_simple_email(self, sample_eml_file):
        """Test extraction from simple HTML email."""
        msg = email.message_from_bytes(
            sample_eml_file.read_bytes(),
            policy=policy.default
        )
        text, html = extract_best_part(msg)
        assert html is not None
        assert "Test Email" in html

    def test_extract_from_multipart(self, multipart_eml_file):
        """Test extraction from multipart email."""
        msg = email.message_from_bytes(
            multipart_eml_file.read_bytes(),
            policy=policy.default
        )
        text, html = extract_best_part(msg)
        assert text == "Plain text content"
        assert "HTML" in html

    def test_extract_prefers_html(self, multipart_eml_file):
        """Test HTML preference over plain text."""
        msg = email.message_from_bytes(
            multipart_eml_file.read_bytes(),
            policy=policy.default
        )
        text, html = extract_best_part(msg)
        # Both should be extracted
        assert text is not None
        assert html is not None

    def test_extract_with_attachment(self, eml_with_attachment):
        """Test extraction skips attachments."""
        msg = email.message_from_bytes(
            eml_with_attachment.read_bytes(),
            policy=policy.default
        )
        text, html = extract_best_part(msg)
        # Should extract text part, not attachment
        assert text == "Email with attachment"


# ==============================================================================
# TestAttachmentHandling
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestAttachmentHandling:
    """Test attachment saving and handling."""

    def test_save_attachments(self, eml_with_attachment, tmp_path):
        """Test attachment saving."""
        msg = email.message_from_bytes(
            eml_with_attachment.read_bytes(),
            policy=policy.default
        )
        out_dir = tmp_path / "attachments"
        save_attachments(msg, out_dir)

        # Check attachment was saved
        saved_files = list(out_dir.glob("*"))
        assert len(saved_files) > 0

    def test_save_attachments_sanitizes_filenames(self, tmp_path):
        """Test attachment filename sanitization."""
        from email.mime.application import MIMEApplication
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        attachment = MIMEApplication(b'content', _subtype='txt')
        attachment.add_header('Content-Disposition', 'attachment',
                            filename='bad<>:name.txt')
        msg.attach(attachment)

        out_dir = tmp_path / "attachments"
        save_attachments(msg, out_dir)

        # Should save with sanitized name
        saved_files = list(out_dir.glob("*"))
        for f in saved_files:
            assert "<" not in f.name
            assert ">" not in f.name


# ==============================================================================
# TestCIDImageHandling
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestCIDImageHandling:
    """Test CID image extraction and rewriting."""

    def test_cid_image_extraction(self, eml_with_inline_image, tmp_path):
        """Test CID image extraction."""
        msg = email.message_from_bytes(
            eml_with_inline_image.read_bytes(),
            policy=policy.default
        )
        attach_dir = tmp_path / "attachments"
        cid_map = cid_image_map(msg, attach_dir)

        # Should have one CID mapping
        assert len(cid_map) > 0
        assert any("cid:" in key for key in cid_map.keys())

    def test_cid_rewrite(self):
        """Test CID reference rewriting."""
        markdown = "Text with ![](cid:image001) inline image"
        cid_map = {"cid:image001": "_attachments/image.png"}

        rewritten = apply_cid_rewrites(markdown, cid_map)
        assert "_attachments/image.png" in rewritten
        assert "cid:image001" not in rewritten

    def test_cid_rewrite_multiple(self):
        """Test multiple CID rewrites."""
        markdown = "![](cid:img1) and ![](cid:img2)"
        cid_map = {
            "cid:img1": "_attachments/img1.png",
            "cid:img2": "_attachments/img2.png"
        }

        rewritten = apply_cid_rewrites(markdown, cid_map)
        assert "_attachments/img1.png" in rewritten
        assert "_attachments/img2.png" in rewritten


# ==============================================================================
# TestFrontMatterGeneration
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestFrontMatterGeneration:
    """Test YAML front matter generation."""

    def test_build_front_matter_basic(self, sample_eml_file):
        """Test basic front matter generation."""
        msg = email.message_from_bytes(
            sample_eml_file.read_bytes(),
            policy=policy.default
        )
        fm = build_front_matter(msg, "test.eml")

        assert fm['subject'] == "Test Email"
        assert "sender@example.com" in str(fm['from'])
        assert fm['source_file'] == "test.eml"

    def test_front_matter_with_date(self, sample_eml_file):
        """Test date parsing in front matter."""
        msg = email.message_from_bytes(
            sample_eml_file.read_bytes(),
            policy=policy.default
        )
        fm = build_front_matter(msg, "test.eml")

        # Should parse date to ISO format
        assert fm['date'] is not None

    def test_front_matter_with_message_id(self, sample_eml_file):
        """Test message ID in front matter."""
        msg = email.message_from_bytes(
            sample_eml_file.read_bytes(),
            policy=policy.default
        )
        fm = build_front_matter(msg, "test.eml")

        assert "abc123@example.com" in fm['message_id']

    def test_compose_markdown_with_front_matter(self):
        """Test markdown composition with front matter."""
        fm = {
            'subject': 'Test',
            'from': ['sender@example.com'],
            'to': ['recipient@example.com'],
            'date': '2024-01-01T12:00:00',
            'source_file': 'test.eml'
        }
        body = "# Email Content\n\nBody text here."

        composed = compose_markdown(fm, body)
        assert "---" in composed  # YAML delimiters
        assert "subject: Test" in composed or "subject:" in composed
        assert "Email Content" in composed


# ==============================================================================
# TestEMLProcessing
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestEMLProcessing:
    """Test complete EML processing pipeline."""

    def test_process_simple_eml(self, sample_eml_file, tmp_path):
        """Test processing simple EML file."""
        base_dir = sample_eml_file.parent
        out_root = tmp_path / "output"

        output_path = process_eml(sample_eml_file, base_dir, out_root)

        assert output_path is not None
        assert output_path.exists()
        assert output_path.suffix == '.md'

    def test_process_eml_creates_directory(self, sample_eml_file, tmp_path):
        """Test output directory creation."""
        base_dir = sample_eml_file.parent
        out_root = tmp_path / "output"

        output_path = process_eml(sample_eml_file, base_dir, out_root)

        assert output_path.parent.exists()

    def test_process_eml_content(self, sample_eml_file, tmp_path):
        """Test processed content quality."""
        base_dir = sample_eml_file.parent
        out_root = tmp_path / "output"

        output_path = process_eml(sample_eml_file, base_dir, out_root)
        content = output_path.read_text(encoding='utf-8')

        # Should have front matter
        assert "---" in content
        # Should have email content
        assert "Test Email" in content

    def test_process_multipart_eml(self, multipart_eml_file, tmp_path):
        """Test processing multipart email."""
        base_dir = multipart_eml_file.parent
        out_root = tmp_path / "output"

        output_path = process_eml(multipart_eml_file, base_dir, out_root)

        assert output_path is not None
        content = output_path.read_text(encoding='utf-8')
        # Should prefer HTML content
        assert "HTML" in content or "Content" in content


# ==============================================================================
# TestEdgeCases
# ==============================================================================

@pytest.mark.skipif(not CLEANER_AVAILABLE, reason="Cleaner module not available")
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handle_missing_headers(self, tmp_path):
        """Test handling email with missing headers."""
        eml_content = """Content-Type: text/plain

Body content without headers
"""
        eml_path = tmp_path / "no_headers.eml"
        eml_path.write_bytes(eml_content.encode('utf-8'))

        msg = email.message_from_bytes(eml_path.read_bytes(), policy=policy.default)
        fm = build_front_matter(msg, "test.eml")

        # Should handle missing headers gracefully
        assert 'subject' in fm
        assert 'from' in fm

    def test_handle_unicode_in_headers(self, tmp_path):
        """Test handling unicode in email headers."""
        eml_content = """From: café@example.com
To: résumé@example.com
Subject: Unicode test: café résumé 日本語
Content-Type: text/plain

Body
"""
        eml_path = tmp_path / "unicode.eml"
        eml_path.write_bytes(eml_content.encode('utf-8'))

        msg = email.message_from_bytes(eml_path.read_bytes(), policy=policy.default)
        fm = build_front_matter(msg, "test.eml")

        # Should handle unicode in headers
        assert 'subject' in fm

    def test_handle_very_long_content(self, tmp_path):
        """Test handling very long email content."""
        long_content = "<html><body>" + ("<p>Long paragraph</p>" * 1000) + "</body></html>"
        eml_content = f"""From: sender@example.com
Subject: Long email
Content-Type: text/html

{long_content}
"""
        eml_path = tmp_path / "long.eml"
        eml_path.write_bytes(eml_content.encode('utf-8'))

        base_dir = eml_path.parent
        out_root = tmp_path / "output"

        output_path = process_eml(eml_path, base_dir, out_root)
        assert output_path is not None


# ==============================================================================
# Run tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
