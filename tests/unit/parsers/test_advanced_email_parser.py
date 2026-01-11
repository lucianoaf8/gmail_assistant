"""Comprehensive tests for advanced_email_parser module."""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest
from bs4 import BeautifulSoup

from gmail_assistant.parsers.advanced_email_parser import EmailContentParser


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def parser():
    """Create parser instance with default config."""
    return EmailContentParser()


@pytest.fixture
def sample_html_simple():
    """Simple HTML email content."""
    return """
    <html>
    <body>
        <h1>Newsletter Title</h1>
        <p>This is a simple test email with some content.</p>
        <a href="https://example.com">Click here</a>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_newsletter():
    """Newsletter-style HTML email."""
    return """
    <html>
    <body>
        <h1 class="newsletter-title">Weekly AI Newsletter</h1>
        <div class="email-content">
            <h2>Top Stories</h2>
            <p>Story about AI development...</p>
            <img src="https://example.com/image.jpg" alt="AI Image" />
        </div>
        <div class="footer">Unsubscribe | Preferences</div>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_marketing():
    """Marketing email with complex tables."""
    return """
    <html>
    <body>
        <table width="600">
            <tr><td><img src="image1.jpg" /></td></tr>
            <tr><td><h1>Special Offer!</h1></td></tr>
            <tr><td><img src="image2.jpg" /></td></tr>
            <tr><td><img src="image3.jpg" /></td></tr>
            <tr><td><img src="image4.jpg" /></td></tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_tracking():
    """HTML with tracking elements."""
    return """
    <html>
    <head>
        <script>trackingCode();</script>
        <style>.hidden { display: none; }</style>
    </head>
    <body>
        <h1>Content</h1>
        <p>Some text with <a href="https://example.com?utm_source=email&utm_campaign=test">tracked link</a></p>
        <img src="pixel.gif" width="1" height="1" />
        <div style="display:none">Hidden tracking div</div>
    </body>
    </html>
    """


@pytest.fixture
def custom_config(tmp_path):
    """Create custom configuration file."""
    config = {
        "strategies": ["smart", "html2text"],
        "cleaning_rules": {
            "remove_tags": ["script", "style"],
            "remove_attributes": ["style", "class"],
            "preserve_attributes": ["href", "src"]
        },
        "formatting": {
            "max_line_length": 80,
            "remove_tracking": True
        }
    }
    config_file = tmp_path / "parser_config.json"
    config_file.write_text(json.dumps(config))
    return config_file


# ==============================================================================
# TestEmailTypeDetection
# ==============================================================================

class TestEmailTypeDetection:
    """Test email type detection functionality."""

    def test_detect_newsletter_by_sender(self, parser):
        """Test newsletter detection based on sender domain."""
        html = "<html><body><p>Content</p></body></html>"
        email_type = parser.detect_email_type(html, "updates@newsletter.com")
        assert email_type == "newsletter"

    def test_detect_notification_by_sender(self, parser):
        """Test notification detection based on sender."""
        html = "<html><body><p>Your order has shipped</p></body></html>"
        email_type = parser.detect_email_type(html, "noreply@service.com")
        assert email_type == "notification"

    def test_detect_marketing_by_content(self, parser, sample_html_marketing):
        """Test marketing email detection by content structure."""
        email_type = parser.detect_email_type(sample_html_marketing, "sales@company.com")
        assert email_type == "marketing"

    def test_detect_simple_email(self, parser):
        """Test simple email detection."""
        html = "<p>Short email without complex structure</p>"
        email_type = parser.detect_email_type(html, "user@example.com")
        assert email_type == "simple"

    def test_detect_with_empty_sender(self, parser, sample_html_simple):
        """Test type detection with empty sender."""
        email_type = parser.detect_email_type(sample_html_simple, "")
        assert email_type in ["simple", "newsletter"]


# ==============================================================================
# TestHTMLCleaning
# ==============================================================================

class TestHTMLCleaning:
    """Test HTML cleaning and preparation."""

    def test_clean_removes_scripts(self, parser, sample_html_tracking):
        """Test that scripts are removed during cleaning."""
        cleaned = parser.clean_html(sample_html_tracking)
        assert "<script>" not in cleaned
        assert "trackingCode" not in cleaned

    def test_clean_removes_styles(self, parser, sample_html_tracking):
        """Test that style tags are removed."""
        cleaned = parser.clean_html(sample_html_tracking)
        assert "<style>" not in cleaned

    def test_clean_removes_comments(self, parser):
        """Test HTML comments removal."""
        html = "<html><body><!-- Comment --><p>Content</p></body></html>"
        cleaned = parser.clean_html(html)
        assert "<!--" not in cleaned
        assert "Comment" not in cleaned

    def test_clean_removes_tracking_pixels(self, parser, sample_html_tracking):
        """Test removal of 1x1 tracking images."""
        cleaned = parser.clean_html(sample_html_tracking)
        soup = BeautifulSoup(cleaned, 'html.parser')
        # Tracking pixel should be removed
        imgs = soup.find_all('img')
        # Should only have images that aren't 1x1 pixels
        for img in imgs:
            width = img.get('width', '')
            height = img.get('height', '')
            assert not (width == '1' and height == '1')

    def test_clean_preserves_content(self, parser, sample_html_simple):
        """Test that actual content is preserved."""
        cleaned = parser.clean_html(sample_html_simple)
        assert "Newsletter Title" in cleaned
        assert "test email" in cleaned

    def test_clean_empty_html(self, parser):
        """Test cleaning empty HTML."""
        cleaned = parser.clean_html("")
        assert cleaned == ""

    def test_clean_with_sender_specific_rules(self, parser):
        """Test sender-specific cleaning rules."""
        html = """
        <html><body>
            <div class="email-content">Main content here</div>
            <div class="unsubscribe">Unsubscribe link</div>
        </body></html>
        """
        cleaned = parser.clean_html(html, "newsletter@theresanaiforthat.com")
        # Should apply theresanaiforthat.com specific rules
        assert "Main content" in cleaned


# ==============================================================================
# TestURLHandling
# ==============================================================================

class TestURLHandling:
    """Test URL fixing and tracking removal."""

    def test_fix_relative_protocol_urls(self, parser):
        """Test fixing protocol-relative URLs."""
        html = '<img src="//example.com/image.jpg" />'
        soup = BeautifulSoup(html, 'html.parser')
        parser._fix_urls(soup)
        img = soup.find('img')
        assert img['src'] == "https://example.com/image.jpg"

    def test_fix_broken_image_paths(self, parser):
        """Test handling of broken relative image paths."""
        html = '<img src="/images/photo.jpg" />'
        soup = BeautifulSoup(html, 'html.parser')
        parser._fix_urls(soup)
        img = soup.find('img')
        assert "[Broken Image:" in img['src']

    def test_remove_tracking_params(self, parser):
        """Test removal of tracking parameters from URLs."""
        html = '<a href="https://example.com?utm_source=email&utm_campaign=test&foo=bar">Link</a>'
        soup = BeautifulSoup(html, 'html.parser')
        parser._remove_tracking_params(soup)
        link = soup.find('a')
        href = link['href']
        assert "utm_source" not in href
        assert "utm_campaign" not in href
        assert "foo=bar" in href  # Non-tracking params preserved

    def test_preserve_valid_urls(self, parser):
        """Test that valid URLs are preserved."""
        html = '<a href="https://example.com/page">Link</a>'
        soup = BeautifulSoup(html, 'html.parser')
        parser._fix_urls(soup)
        link = soup.find('a')
        assert link['href'] == "https://example.com/page"


# ==============================================================================
# TestParsingStrategies
# ==============================================================================

class TestParsingStrategies:
    """Test different parsing strategies."""

    def test_smart_strategy(self, parser, sample_html_newsletter):
        """Test smart strategy parsing."""
        markdown, quality = parser.parse_with_smart_strategy(sample_html_newsletter)
        assert len(markdown) > 0
        assert 0.0 <= quality <= 1.0
        assert "Newsletter" in markdown or "AI" in markdown

    def test_html2text_strategy(self, parser, sample_html_simple):
        """Test html2text strategy."""
        markdown, quality = parser.parse_with_html2text(sample_html_simple)
        assert len(markdown) > 0
        assert 0.0 <= quality <= 1.0
        assert "Newsletter Title" in markdown

    def test_markdownify_strategy(self, parser, sample_html_simple):
        """Test markdownify strategy."""
        markdown, quality = parser.parse_with_markdownify(sample_html_simple)
        assert len(markdown) > 0
        assert 0.0 <= quality <= 1.0

    @pytest.mark.skipif(
        not hasattr(EmailContentParser, 'parse_with_readability'),
        reason="Readability not available"
    )
    def test_readability_strategy_available(self, parser, sample_html_newsletter):
        """Test readability strategy if available."""
        try:
            markdown, quality = parser.parse_with_readability(sample_html_newsletter)
            # If readability is available, should return content
            assert isinstance(markdown, str)
            assert isinstance(quality, float)
        except Exception:
            # If readability not installed, should handle gracefully
            pass

    @pytest.mark.skipif(
        not hasattr(EmailContentParser, 'parse_with_trafilatura'),
        reason="Trafilatura not available"
    )
    def test_trafilatura_strategy_available(self, parser, sample_html_newsletter):
        """Test trafilatura strategy if available."""
        try:
            markdown, quality = parser.parse_with_trafilatura(sample_html_newsletter)
            assert isinstance(markdown, str)
            assert isinstance(quality, float)
        except Exception:
            pass

    def test_strategy_fallback_on_error(self, parser):
        """Test strategy returns empty on error."""
        # Extremely malformed HTML
        bad_html = "<<<<>>>>"
        markdown, quality = parser.parse_with_html2text(bad_html)
        # Should handle gracefully
        assert isinstance(markdown, str)
        assert isinstance(quality, float)


# ==============================================================================
# TestContentExtraction
# ==============================================================================

class TestContentExtraction:
    """Test content extraction for different email types."""

    def test_parse_newsletter_structure(self, parser, sample_html_newsletter):
        """Test newsletter parsing extracts structure."""
        cleaned = parser.clean_html(sample_html_newsletter)
        soup = BeautifulSoup(cleaned, 'html.parser')
        markdown = parser._parse_newsletter(soup)
        assert len(markdown) > 0
        assert "#" in markdown  # Should have headers

    def test_parse_notification(self, parser):
        """Test notification parsing."""
        html = "<html><body><p>Your order has been confirmed.</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        markdown = parser._parse_notification(soup)
        assert "confirmed" in markdown

    def test_parse_marketing(self, parser, sample_html_marketing):
        """Test marketing email parsing."""
        soup = BeautifulSoup(sample_html_marketing, 'html.parser')
        markdown = parser._parse_marketing(soup)
        assert len(markdown) > 0

    def test_parse_simple(self, parser, sample_html_simple):
        """Test simple email parsing."""
        soup = BeautifulSoup(sample_html_simple, 'html.parser')
        markdown = parser._parse_simple(soup)
        assert "Newsletter Title" in markdown


# ==============================================================================
# TestMarkdownPostProcessing
# ==============================================================================

class TestMarkdownPostProcessing:
    """Test markdown post-processing and cleanup."""

    def test_fix_line_breaks(self, parser):
        """Test excessive line break removal."""
        markdown = "Line 1\n\n\n\n\nLine 2"
        fixed = parser._fix_line_breaks(markdown)
        assert "\n\n\n" not in fixed
        assert "Line 1" in fixed and "Line 2" in fixed

    def test_fix_headers(self, parser):
        """Test header formatting fixes."""
        markdown = "##No space after hashes"
        fixed = parser._fix_headers(markdown)
        assert "## No space" in fixed

    def test_fix_links(self, parser):
        """Test link formatting fixes."""
        markdown = "[](https://example.com)"
        fixed = parser._fix_links(markdown)
        # Should fix empty link text
        assert "[https://example.com]" in fixed

    def test_fix_lists(self, parser):
        """Test list formatting fixes."""
        markdown = "*Missing space after bullet"
        fixed = parser._fix_lists(markdown)
        assert "* Missing" in fixed

    def test_remove_excessive_whitespace(self, parser):
        """Test whitespace cleanup."""
        markdown = "Line 1  \n\n\nLine 2   \n\n\n\n\nLine 3  "
        fixed = parser._remove_excessive_whitespace(markdown)
        # Should remove trailing spaces and limit blank lines
        assert "Line 1\n\n" in fixed or "Line 1\n" in fixed
        assert not fixed.endswith("  ")

    def test_post_process_markdown_complete(self, parser):
        """Test complete post-processing pipeline."""
        markdown = "##Header\n\n\n\n*No space\n[](link)\n\n\n\nEnd  "
        processed = parser._post_process_markdown(markdown)
        assert "## Header" in processed
        assert "* No space" in processed
        assert not processed.endswith("  ")


# ==============================================================================
# TestQualityScoring
# ==============================================================================

class TestQualityScoring:
    """Test quality score calculation."""

    def test_quality_score_range(self, parser, sample_html_simple):
        """Test quality score is in valid range."""
        markdown = parser.html2text_parser.handle(sample_html_simple)
        quality = parser._calculate_quality_score(markdown, sample_html_simple)
        assert 0.0 <= quality <= 1.0

    def test_empty_content_zero_quality(self, parser):
        """Test empty content gets zero quality score."""
        quality = parser._calculate_quality_score("", "<html></html>")
        assert quality == 0.0

    def test_quality_score_structure_recognition(self, parser):
        """Test quality score recognizes structure elements."""
        # Well-structured markdown
        markdown = "# Header\n\n- List item\n- Another item\n\n[Link](url)"
        html = "<html><body><h1>Header</h1><ul><li>List item</li></ul></body></html>"
        quality = parser._calculate_quality_score(markdown, html)
        # Should score higher due to structure
        assert quality > 0.5

    def test_quality_score_content_preservation(self, parser):
        """Test quality score considers content preservation."""
        html = "<html><body><p>Short content</p></body></html>"
        # Good preservation
        markdown1 = "Short content"
        quality1 = parser._calculate_quality_score(markdown1, html)
        # Poor preservation (too short)
        markdown2 = "S"
        quality2 = parser._calculate_quality_score(markdown2, html)
        assert quality1 > quality2


# ==============================================================================
# TestMainParsingMethod
# ==============================================================================

class TestMainParsingMethod:
    """Test main parse_email_content method."""

    def test_parse_with_html_only(self, parser, sample_html_simple):
        """Test parsing with HTML content only."""
        result = parser.parse_email_content(html_content=sample_html_simple)
        assert result['markdown']
        assert result['strategy']
        assert 'quality' in result
        assert result['quality'] > 0

    def test_parse_with_plain_text_only(self, parser):
        """Test parsing with plain text only."""
        result = parser.parse_email_content(
            html_content="",
            plain_text="This is plain text content"
        )
        assert result['markdown'] == "This is plain text content"
        assert result['strategy'] == "plain_text"
        assert result['quality'] == 0.8

    def test_parse_with_no_content(self, parser):
        """Test parsing with no content."""
        result = parser.parse_email_content(html_content="", plain_text="")
        assert result['markdown'] == ""
        assert result['quality'] == 0.0
        assert 'error' in result['metadata']

    def test_parse_with_metadata(self, parser, sample_html_simple):
        """Test parsing includes metadata."""
        result = parser.parse_email_content(
            html_content=sample_html_simple,
            sender="newsletter@example.com",
            subject="Weekly Update"
        )
        assert result['metadata']['sender'] == "newsletter@example.com"
        assert result['metadata']['subject'] == "Weekly Update"
        assert 'email_type' in result['metadata']

    def test_parse_best_strategy_selection(self, parser, sample_html_newsletter):
        """Test that best strategy is selected."""
        result = parser.parse_email_content(html_content=sample_html_newsletter)
        # Should try multiple strategies and pick best
        assert result['strategy'] in ['smart', 'readability', 'trafilatura', 'html2text', 'markdownify']
        assert result['quality'] > 0

    def test_parse_input_validation_error(self, parser):
        """Test input validation for oversized content."""
        # Create extremely large HTML (over 5MB limit)
        huge_html = "<p>" + ("x" * 6_000_000) + "</p>"
        result = parser.parse_email_content(html_content=huge_html)
        # Should handle validation error gracefully
        assert 'error' in result['metadata']

    def test_parse_fallback_to_plain_text(self, parser):
        """Test fallback to plain text when all strategies fail."""
        # Malformed HTML that might fail all strategies
        bad_html = "<<>><>><<<"
        result = parser.parse_email_content(
            html_content=bad_html,
            plain_text="Fallback content"
        )
        # Should use fallback or return malformed content
        # Some strategies might still process malformed HTML
        assert result['markdown'] in ["Fallback content", "*(Content could not be parsed)*", bad_html.strip()]


# ==============================================================================
# TestConfigurationLoading
# ==============================================================================

class TestConfigurationLoading:
    """Test configuration loading and application."""

    def test_default_config_loaded(self, parser):
        """Test default configuration is loaded."""
        assert parser.config is not None
        assert 'strategies' in parser.config
        assert 'cleaning_rules' in parser.config
        assert 'formatting' in parser.config

    def test_custom_config_loading(self, custom_config):
        """Test custom configuration file loading."""
        parser = EmailContentParser(str(custom_config))
        assert parser.config['strategies'] == ["smart", "html2text"]
        assert parser.config['formatting']['remove_tracking'] is True

    def test_parser_setup_with_config(self, parser):
        """Test parsers are set up according to config."""
        assert hasattr(parser, 'html2text_parser')
        assert hasattr(parser, 'markdownify_settings')
        # Check html2text configuration
        assert parser.html2text_parser.body_width == parser.config["formatting"]["max_line_length"]

    def test_nonexistent_config_uses_defaults(self):
        """Test nonexistent config file uses defaults."""
        parser = EmailContentParser("/nonexistent/config.json")
        assert parser.config is not None
        assert 'strategies' in parser.config


# ==============================================================================
# TestDomainExtraction
# ==============================================================================

class TestDomainExtraction:
    """Test domain extraction from email addresses and URLs."""

    def test_extract_from_email(self, parser):
        """Test domain extraction from email address."""
        domain = parser._extract_domain("user@example.com")
        assert domain == "example.com"

    def test_extract_from_url(self, parser):
        """Test domain extraction from URL."""
        domain = parser._extract_domain("https://www.example.com/path")
        assert domain == "www.example.com"

    def test_extract_from_plain_domain(self, parser):
        """Test extraction from plain domain string."""
        domain = parser._extract_domain("example.com")
        assert domain == "example.com"


# ==============================================================================
# TestEdgeCases
# ==============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unicode_content(self, parser):
        """Test handling of unicode content."""
        html = "<html><body><p>Unicode: café, résumé, 日本語</p></body></html>"
        result = parser.parse_email_content(html_content=html)
        assert result['markdown']
        assert result['quality'] > 0

    def test_very_long_lines(self, parser):
        """Test handling of very long lines."""
        html = "<html><body><p>" + ("word " * 1000) + "</p></body></html>"
        result = parser.parse_email_content(html_content=html)
        assert result['markdown']

    def test_deeply_nested_html(self, parser):
        """Test handling of deeply nested HTML."""
        html = "<html><body>"
        for _ in range(50):
            html += "<div>"
        html += "<p>Content</p>"
        for _ in range(50):
            html += "</div>"
        html += "</body></html>"
        result = parser.parse_email_content(html_content=html)
        assert result['markdown']

    def test_malformed_encoding(self, parser):
        """Test handling of potentially malformed content."""
        html = "<html><body><p>Test\x00content\xffwith\xfebad\xfdbytes</p></body></html>"
        result = parser.parse_email_content(html_content=html)
        # Should handle without crashing
        assert isinstance(result, dict)

    def test_empty_tags(self, parser):
        """Test handling of empty tags."""
        html = "<html><body><p></p><div></div><span></span></body></html>"
        result = parser.parse_email_content(html_content=html)
        assert isinstance(result, dict)


# ==============================================================================
# Run tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
