#!/usr/bin/env python3
"""
Ultimate Email Processor - Combining Technical Robustness with Content Quality
Fixes YAML serialization WHILE preserving rich content extraction
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import email
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, getaddresses


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SafeMetadataExtractor:
    """Safe metadata extraction with YAML compatibility"""
    
    @staticmethod
    def sanitize_for_yaml(obj: Any) -> Any:
        """Convert any object to YAML-serializable format"""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [SafeMetadataExtractor.sanitize_for_yaml(item) for item in obj]
        elif isinstance(obj, dict):
            return {str(k): SafeMetadataExtractor.sanitize_for_yaml(v) for k, v in obj.items()}
        else:
            return str(obj)
    
    @staticmethod
    def extract_safe_metadata(msg: email.message.Message, source_file: str) -> Dict[str, Any]:
        """Extract metadata with guaranteed YAML compatibility"""
        try:
            # Basic email headers
            subject = (msg.get("Subject") or "").strip()
            from_list = getaddresses(msg.get_all("From", []))
            to_list = getaddresses(msg.get_all("To", []))
            
            # Safe date parsing
            date_iso = None
            date_display = None
            date_hdr = msg.get("Date")
            if date_hdr:
                try:
                    dt_obj = parsedate_to_datetime(date_hdr)
                    date_iso = dt_obj.astimezone().isoformat()
                    date_display = dt_obj.strftime("%a, %d %b %Y %H:%M:%S %z")
                except Exception:
                    date_iso = str(date_hdr)
                    date_display = str(date_hdr)
            
            # Safe Gmail labels extraction - Convert to simple string list
            gmail_labels = []
            for label_header in msg.get_all("X-Gmail-Labels", []):
                if isinstance(label_header, str):
                    labels = [label.strip() for label in label_header.split(',')]
                    gmail_labels.extend(labels)
                else:
                    gmail_labels.append(str(label_header))
            
            # Extract Gmail IDs safely
            gmail_id = ""
            thread_id = ""
            for header_name in ["X-Gmail-Message-Id", "X-GM-MSGID"]:
                if msg.get(header_name):
                    gmail_id = str(msg.get(header_name))
                    break
            for header_name in ["X-Gmail-Thread-Id", "X-GM-THRID"]:
                if msg.get(header_name):
                    thread_id = str(msg.get(header_name))
                    break
            
            # Build safe metadata dictionary
            metadata = {
                "source_file": str(source_file),
                "subject": subject,
                "from": [f"{name} <{addr}>" if name else addr for name, addr in from_list],
                "to": [f"{name} <{addr}>" if name else addr for name, addr in to_list],
                "date": date_iso,
                "date_display": date_display,
                "message_id": str(msg.get("Message-Id") or msg.get("Message-ID") or ""),
                "gmail_id": gmail_id,
                "thread_id": thread_id,
                "labels": gmail_labels,  # Now guaranteed to be string list
                "extraction_timestamp": datetime.now().isoformat(),
                "extraction_method": "safe_metadata_extractor"
            }
            
            # Sanitize everything to ensure YAML compatibility
            return SafeMetadataExtractor.sanitize_for_yaml(metadata)
            
        except Exception as e:
            logger.warning(f"Metadata extraction error: {e}")
            return {
                "source_file": str(source_file),
                "subject": "Extraction Failed",
                "extraction_timestamp": datetime.now().isoformat(),
                "extraction_error": str(e),
                "extraction_method": "safe_metadata_extractor_fallback"
            }

class AdvancedContentExtractor:
    """Advanced content extraction using the working strategies from previous version"""
    
    def __init__(self):
        self.has_advanced_deps = self._check_dependencies()
    
    def _check_dependencies(self) -> bool:
        """Check if advanced processing dependencies are available"""
        try:
            import html2text
            import markdownify
            from bs4 import BeautifulSoup
            return True
        except ImportError:
            logger.warning("Advanced processing dependencies not available")
            return False
    
    def extract_best_content(self, msg: email.message.Message) -> Tuple[str, str, float]:
        """Extract the best content using the proven approach"""
        text_plain = None
        text_html = None
        
        # Extract content parts
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = (part.get("Content-Disposition") or "").lower()
                if "attachment" in disposition:
                    continue
                try:
                    payload = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        payload = payload.decode("utf-8", errors="replace")
                
                if content_type == "text/plain" and text_plain is None:
                    text_plain = str(payload)
                elif content_type == "text/html" and text_html is None:
                    text_html = str(payload)
        else:
            content_type = msg.get_content_type()
            payload = msg.get_content()
            if content_type == "text/plain":
                text_plain = str(payload)
            elif content_type == "text/html":
                text_html = str(payload)
        
        # Process content using advanced parsing if available
        if self.has_advanced_deps and text_html:
            content, quality = self._process_html_content(text_html, text_plain)
        elif text_plain:
            content = text_plain.strip()
            quality = 0.8
        elif text_html:
            # Basic HTML stripping as fallback
            content = re.sub(r'<[^>]+>', '', text_html)
            content = re.sub(r'\s+', ' ', content).strip()
            quality = 0.6
        else:
            content = "No readable content found"
            quality = 0.3
        
        return content, "advanced_extraction" if self.has_advanced_deps else "basic_extraction", quality
    
    def _process_html_content(self, html_content: str, text_plain: str = "") -> Tuple[str, float]:
        """Process HTML content using advanced parser (similar to working version)"""
        try:
            # Import advanced parsing modules
            from gmail_assistant.parsers.advanced_email_parser import EmailContentParser
            
            # Initialize parser
            parser = EmailContentParser()
            
            # Use the advanced parser
            result = parser.parse_email_content(
                html_content=html_content,
                plain_text=text_plain,
                sender="",
                subject=""
            )
            
            if result and result.get("markdown"):
                return result["markdown"], result.get("quality", 0.7)
            else:
                # Fallback to basic processing
                return self._basic_html_processing(html_content), 0.6
                
        except Exception as e:
            logger.warning(f"Advanced HTML processing failed: {e}")
            return self._basic_html_processing(html_content), 0.5
    
    def _basic_html_processing(self, html_content: str) -> str:
        """Basic HTML processing fallback"""
        if not self.has_advanced_deps:
            # Very basic HTML stripping
            content = re.sub(r'<[^>]+>', '', html_content)
            content = re.sub(r'\s+', ' ', content).strip()
            return content
        
        try:
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0
            return h.handle(html_content)
        except Exception:
            content = re.sub(r'<[^>]+>', '', html_content)
            content = re.sub(r'\s+', ' ', content).strip()
            return content

class ProfessionalFormatter:
    """Professional markdown formatting that preserves the table structure"""
    
    @staticmethod
    def create_professional_output(metadata: Dict[str, Any], content: str, 
                                 strategy: str, quality: float) -> str:
        """Create professional markdown output with table structure"""
        
        # Extract key information for table
        from_addr = metadata.get("from", [""])[0] if metadata.get("from") else ""
        to_addr = metadata.get("to", [""])[0] if metadata.get("to") else ""
        subject = metadata.get("subject", "")
        date_display = metadata.get("date_display", metadata.get("date", ""))
        gmail_id = metadata.get("gmail_id", "")
        thread_id = metadata.get("thread_id", "")
        labels = ", ".join(metadata.get("labels", []))
        
        # Create the professional table format (like the working version)
        markdown_content = f"""# Email Details

| Field | Value |
|-------|-------|
| From | {from_addr} |
| To | {to_addr} |
| Date | {date_display} |
| Subject | {subject} |
| Gmail ID | {gmail_id} |
| Thread ID | {thread_id} |
| Labels | {labels} |

## Message Content

{content}
"""
        
        # Add processing metadata to front matter
        processing_metadata = {
            "processing": {
                "strategy_used": strategy,
                "quality_score": round(quality, 3),
                "processor_version": "ultimate_v1.0",
                "processing_timestamp": datetime.now().isoformat(),
                "content_format": "professional_table"
            }
        }
        
        # Combine metadata (excluding display fields from front matter)
        front_matter_metadata = {k: v for k, v in metadata.items() 
                               if k not in ["date_display"]}  # Keep clean front matter
        final_metadata = {**front_matter_metadata, **processing_metadata}
        
        # Generate front matter and content
        try:
            import frontmatter
            post = frontmatter.Post(markdown_content, **final_metadata)
            return frontmatter.dumps(post)
        except ImportError:
            # Fallback to manual YAML generation
            yaml_content = "---\n"
            for key, value in final_metadata.items():
                yaml_content += f"{key}: {value}\n"
            yaml_content += "---\n\n"
            return yaml_content + markdown_content

class UltimateEmailProcessor:
    """Ultimate processor combining technical robustness with content quality"""
    
    def __init__(self):
        self.metadata_extractor = SafeMetadataExtractor()
        self.content_extractor = AdvancedContentExtractor()
        self.formatter = ProfessionalFormatter()
    
    def process_single_email(self, email_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Process email with both technical robustness and content quality"""
        logger.info(f"Processing: {email_path.name}")
        
        start_time = time.time()
        
        try:
            # Load and parse email
            with open(email_path, 'rb') as f:
                raw_data = f.read()
            msg = BytesParser(policy=policy.default).parsebytes(raw_data)
            
            # Extract safe metadata (fixes YAML issues)
            metadata = self.metadata_extractor.extract_safe_metadata(msg, email_path.name)
            
            # Extract high-quality content (preserves content quality)
            content, strategy, quality = self.content_extractor.extract_best_content(msg)
            
            # Create professional output (preserves formatting)
            final_output = self.formatter.create_professional_output(
                metadata, content, strategy, quality
            )
            
            # Save output
            output_path = output_dir / f"{email_path.stem}_ultimate.md"
            output_path.write_text(final_output, encoding='utf-8')
            
            total_time = time.time() - start_time
            
            return {
                "source_file": str(email_path),
                "output_file": str(output_path),
                "strategy_used": strategy,
                "quality_score": quality,
                "processing_time": round(total_time, 3),
                "content_length": len(content),
                "status": "success"
            }
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Failed to process {email_path.name}: {e}")
            
            return {
                "source_file": str(email_path),
                "output_file": None,
                "strategy_used": "failed",
                "quality_score": 0.0,
                "processing_time": round(total_time, 3),
                "content_length": 0,
                "status": "error",
                "error": str(e)
            }

def select_test_files(backup_dir: Path, num_each: int = 3) -> List[Path]:
    """Select test EML files"""
    eml_files = []
    for file_path in backup_dir.rglob("*.eml"):
        if len(eml_files) < num_each:
            eml_files.append(file_path)
        else:
            break
    return eml_files

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Ultimate Email Processor - Technical + Content Quality")
    parser.add_argument("--backup-dir", default="backup_unread", help="Backup directory")
    parser.add_argument("--output-dir", default="ultimate_output", help="Output directory")
    parser.add_argument("--test-mode", action="store_true", help="Test mode (3 EML files only)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    backup_dir = Path(args.backup_dir)
    output_dir = Path(args.output_dir)
    
    if not backup_dir.exists():
        logger.error(f"Backup directory not found: {backup_dir}")
        return 1
    
    output_dir.mkdir(exist_ok=True)
    
    # Initialize processor
    processor = UltimateEmailProcessor()
    
    # Select files
    if args.test_mode:
        all_files = select_test_files(backup_dir, 3)
        logger.info(f"Test mode: Processing {len(all_files)} EML files")
    else:
        all_files = list(backup_dir.rglob("*.eml"))
        logger.info(f"Full processing: {len(all_files)} EML files found")
    
    if not all_files:
        logger.error("No EML files found")
        return 1
    
    # Process files
    results = []
    start_time = time.time()
    
    for i, file_path in enumerate(all_files, 1):
        logger.info(f"Processing {i}/{len(all_files)}: {file_path.name}")
        result = processor.process_single_email(file_path, output_dir)
        results.append(result)
    
    total_time = time.time() - start_time
    
    # Generate summary
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    
    avg_quality = sum(r["quality_score"] for r in successful) / len(successful) if successful else 0
    
    print(f"\n{'='*80}")
    print("ULTIMATE EMAIL PROCESSING RESULTS")
    print(f"{'='*80}")
    print(f"Files Processed: {len(results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    print(f"Average Quality Score: {avg_quality:.3f}")
    print(f"Total Processing Time: {total_time:.1f} seconds")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*80}")
    
    return 0 if len(successful) == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())