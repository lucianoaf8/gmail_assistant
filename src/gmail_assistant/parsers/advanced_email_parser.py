#!/usr/bin/env python3
"""
Advanced Email Content Parser
Intelligently converts email HTML to clean, readable markdown with multiple strategies
"""

import re
import html
import json
import logging
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
from pathlib import Path
import sys
import os

# Local imports
from gmail_assistant.utils.input_validator import InputValidator, ValidationError

# Core dependencies
from bs4 import BeautifulSoup, Comment
import html2text
import markdownify

# Optional dependencies for enhanced parsing
try:
    from readability import Document
    HAS_READABILITY = True
except ImportError:
    HAS_READABILITY = False

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailContentParser:
    """
    Advanced email content parser with multiple strategies for clean markdown output
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.validator = InputValidator()
        self.setup_parsers()
        
    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load parser configuration"""
        default_config = {
            "strategies": ["smart", "readability", "trafilatura", "html2text", "markdownify"],
            "newsletter_patterns": {
                "theresanaiforthat.com": {
                    "content_selectors": [".email-content", "#main-content", ".newsletter-body"],
                    "remove_selectors": [".unsubscribe", ".footer", ".header", ".social-links"],
                    "title_selector": "h1, .subject-line, .newsletter-title"
                },
                "mindstream.news": {
                    "content_selectors": [".email-body", ".content"],
                    "remove_selectors": [".footer", ".unsubscribe-link"],
                    "preserve_images": True
                },
                "futurepedia.io": {
                    "content_selectors": [".newsletter-content", ".main-content"],
                    "remove_selectors": [".sponsor", ".advertisement"]
                }
            },
            "cleaning_rules": {
                "remove_tags": ["script", "style", "meta", "link", "noscript"],
                "remove_attributes": ["style", "class", "id", "onclick", "onload"],
                "preserve_attributes": ["href", "src", "alt", "title"],
                "max_image_width": 800,
                "convert_tables": True,
                "preserve_code_blocks": True
            },
            "formatting": {
                "max_line_length": 80,
                "preserve_whitespace": False,
                "add_section_breaks": True,
                "clean_links": True,
                "remove_tracking": True
            }
        }
        
        if config_file and Path(config_file).exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def setup_parsers(self):
        """Initialize different parsing strategies"""
        # HTML2Text with optimized settings
        self.html2text_parser = html2text.HTML2Text()
        self.html2text_parser.ignore_links = False
        self.html2text_parser.ignore_images = False
        self.html2text_parser.ignore_tables = False
        self.html2text_parser.body_width = self.config["formatting"]["max_line_length"]
        self.html2text_parser.unicode_snob = True
        self.html2text_parser.bypass_tables = False
        self.html2text_parser.default_image_alt = "[Image]"
        
        # Markdownify with custom settings
        self.markdownify_settings = {
            'heading_style': 'ATX',
            'bullets': '-',
            'strong_style': '**',
            'emphasis_style': '*',
            'link_style': 'INLINE',
            'convert': ['b', 'strong', 'i', 'em', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                       'p', 'br', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'table', 'thead', 
                       'tbody', 'tr', 'td', 'th', 'div', 'span']
        }
    
    def detect_email_type(self, html_content: str, sender: str = "") -> str:
        """Detect the type of email for targeted parsing"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Newsletter patterns
        if any(domain in sender.lower() for domain in ["newsletter", "digest", "update"]):
            return "newsletter"
        
        # Service notifications
        if any(domain in sender.lower() for domain in ["noreply", "no-reply", "notification", "support"]):
            return "notification"
        
        # Marketing emails
        if soup.find(['table']) and len(soup.find_all('img')) > 3:
            return "marketing"
        
        # Simple text emails
        if not soup.find(['table', 'div']) or len(html_content) < 1000:
            return "simple"
        
        # Default to newsletter for complex HTML
        return "newsletter"
    
    def clean_html(self, html_content: str, sender: str = "") -> str:
        """Clean and prepare HTML for conversion"""
        if not html_content.strip():
            return ""
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted tags
        for tag_name in self.config["cleaning_rules"]["remove_tags"]:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Apply sender-specific cleaning rules
        sender_domain = self._extract_domain(sender)
        if sender_domain in self.config["newsletter_patterns"]:
            rules = self.config["newsletter_patterns"][sender_domain]
            
            # Remove unwanted sections
            for selector in rules.get("remove_selectors", []):
                for element in soup.select(selector):
                    element.decompose()
            
            # Focus on main content if selectors are defined
            content_selectors = rules.get("content_selectors", [])
            if content_selectors:
                main_content = None
                for selector in content_selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                if main_content:
                    soup = BeautifulSoup(str(main_content), 'html.parser')
        
        # Clean attributes
        for tag in soup.find_all():
            # Remove unwanted attributes
            attrs_to_remove = []
            for attr in tag.attrs:
                if attr not in self.config["cleaning_rules"]["preserve_attributes"]:
                    attrs_to_remove.append(attr)
            
            for attr in attrs_to_remove:
                del tag[attr]
        
        # Fix broken links and images
        self._fix_urls(soup)
        
        # Clean up tracking parameters
        if self.config["formatting"]["remove_tracking"]:
            self._remove_tracking_params(soup)
        
        return str(soup)
    
    def _extract_domain(self, email_or_url: str) -> str:
        """Extract domain from email address or URL"""
        if '@' in email_or_url:
            return email_or_url.split('@')[-1].lower()
        elif 'http' in email_or_url:
            return urlparse(email_or_url).netloc.lower()
        return email_or_url.lower()
    
    def _fix_urls(self, soup: BeautifulSoup):
        """Fix relative URLs and broken links"""
        # Fix image sources
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith(('http', 'data:')):
                # Try to fix relative URLs
                if src.startswith('//'):
                    img['src'] = 'https:' + src
                elif src.startswith('/'):
                    # Can't fix without base URL, mark as broken
                    img['src'] = f"[Broken Image: {src}]"
        
        # Fix links
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href and not href.startswith(('http', 'mailto:', '#')):
                if href.startswith('//'):
                    link['href'] = 'https:' + href
    
    def _remove_tracking_params(self, soup: BeautifulSoup):
        """Remove tracking parameters from URLs"""
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'source', 'medium', 'campaign', 'ref', 'referrer', 'track', 'tracking'
        ]
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href and '?' in href:
                try:
                    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                    parsed = urlparse(href)
                    query_params = parse_qs(parsed.query)
                    
                    # Remove tracking parameters
                    cleaned_params = {k: v for k, v in query_params.items() 
                                    if not any(track in k.lower() for track in tracking_params)}
                    
                    # Rebuild URL
                    if cleaned_params:
                        new_query = urlencode(cleaned_params, doseq=True)
                        new_parsed = parsed._replace(query=new_query)
                    else:
                        new_parsed = parsed._replace(query='')
                    
                    link['href'] = urlunparse(new_parsed)
                except Exception as e:
                    # Keep original URL if parsing fails, log for debugging
                    logging.debug(f"URL parsing failed for link, keeping original: {e}")
    
    def parse_with_smart_strategy(self, html_content: str, sender: str = "") -> Tuple[str, float]:
        """Smart parsing strategy that adapts to content type"""
        try:
            email_type = self.detect_email_type(html_content, sender)
            cleaned_html = self.clean_html(html_content, sender)
            
            if not cleaned_html.strip():
                return "", 0.0
            
            soup = BeautifulSoup(cleaned_html, 'html.parser')
            
            # Extract main content based on email type
            if email_type == "newsletter":
                markdown = self._parse_newsletter(soup)
            elif email_type == "notification":
                markdown = self._parse_notification(soup)
            elif email_type == "marketing":
                markdown = self._parse_marketing(soup)
            else:
                markdown = self._parse_simple(soup)
            
            # Post-process markdown
            markdown = self._post_process_markdown(markdown)
            
            # Calculate quality score
            quality = self._calculate_quality_score(markdown, html_content)
            
            return markdown, quality
            
        except Exception as e:
            logger.error(f"Smart strategy failed: {e}")
            return "", 0.0
    
    def _parse_newsletter(self, soup: BeautifulSoup) -> str:
        """Parse newsletter-style emails"""
        parts = []
        
        # Extract title
        title = soup.find(['h1', 'h2']) or soup.find(class_=re.compile(r'title|subject|header'))
        if title:
            parts.append(f"# {title.get_text().strip()}\n")
        
        # Extract sections
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            # Skip if it's too small or seems like metadata
            text = section.get_text().strip()
            if len(text) < 50:
                continue
            
            # Look for section headers
            header = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if header:
                level = int(header.name[1])
                parts.append(f"\n{'#' * level} {header.get_text().strip()}\n")
            
            # Convert content
            section_html = str(section)
            section_md = self.html2text_parser.handle(section_html)
            parts.append(section_md)
        
        return "\n".join(parts)
    
    def _parse_notification(self, soup: BeautifulSoup) -> str:
        """Parse service notification emails"""
        # These are usually simpler, focus on main message
        main_content = soup.find('body') or soup
        
        # Remove headers and footers
        for element in main_content.find_all(['header', 'footer']):
            element.decompose()
        
        return self.html2text_parser.handle(str(main_content))
    
    def _parse_marketing(self, soup: BeautifulSoup) -> str:
        """Parse marketing emails with complex layouts"""
        # Try to extract text content while preserving structure
        return markdownify.markdownify(str(soup), **self.markdownify_settings)
    
    def _parse_simple(self, soup: BeautifulSoup) -> str:
        """Parse simple text emails"""
        return self.html2text_parser.handle(str(soup))
    
    def parse_with_readability(self, html_content: str) -> Tuple[str, float]:
        """Parse using readability for content extraction"""
        if not HAS_READABILITY:
            return "", 0.0
        
        try:
            doc = Document(html_content)
            clean_html = doc.summary()
            
            # Convert to markdown
            markdown = self.html2text_parser.handle(clean_html)
            markdown = self._post_process_markdown(markdown)
            
            quality = self._calculate_quality_score(markdown, html_content)
            return markdown, quality
            
        except Exception as e:
            logger.error(f"Readability strategy failed: {e}")
            return "", 0.0
    
    def parse_with_trafilatura(self, html_content: str) -> Tuple[str, float]:
        """Parse using trafilatura for content extraction"""
        if not HAS_TRAFILATURA:
            return "", 0.0
        
        try:
            text = trafilatura.extract(html_content, output_format='markdown')
            if text:
                markdown = self._post_process_markdown(text)
                quality = self._calculate_quality_score(markdown, html_content)
                return markdown, quality
            
        except Exception as e:
            logger.error(f"Trafilatura strategy failed: {e}")
        
        return "", 0.0
    
    def parse_with_html2text(self, html_content: str) -> Tuple[str, float]:
        """Parse using html2text library"""
        try:
            cleaned_html = self.clean_html(html_content)
            markdown = self.html2text_parser.handle(cleaned_html)
            markdown = self._post_process_markdown(markdown)
            
            quality = self._calculate_quality_score(markdown, html_content)
            return markdown, quality
            
        except Exception as e:
            logger.error(f"HTML2Text strategy failed: {e}")
            return "", 0.0
    
    def parse_with_markdownify(self, html_content: str) -> Tuple[str, float]:
        """Parse using markdownify library"""
        try:
            cleaned_html = self.clean_html(html_content)
            markdown = markdownify.markdownify(cleaned_html, **self.markdownify_settings)
            markdown = self._post_process_markdown(markdown)
            
            quality = self._calculate_quality_score(markdown, html_content)
            return markdown, quality
            
        except Exception as e:
            logger.error(f"Markdownify strategy failed: {e}")
            return "", 0.0
    
    def _post_process_markdown(self, markdown: str) -> str:
        """Clean up and improve markdown output"""
        if not markdown:
            return ""
        
        # Fix common issues
        markdown = self._fix_line_breaks(markdown)
        markdown = self._fix_headers(markdown)
        markdown = self._fix_links(markdown)
        markdown = self._fix_lists(markdown)
        markdown = self._fix_tables(markdown)
        markdown = self._remove_excessive_whitespace(markdown)
        
        return markdown.strip()
    
    def _fix_line_breaks(self, markdown: str) -> str:
        """Fix excessive line breaks and spacing"""
        # Remove excessive newlines (more than 2)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Fix Windows line endings
        markdown = markdown.replace('\r\n', '\n')
        
        return markdown
    
    def _fix_headers(self, markdown: str) -> str:
        """Fix header formatting"""
        lines = markdown.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix headers with missing spaces
            if re.match(r'^#{1,6}[^#\s]', line):
                match = re.match(r'^(#{1,6})(.+)', line)
                if match:
                    hashes, content = match.groups()
                    line = f"{hashes} {content.strip()}"
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_links(self, markdown: str) -> str:
        """Fix link formatting"""
        # Fix broken markdown links
        markdown = re.sub(r'\[\s*\]\(([^)]+)\)', r'[\1](\1)', markdown)
        
        # Fix links with no text
        markdown = re.sub(r'\[\]\(([^)]+)\)', r'[\1](\1)', markdown)
        
        return markdown
    
    def _fix_lists(self, markdown: str) -> str:
        """Fix list formatting"""
        lines = markdown.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix lists without proper spacing
            if re.match(r'^[\*\-\+]\S', line):
                line = re.sub(r'^([\*\-\+])(\S)', r'\1 \2', line)
            elif re.match(r'^\d+\.\S', line):
                line = re.sub(r'^(\d+\.)(\S)', r'\1 \2', line)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_tables(self, markdown: str) -> str:
        """Fix table formatting"""
        # This is complex - for now, just ensure proper spacing
        lines = markdown.split('\n')
        in_table = False
        fixed_lines = []
        
        for line in lines:
            if '|' in line and not in_table:
                in_table = True
                # Add empty line before table
                if fixed_lines and fixed_lines[-1].strip():
                    fixed_lines.append('')
            elif in_table and '|' not in line.strip():
                in_table = False
                # Add empty line after table
                fixed_lines.append(line)
                if line.strip():
                    fixed_lines.append('')
                continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _remove_excessive_whitespace(self, markdown: str) -> str:
        """Remove excessive whitespace while preserving structure"""
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in markdown.split('\n')]
        
        # Remove excessive empty lines
        cleaned_lines = []
        empty_count = 0
        
        for line in lines:
            if not line.strip():
                empty_count += 1
                if empty_count <= 2:  # Allow max 2 consecutive empty lines
                    cleaned_lines.append(line)
            else:
                empty_count = 0
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _calculate_quality_score(self, markdown: str, original_html: str) -> float:
        """Calculate quality score for the parsed markdown"""
        if not markdown.strip():
            return 0.0
        
        score = 0.0
        
        # Content preservation (40% of score)
        html_text = BeautifulSoup(original_html, 'html.parser').get_text()
        if html_text.strip():
            content_ratio = len(markdown.strip()) / len(html_text.strip())
            score += min(content_ratio, 1.0) * 0.4
        
        # Structure quality (30% of score)
        has_headers = bool(re.search(r'^#{1,6}\s', markdown, re.MULTILINE))
        has_lists = bool(re.search(r'^[\*\-\+\d+\.]\s', markdown, re.MULTILINE))
        has_links = bool(re.search(r'\[.+\]\(.+\)', markdown))
        
        structure_score = sum([has_headers, has_lists, has_links]) / 3
        score += structure_score * 0.3
        
        # Readability (20% of score)
        lines = markdown.split('\n')
        readable_lines = [line for line in lines if len(line.strip()) > 0]
        if readable_lines:
            avg_line_length = sum(len(line) for line in readable_lines) / len(readable_lines)
            readability_score = 1.0 if 20 <= avg_line_length <= 120 else 0.5
            score += readability_score * 0.2
        
        # Formatting quality (10% of score)
        has_proper_spacing = not bool(re.search(r'\n{4,}', markdown))
        has_proper_headers = not bool(re.search(r'^#{1,6}[^#\s]', markdown, re.MULTILINE))
        
        formatting_score = sum([has_proper_spacing, has_proper_headers]) / 2
        score += formatting_score * 0.1
        
        return min(score, 1.0)
    
    def parse_email_content(self, html_content: str, plain_text: str = "",
                          sender: str = "", subject: str = "") -> Dict[str, Union[str, float]]:
        """
        Main parsing method that tries multiple strategies and returns the best result
        """
        try:
            # Validate inputs
            if html_content:
                html_content = self.validator.validate_string(html_content, max_length=5000000)  # 5MB limit
            if plain_text:
                plain_text = self.validator.validate_string(plain_text, max_length=1000000)  # 1MB limit
            if sender:
                sender = self.validator.validate_string(sender, max_length=500)
            if subject:
                subject = self.validator.validate_string(subject, max_length=1000)
        except ValidationError as e:
            logger.error(f"Input validation failed: {e}")
            return {
                "markdown": "",
                "strategy": "none",
                "quality": 0.0,
                "metadata": {"error": f"Input validation failed: {e}"}
            }

        if not html_content and not plain_text:
            return {
                "markdown": "",
                "strategy": "none",
                "quality": 0.0,
                "metadata": {"error": "No content provided"}
            }
        
        # If only plain text is available, return it formatted
        if plain_text and not html_content:
            return {
                "markdown": plain_text,
                "strategy": "plain_text",
                "quality": 0.8,
                "metadata": {"type": "plain_text"}
            }
        
        results = []
        
        # Try each strategy
        for strategy in self.config["strategies"]:
            logger.info(f"Trying strategy: {strategy}")
            
            if strategy == "smart":
                markdown, quality = self.parse_with_smart_strategy(html_content, sender)
            elif strategy == "readability":
                markdown, quality = self.parse_with_readability(html_content)
            elif strategy == "trafilatura":
                markdown, quality = self.parse_with_trafilatura(html_content)
            elif strategy == "html2text":
                markdown, quality = self.parse_with_html2text(html_content)
            elif strategy == "markdownify":
                markdown, quality = self.parse_with_markdownify(html_content)
            else:
                continue
            
            if markdown and quality > 0:
                results.append({
                    "markdown": markdown,
                    "strategy": strategy,
                    "quality": quality,
                    "length": len(markdown)
                })
        
        # Choose best result
        if not results:
            # Fallback to plain text if available
            if plain_text:
                return {
                    "markdown": plain_text,
                    "strategy": "fallback_plain",
                    "quality": 0.6,
                    "metadata": {"type": "fallback"}
                }
            else:
                return {
                    "markdown": "*(Content could not be parsed)*",
                    "strategy": "failed",
                    "quality": 0.0,
                    "metadata": {"error": "All parsing strategies failed"}
                }
        
        # Sort by quality score and return best
        best_result = max(results, key=lambda x: x["quality"])
        
        # Add metadata
        best_result["metadata"] = {
            "email_type": self.detect_email_type(html_content, sender),
            "sender": sender,
            "subject": subject,
            "strategies_tried": len(results),
            "alternative_results": len(results) - 1
        }
        
        logger.info(f"Best strategy: {best_result['strategy']} (quality: {best_result['quality']:.2f})")
        
        return best_result

def main():
    """Test the parser with sample content"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python advanced_parser.py <html_file>")
        return
    
    parser = EmailContentParser()
    
    # Read test file
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse content
    result = parser.parse_email_content(html_content)
    
    # Print results
    print(f"Strategy: {result['strategy']}")
    print(f"Quality: {result['quality']:.2f}")
    print(f"Length: {len(result['markdown'])} characters")
    print("\n" + "="*50)
    print(result['markdown'])

if __name__ == "__main__":
    main()
