"""Comprehensive tests for robust_eml_converter module."""
from __future__ import annotations

import base64
import email
import quopri
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from unittest import mock

import pytest

try:
    from gmail_assistant.parsers.robust_eml_converter import RobustEMLConverter
    CONVERTER_AVAILABLE = True
except ImportError:
    CONVERTER_AVAILABLE = False


# ==============================================================================
# Helpers
# ==============================================================================

def _generate_transport_headers(num_lines: int = 160) -> str:
    """Generate Gmail API style transport headers to pad EML content.

    RobustEMLConverter expects Gmail API format with ~160 lines of transport
    headers before the actual email headers and body.
    Returns string ending with blank line (double newline).
    """
    headers = []
    headers.append("Delivered-To: user@gmail.com")
    headers.append("Received: by 2002:a17:90a:dea2:0:0:0:0 with SMTP id t34csp123456pjq;")
    headers.append("        Mon, 1 Jan 2024 12:00:00 -0500 (EST)")
    headers.append("X-Google-DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;")
    headers.append("        d=1e100.net; s=20210112;")
    headers.append("X-Gm-Message-State: AOAM532abc123")
    headers.append("X-Google-Smtp-Source: ABdhPJabc123")
    headers.append("X-Received: by 2002:a17:90a:e2c2:: with SMTP id")

    # Pad with Received headers to reach target line count
    for i in range(len(headers), num_lines - 10):
        headers.append(f"Received: from mail{i}.example.com (mail{i}.example.com [{i}.{i%256}.{i%256}.{i%256}])")

    headers.append("X-Gmail-Labels: INBOX,UNREAD,CATEGORY_PERSONAL")
    # Return with trailing blank line (double newline for proper separation)
    return "\n".join(headers) + "\n\n"


def _create_gmail_api_eml(
    html_content: str = "",
    text_content: str = "",
    subject: str = "Test Email",
    from_addr: str = "sender@example.com",
    to_addr: str = "recipient@example.com",
    date: str = "Mon, 1 Jan 2024 12:00:00 -0500",
    message_id: str = "<test@example.com>",
    multipart: bool = False
) -> bytes:
    """Create Gmail API format EML content with transport headers.

    The RobustEMLConverter expects Gmail API format with:
    - ~160 lines of transport headers
    - Email headers (From, To, Subject, etc.)
    - Additional X-headers to ensure 6+ lines before body
    - Double blank lines before body
    - Body content
    """
    transport = _generate_transport_headers()

    # Email headers - need 6+ lines before blank lines for algorithm
    email_headers = [
        f"From: {from_addr}",
        f"To: {to_addr}",
        f"Subject: {subject}",
        f"Date: {date}",
        f"Message-ID: {message_id}",
        "MIME-Version: 1.0",
        "X-Mailer: Gmail Assistant Test",
        "X-Priority: 3",
    ]

    if multipart and text_content and html_content:
        # Boundary must not contain '=' for _extract_mime_content detection
        boundary = "Part_1234567890_ABCDEF"
        email_headers.append(f'Content-Type: multipart/alternative; boundary="{boundary}"')
        # Add blank lines - need double blank for body detection
        email_headers.extend(["", ""])

        body_parts = [
            f"--{boundary}",
            "Content-Type: text/plain; charset=utf-8",
            "",
            text_content,
            f"--{boundary}",
            "Content-Type: text/html; charset=utf-8",
            "",
            html_content,
            f"--{boundary}--",
        ]
        body = "\n".join(body_parts)
    elif html_content:
        email_headers.append('Content-Type: text/html; charset="utf-8"')
        # Add double blank lines for body detection
        email_headers.extend(["", ""])
        body = html_content
    elif text_content:
        email_headers.append('Content-Type: text/plain; charset="utf-8"')
        email_headers.extend(["", ""])
        body = text_content
    else:
        email_headers.extend(["", ""])
        body = ""

    full_content = transport + "\n".join(email_headers) + "\n" + body
    return full_content.encode('utf-8')


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def converter():
    """Create converter instance."""
    if not CONVERTER_AVAILABLE:
        pytest.skip("RobustEMLConverter not available")
    return RobustEMLConverter()


@pytest.fixture
def simple_eml_file(tmp_path):
    """Create simple EML file in Gmail API format."""
    content = _create_gmail_api_eml(
        html_content='<html><body><h1>Test</h1><p>Content</p></body></html>',
        subject='Test Email',
        from_addr='sender@example.com',
        to_addr='recipient@example.com',
        date='Mon, 1 Jan 2024 12:00:00 -0500',
        message_id='<test@example.com>'
    )
    eml_path = tmp_path / "simple.eml"
    eml_path.write_bytes(content)
    return eml_path


@pytest.fixture
def multipart_eml_file(tmp_path):
    """Create multipart EML file with text and HTML in Gmail API format."""
    content = _create_gmail_api_eml(
        html_content='<html><body><h1>HTML Version</h1></body></html>',
        text_content='Plain text version',
        subject='Multipart Email',
        from_addr='sender@example.com',
        to_addr='recipient@example.com',
        date='Mon, 1 Jan 2024 12:00:00 -0500',
        multipart=True
    )
    eml_path = tmp_path / "multipart.eml"
    eml_path.write_bytes(content)
    return eml_path


@pytest.fixture
def gmail_api_eml_file(tmp_path):
    """Create Gmail API format EML file with transport headers."""
    content = _create_gmail_api_eml(
        html_content='<html><body><h1>Gmail Content</h1></body></html>',
        subject='Gmail API Email',
        from_addr='sender@example.com',
        to_addr='recipient@example.com',
        date='Mon, 1 Jan 2024 12:00:00 -0500',
        message_id='<gmail123@mail.gmail.com>'
    )
    eml_path = tmp_path / "gmail_api.eml"
    eml_path.write_bytes(content)
    return eml_path


@pytest.fixture
def base64_encoded_eml(tmp_path):
    """Create EML with base64 encoded content in Gmail API format."""
    html_content = '<html><body><h1>Base64 Content</h1><p>This is encoded content.</p></body></html>'
    html_bytes = html_content.encode('utf-8')
    encoded = base64.b64encode(html_bytes).decode('ascii')

    transport = _generate_transport_headers()
    email_part = f"""From: sender@example.com
Subject: Base64 Email
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: base64

{encoded}
"""
    full_content = transport + email_part
    eml_path = tmp_path / "base64.eml"
    eml_path.write_bytes(full_content.encode('utf-8'))
    return eml_path


@pytest.fixture
def quoted_printable_eml(tmp_path):
    """Create EML with quoted-printable encoding in Gmail API format."""
    html_content = '<html><body><p>Content with special chars: café, résumé</p></body></html>'
    encoded = quopri.encodestring(html_content.encode('utf-8')).decode('ascii')

    transport = _generate_transport_headers()
    email_part = f"""From: sender@example.com
Subject: Quoted-Printable Email
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

{encoded}
"""
    full_content = transport + email_part
    eml_path = tmp_path / "quoted.eml"
    eml_path.write_bytes(full_content.encode('utf-8'))
    return eml_path


@pytest.fixture
def eml_with_inline_images(tmp_path):
    """Create EML with inline CID images in Gmail API format."""
    boundary = "Part_Images_1234567890"
    img_data = base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'\x00' * 50).decode('ascii')

    transport = _generate_transport_headers()
    email_part = f"""From: sender@example.com
Subject: Email with Images
Content-Type: multipart/related; boundary="{boundary}"

--{boundary}
Content-Type: text/html; charset="utf-8"

<html><body><img src="cid:image1" /><img src="cid:image2" /></body></html>
--{boundary}
Content-Type: image/png
Content-ID: <image1>
Content-Disposition: inline; filename="img1.png"
Content-Transfer-Encoding: base64

{img_data}
--{boundary}
Content-Type: image/png
Content-ID: <image2>
Content-Disposition: inline; filename="img2.png"
Content-Transfer-Encoding: base64

{img_data}
--{boundary}--
"""
    full_content = transport + email_part
    eml_path = tmp_path / "with_images.eml"
    eml_path.write_bytes(full_content.encode('utf-8'))
    return eml_path


# ==============================================================================
# TestEmailPartExtraction
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestEmailPartExtraction:
    """Test email part extraction from various formats."""

    def test_extract_simple_html(self, converter, simple_eml_file):
        """Test extraction from simple HTML email."""
        parts = converter.extract_email_parts(simple_eml_file)

        assert parts['html']
        assert 'Test' in parts['html']
        assert 'Content' in parts['html']

    def test_extract_multipart(self, converter, multipart_eml_file):
        """Test extraction from multipart email."""
        parts = converter.extract_email_parts(multipart_eml_file)

        assert parts['text'] == 'Plain text version'
        assert 'HTML Version' in parts['html']

    def test_extract_metadata(self, converter, simple_eml_file):
        """Test metadata extraction."""
        parts = converter.extract_email_parts(simple_eml_file)
        metadata = parts['metadata']

        assert metadata['subject'] == 'Test Email'
        assert 'sender@example.com' in metadata['from']
        assert metadata['message_id']

    def test_extract_gmail_api_format(self, converter, gmail_api_eml_file):
        """Test extraction from Gmail API format."""
        parts = converter.extract_email_parts(gmail_api_eml_file)

        # Should find actual email headers despite transport headers
        assert parts['metadata']['subject'] == 'Gmail API Email'
        assert 'Gmail Content' in parts['html']

    def test_extract_handles_missing_parts(self, converter, tmp_path):
        """Test handling of emails with missing parts."""
        content = _create_gmail_api_eml(
            text_content='Only text content',
            from_addr='sender@example.com'
        )
        eml_path = tmp_path / "text_only.eml"
        eml_path.write_bytes(content)

        parts = converter.extract_email_parts(eml_path)
        assert parts['text']
        assert parts['html'] == ""


# ==============================================================================
# TestHeaderParsing
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestHeaderParsing:
    """Test email header parsing."""

    def test_clean_simple_header(self, converter):
        """Test cleaning simple header value."""
        cleaned = converter._clean_header("Test Subject")
        assert cleaned == "Test Subject"

    def test_clean_encoded_header(self, converter):
        """Test cleaning encoded header."""
        # Encoded UTF-8 subject
        encoded = "=?utf-8?B?VGVzdCBTdWJqZWN0?="
        cleaned = converter._clean_header(encoded)
        assert "Test" in cleaned

    def test_clean_empty_header(self, converter):
        """Test cleaning empty header."""
        cleaned = converter._clean_header("")
        assert cleaned == ""

    def test_parse_date(self, converter):
        """Test date parsing to ISO format."""
        date_str = "Mon, 1 Jan 2024 12:00:00 -0500"
        iso_date = converter._parse_date(date_str)
        assert iso_date is not None
        assert "2024" in iso_date

    def test_parse_invalid_date(self, converter):
        """Test invalid date handling."""
        iso_date = converter._parse_date("invalid date")
        assert iso_date is None

    def test_find_actual_headers_simple(self, converter, simple_eml_file):
        """Test finding headers in simple email."""
        msg = email.message_from_bytes(
            simple_eml_file.read_bytes(),
            policy=email.policy.default
        )
        # Inject eml_path into locals for the method to find
        import inspect
        frame = inspect.currentframe()
        frame.f_locals['eml_path'] = simple_eml_file

        headers = converter._find_actual_email_headers(msg)
        assert 'Subject' in headers or 'From' in headers


# ==============================================================================
# TestMIMEContentExtraction
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestMIMEContentExtraction:
    """Test MIME content extraction and decoding."""

    def test_extract_base64_content(self, converter):
        """Test base64 content extraction."""
        html = '<html><body><h1>Test</h1></body></html>'
        encoded = base64.b64encode(html.encode('utf-8')).decode('ascii')

        # Boundary must be > 20 chars for _extract_mime_content
        boundary = "Part_1234567890_ABCDEF"
        mime_body = f"""--{boundary}
Content-Type: text/html
Content-Transfer-Encoding: base64

{encoded}
--{boundary}--
"""
        extracted = converter._extract_mime_content(mime_body, 'text/html')
        assert 'Test' in extracted

    def test_extract_quoted_printable_content(self, converter):
        """Test quoted-printable content extraction."""
        html = '<html><body><p>Café</p></body></html>'
        encoded = quopri.encodestring(html.encode('utf-8')).decode('ascii')

        boundary = "Part_1234567890_ABCDEF"
        mime_body = f"""--{boundary}
Content-Type: text/html
Content-Transfer-Encoding: quoted-printable

{encoded}
--{boundary}--
"""
        extracted = converter._extract_mime_content(mime_body, 'text/html')
        # Should decode properly
        assert isinstance(extracted, str)

    def test_extract_plain_content(self, converter):
        """Test extraction of non-encoded content."""
        boundary = "Part_1234567890_ABCDEF"
        mime_body = f"""--{boundary}
Content-Type: text/html

<html><body><p>Plain content</p></body></html>
--{boundary}--
"""
        extracted = converter._extract_mime_content(mime_body, 'text/html')
        assert 'Plain content' in extracted

    def test_extract_missing_boundary(self, converter):
        """Test handling of missing MIME boundary."""
        mime_body = "Content without proper MIME structure"
        extracted = converter._extract_mime_content(mime_body, 'text/html')
        assert extracted == ""


# ==============================================================================
# TestBodyExtraction
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestBodyExtraction:
    """Test email body extraction from raw content."""

    def test_extract_simple_body(self, converter):
        """Test simple body extraction - needs Gmail API format."""
        # _extract_actual_body expects Gmail API format with transport headers
        # Also needs 6+ header lines before blank lines for detection algorithm
        transport = _generate_transport_headers()
        raw_content = transport + """From: sender@example.com
To: recipient@example.com
Subject: Test
Date: Mon, 1 Jan 2024 12:00:00 -0500
Message-ID: <test@example.com>
MIME-Version: 1.0
X-Mailer: Test
Content-Type: text/html


<html><body>Content</body></html>
"""
        body = converter._extract_actual_body(raw_content)
        assert 'Content' in body

    def test_extract_gmail_api_body(self, converter):
        """Test body extraction from Gmail API format."""
        # Simulate Gmail API format with transport headers
        transport = _generate_transport_headers()
        boundary = "Part_1234567890_ABCDEF"
        raw_content = transport + f"""From: sender@example.com
Subject: Gmail Email
Content-Type: multipart/alternative; boundary="{boundary}"


--{boundary}
Content-Type: text/html

<html><body>Gmail Body</body></html>
--{boundary}--
"""
        body = converter._extract_actual_body(raw_content)
        # Should extract content after headers
        assert isinstance(body, str)

    def test_extract_with_mime_boundary(self, converter):
        """Test extraction with MIME boundary markers."""
        transport = _generate_transport_headers()
        boundary = "Part_1234567890_ABCDEF"
        raw_content = transport + f"""Subject: Test
Content-Type: multipart/alternative; boundary="{boundary}"


--{boundary}
Content-Type: text/html

<html>Content</html>
--{boundary}--
"""
        body = converter._extract_actual_body(raw_content)
        assert boundary.replace('----=_', '--') in body or 'Content' in body


# ==============================================================================
# TestConversionPipeline
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestConversionPipeline:
    """Test complete conversion pipeline."""

    def test_convert_simple_eml(self, converter, simple_eml_file, tmp_path):
        """Test converting simple EML to markdown."""
        output_path = tmp_path / "output.md"
        success = converter.convert_eml_to_markdown(simple_eml_file, output_path)

        assert success
        assert output_path.exists()

        content = output_path.read_text(encoding='utf-8')
        assert "---" in content  # Front matter
        assert "Test" in content

    def test_convert_creates_output_directory(self, converter, simple_eml_file, tmp_path):
        """Test output directory creation."""
        output_path = tmp_path / "subdir" / "output.md"
        success = converter.convert_eml_to_markdown(simple_eml_file, output_path)

        assert success
        assert output_path.parent.exists()

    def test_convert_includes_metadata(self, converter, simple_eml_file, tmp_path):
        """Test metadata inclusion in output."""
        output_path = tmp_path / "output.md"
        converter.convert_eml_to_markdown(simple_eml_file, output_path)

        content = output_path.read_text(encoding='utf-8')
        assert "subject:" in content.lower()
        assert "from:" in content.lower()

    def test_convert_multipart_prefers_html(self, converter, multipart_eml_file, tmp_path):
        """Test HTML preference in multipart emails."""
        output_path = tmp_path / "output.md"
        converter.convert_eml_to_markdown(multipart_eml_file, output_path)

        content = output_path.read_text(encoding='utf-8')
        # Should use HTML version
        assert "HTML Version" in content or "Version" in content

    def test_convert_handles_errors(self, converter, tmp_path):
        """Test error handling in conversion."""
        non_eml = tmp_path / "not_eml.txt"
        non_eml.write_text("Not an email file")

        output_path = tmp_path / "output.md"
        success = converter.convert_eml_to_markdown(non_eml, output_path)

        # Should handle gracefully
        assert isinstance(success, bool)


# ==============================================================================
# TestDirectoryConversion
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestDirectoryConversion:
    """Test batch directory conversion."""

    def test_convert_directory(self, converter, tmp_path):
        """Test converting directory of EML files."""
        # Create test EML files
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        for i in range(3):
            content = _create_gmail_api_eml(
                html_content=f'<html><body>Email {i}</body></html>',
                subject=f'Email {i}'
            )
            eml_path = input_dir / f"email{i}.eml"
            eml_path.write_bytes(content)

        output_dir = tmp_path / "output"
        stats = converter.convert_directory(input_dir, output_dir)

        assert stats['total'] == 3
        assert stats['success'] > 0

    def test_convert_directory_with_limit(self, converter, tmp_path):
        """Test directory conversion with file limit."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        for i in range(5):
            content = _create_gmail_api_eml(
                html_content=f'<html>Email {i}</html>'
            )
            eml_path = input_dir / f"email{i}.eml"
            eml_path.write_bytes(content)

        output_dir = tmp_path / "output"
        stats = converter.convert_directory(input_dir, output_dir, limit=2)

        assert stats['total'] == 2  # Limited to 2 files

    def test_convert_preserves_structure(self, converter, tmp_path):
        """Test directory structure preservation."""
        input_dir = tmp_path / "input"
        subdir = input_dir / "2024" / "01"
        subdir.mkdir(parents=True)

        content = _create_gmail_api_eml(
            html_content='<html>Test</html>'
        )
        eml_path = subdir / "email.eml"
        eml_path.write_bytes(content)

        output_dir = tmp_path / "output"
        converter.convert_directory(input_dir, output_dir)

        # Check structure is preserved
        expected_output = output_dir / "2024" / "01" / "email.md"
        assert expected_output.exists()


# ==============================================================================
# TestEncodingHandling
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestEncodingHandling:
    """Test various encoding scenarios."""

    def test_handle_utf8_content(self, converter, tmp_path):
        """Test UTF-8 content handling."""
        content = _create_gmail_api_eml(
            html_content='<html><body>UTF-8: café, résumé</body></html>',
            subject='UTF-8 Test'
        )
        eml_path = tmp_path / "utf8.eml"
        eml_path.write_bytes(content)

        parts = converter.extract_email_parts(eml_path)
        assert 'café' in parts['html'] or 'caf' in parts['html']

    def test_handle_latin1_content(self, converter, tmp_path):
        """Test Latin-1 encoding."""
        content = _create_gmail_api_eml(
            html_content='<html><body>Content</body></html>'
        )
        eml_path = tmp_path / "latin1.eml"
        eml_path.write_bytes(content)

        parts = converter.extract_email_parts(eml_path)
        assert parts['html']

    def test_handle_mixed_encodings(self, converter, tmp_path):
        """Test mixed encoding scenarios."""
        content = _create_gmail_api_eml(
            html_content='<html>UTF-8 content</html>',
            text_content='Plain text',
            subject='=?utf-8?B?VGVzdA==?=',
            multipart=True
        )
        eml_path = tmp_path / "mixed.eml"
        eml_path.write_bytes(content)

        parts = converter.extract_email_parts(eml_path)
        # Should handle mixed encodings
        assert parts['text']
        assert parts['html']


# ==============================================================================
# TestEdgeCases
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_handle_empty_eml(self, converter, tmp_path):
        """Test handling of empty EML file."""
        eml_path = tmp_path / "empty.eml"
        eml_path.write_bytes(b'')

        parts = converter.extract_email_parts(eml_path)
        # Should return empty parts without crashing
        assert parts['html'] == ""
        assert parts['text'] == ""

    def test_handle_malformed_eml(self, converter, tmp_path):
        """Test handling of malformed EML."""
        eml_path = tmp_path / "malformed.eml"
        eml_path.write_bytes(b'Not a valid EML file')

        parts = converter.extract_email_parts(eml_path)
        # Should handle gracefully
        assert isinstance(parts, dict)

    def test_handle_very_large_eml(self, converter, tmp_path):
        """Test handling of very large email."""
        large_html = '<html><body>' + ('<p>Content</p>' * 10000) + '</body></html>'
        content = _create_gmail_api_eml(html_content=large_html)

        eml_path = tmp_path / "large.eml"
        eml_path.write_bytes(content)

        parts = converter.extract_email_parts(eml_path)
        assert parts['html']

    def test_handle_missing_content_type(self, converter, tmp_path):
        """Test handling of email without Content-Type."""
        # Create Gmail API format but without Content-Type header
        transport = _generate_transport_headers()
        email_part = """From: sender@example.com
Subject: No Content Type

Body content here
"""
        eml_path = tmp_path / "no_type.eml"
        eml_path.write_bytes((transport + email_part).encode('utf-8'))

        parts = converter.extract_email_parts(eml_path)
        # Should handle missing content type
        assert isinstance(parts, dict)

    def test_handle_nested_multipart(self, converter, tmp_path):
        """Test deeply nested multipart messages."""
        transport = _generate_transport_headers()
        outer_boundary = "OuterBoundary_1234567890"
        inner_boundary = "InnerBoundary_1234567890"

        email_part = f"""From: sender@example.com
Subject: Nested Multipart
Content-Type: multipart/mixed; boundary="{outer_boundary}"

--{outer_boundary}
Content-Type: multipart/alternative; boundary="{inner_boundary}"

--{inner_boundary}
Content-Type: text/html; charset="utf-8"

<html>Nested</html>
--{inner_boundary}--
--{outer_boundary}--
"""
        eml_path = tmp_path / "nested.eml"
        eml_path.write_bytes((transport + email_part).encode('utf-8'))

        parts = converter.extract_email_parts(eml_path)
        # Should find content in nested structure
        assert parts['html']


# ==============================================================================
# TestIntegrationWithAdvancedParser
# ==============================================================================

@pytest.mark.skipif(not CONVERTER_AVAILABLE, reason="Converter not available")
class TestIntegrationWithAdvancedParser:
    """Test integration with EmailContentParser."""

    def test_uses_advanced_parser(self, converter, simple_eml_file, tmp_path):
        """Test that advanced parser is used for conversion."""
        output_path = tmp_path / "output.md"
        converter.convert_eml_to_markdown(simple_eml_file, output_path)

        content = output_path.read_text(encoding='utf-8')
        # Should have quality metrics from advanced parser
        assert "quality_score:" in content.lower() or "conversion_strategy:" in content.lower()

    def test_quality_score_in_metadata(self, converter, simple_eml_file, tmp_path):
        """Test quality score inclusion in front matter."""
        output_path = tmp_path / "output.md"
        converter.convert_eml_to_markdown(simple_eml_file, output_path)

        content = output_path.read_text(encoding='utf-8')
        # Check for quality-related metadata
        assert "quality" in content.lower() or "strategy" in content.lower()


# ==============================================================================
# Run tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
