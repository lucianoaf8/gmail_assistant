"""
Backup manifest with checksums for integrity verification.

Provides SHA-256 checksums for all backup files to detect corruption
or tampering, with support for incremental updates and verification.

Usage:
    manager = ManifestManager(backup_dir)

    # Create initial manifest
    manifest = manager.create_manifest()

    # Verify backup integrity
    results = manager.verify_integrity()
    if results['corrupted']:
        print(f"Corrupted files: {results['corrupted']}")

    # Update manifest with new files
    manager.update_manifest(new_files)
"""

import hashlib
import json
import logging
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FileEntry:
    """Single file entry in manifest."""
    path: str
    size_bytes: int
    sha256: str
    modified_at: str
    gmail_id: str | None = None
    content_type: str | None = None  # eml, markdown, etc.

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'FileEntry':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class BackupManifest:
    """Complete backup manifest."""
    version: str = "1.0"
    created_at: str = ""
    updated_at: str = ""
    backup_directory: str = ""
    total_files: int = 0
    total_size_bytes: int = 0
    files: list[FileEntry] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'backup_directory': self.backup_directory,
            'total_files': self.total_files,
            'total_size_bytes': self.total_size_bytes,
            'files': [f.to_dict() for f in self.files],
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'BackupManifest':
        """Create from dictionary."""
        files = [FileEntry.from_dict(f) for f in data.get('files', [])]
        return cls(
            version=data.get('version', '1.0'),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            backup_directory=data.get('backup_directory', ''),
            total_files=data.get('total_files', 0),
            total_size_bytes=data.get('total_size_bytes', 0),
            files=files,
            metadata=data.get('metadata', {})
        )


@dataclass
class VerificationResult:
    """Result of integrity verification."""
    verified: int = 0
    missing: list[str] = field(default_factory=list)
    corrupted: list[dict[str, str]] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if backup is fully valid."""
        return not self.missing and not self.corrupted

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'verified': self.verified,
            'missing': self.missing,
            'corrupted': self.corrupted,
            'extra': self.extra,
            'errors': self.errors,
            'is_valid': self.is_valid
        }


class ManifestManager:
    """
    Manages backup manifests for integrity verification.

    Features:
    - SHA-256 checksums for all files
    - Incremental manifest updates
    - Verification of backup integrity
    - Missing/corrupted file detection
    - Thread-safe operations

    Example:
        >>> manager = ManifestManager(Path("backups/gmail"))
        >>> manifest = manager.create_manifest()
        >>> print(f"Manifest created: {manifest.total_files} files")
        >>> # Later...
        >>> result = manager.verify_integrity()
        >>> print(f"Verified: {result.verified}, Corrupted: {len(result.corrupted)}")
    """

    MANIFEST_FILENAME = "backup_manifest.json"
    CHUNK_SIZE = 8192  # Bytes to read at a time for hashing

    def __init__(self, backup_dir: Path):
        """
        Initialize manifest manager.

        Args:
            backup_dir: Path to backup directory
        """
        self.backup_dir = Path(backup_dir)
        self.manifest_path = self.backup_dir / self.MANIFEST_FILENAME
        self._lock = threading.Lock()

    def create_manifest(
        self,
        file_patterns: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        progress_callback: Callable[..., Any] | None = None
    ) -> BackupManifest:
        """
        Create new manifest for backup directory.

        Args:
            file_patterns: Glob patterns for files (default: *.eml, *.md)
            metadata: Additional metadata to store
            progress_callback: Optional callback(current, total) for progress

        Returns:
            BackupManifest object
        """
        if file_patterns is None:
            file_patterns = ["**/*.eml", "**/*.md"]

        # Collect all files
        all_files = set()
        for pattern in file_patterns:
            for filepath in self.backup_dir.glob(pattern):
                if filepath.is_file() and filepath.name != self.MANIFEST_FILENAME:
                    all_files.add(filepath)

        files = sorted(all_files)
        total = len(files)

        logger.info(f"Creating manifest for {total} files")

        manifest = BackupManifest(
            backup_directory=str(self.backup_dir),
            metadata=metadata or {}
        )

        for i, filepath in enumerate(files):
            try:
                entry = self._create_file_entry(filepath)
                manifest.files.append(entry)
                manifest.total_size_bytes += entry.size_bytes
            except Exception as e:
                logger.warning(f"Failed to process {filepath}: {e}")

            if progress_callback and (i + 1) % 100 == 0:
                progress_callback(i + 1, total)

        manifest.total_files = len(manifest.files)
        manifest.updated_at = datetime.now().isoformat()

        # Save manifest
        self.save_manifest(manifest)

        logger.info(
            f"Created manifest: {manifest.total_files} files, "
            f"{manifest.total_size_bytes / 1024 / 1024:.1f} MB"
        )

        return manifest

    def _create_file_entry(self, filepath: Path) -> FileEntry:
        """Create manifest entry for a file."""
        stat = filepath.stat()

        # Calculate SHA-256
        sha256_hash = self._calculate_sha256(filepath)

        # Determine content type
        suffix = filepath.suffix.lower()
        content_type = {
            '.eml': 'eml',
            '.md': 'markdown',
            '.txt': 'text',
            '.json': 'json'
        }.get(suffix, 'unknown')

        # Extract gmail_id from filename if present
        gmail_id = self._extract_gmail_id(filepath)

        return FileEntry(
            path=str(filepath.relative_to(self.backup_dir)),
            size_bytes=stat.st_size,
            sha256=sha256_hash,
            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            gmail_id=gmail_id,
            content_type=content_type
        )

    def _calculate_sha256(self, filepath: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _extract_gmail_id(self, filepath: Path) -> str | None:
        """
        Extract gmail_id from filename.

        Assumes format: YYYY-MM-DD_HHMMSS_subject_gmailid.eml
        """
        stem = filepath.stem
        parts = stem.split('_')

        # Gmail IDs are typically 16+ hex characters
        if len(parts) >= 4:
            potential_id = parts[-1]
            if len(potential_id) >= 16 and all(c in '0123456789abcdef' for c in potential_id.lower()):
                return potential_id

        return None

    def save_manifest(self, manifest: BackupManifest) -> None:
        """Save manifest to file atomically."""
        with self._lock:
            # Write to temp file first
            temp_path = self.manifest_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(manifest.to_dict(), f, indent=2)

            # Atomic rename
            temp_path.replace(self.manifest_path)

        logger.debug(f"Saved manifest: {manifest.total_files} files")

    def load_manifest(self) -> BackupManifest | None:
        """Load existing manifest."""
        if not self.manifest_path.exists():
            return None

        try:
            with open(self.manifest_path, encoding='utf-8') as f:
                data = json.load(f)
            return BackupManifest.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return None

    def verify_integrity(
        self,
        progress_callback: Callable[..., Any] | None = None
    ) -> VerificationResult:
        """
        Verify backup integrity against manifest.

        Checks:
        - All manifested files exist
        - All files have matching checksums
        - Reports extra files not in manifest

        Args:
            progress_callback: Optional callback(current, total)

        Returns:
            VerificationResult with verification details
        """
        manifest = self.load_manifest()
        if not manifest:
            return VerificationResult(
                errors=['No manifest found - create one first']
            )

        result = VerificationResult()
        total = len(manifest.files)

        logger.info(f"Verifying {total} files")

        # Verify each file in manifest
        for i, entry in enumerate(manifest.files):
            filepath = self.backup_dir / entry.path

            if not filepath.exists():
                result.missing.append(entry.path)
                continue

            try:
                # Verify checksum
                actual_sha256 = self._calculate_sha256(filepath)

                if actual_sha256 != entry.sha256:
                    result.corrupted.append({
                        'path': entry.path,
                        'expected': entry.sha256,
                        'actual': actual_sha256
                    })
                else:
                    result.verified += 1

            except Exception as e:
                result.errors.append(f"{entry.path}: {e!s}")

            if progress_callback and (i + 1) % 100 == 0:
                progress_callback(i + 1, total)

        # Check for extra files not in manifest
        manifest_paths = {e.path for e in manifest.files}
        for pattern in ["**/*.eml", "**/*.md"]:
            for filepath in self.backup_dir.glob(pattern):
                if filepath.is_file() and filepath.name != self.MANIFEST_FILENAME:
                    rel_path = str(filepath.relative_to(self.backup_dir))
                    if rel_path not in manifest_paths:
                        result.extra.append(rel_path)

        logger.info(
            f"Verification complete: {result.verified} verified, "
            f"{len(result.missing)} missing, {len(result.corrupted)} corrupted"
        )

        return result

    def update_manifest(
        self,
        new_files: list[Path] | None = None
    ) -> BackupManifest:
        """
        Update manifest with new files.

        If new_files is None, scans for files not in manifest.

        Args:
            new_files: List of new file paths to add

        Returns:
            Updated BackupManifest
        """
        manifest = self.load_manifest() or BackupManifest(
            backup_directory=str(self.backup_dir)
        )

        existing_paths = {e.path for e in manifest.files}

        # If no files specified, find new files
        if new_files is None:
            new_files = []
            for pattern in ["**/*.eml", "**/*.md"]:
                for filepath in self.backup_dir.glob(pattern):
                    if filepath.is_file() and filepath.name != self.MANIFEST_FILENAME:
                        rel_path = str(filepath.relative_to(self.backup_dir))
                        if rel_path not in existing_paths:
                            new_files.append(filepath)

        added = 0
        for filepath in new_files:
            filepath = Path(filepath)
            if not filepath.is_absolute():
                filepath = self.backup_dir / filepath

            rel_path = str(filepath.relative_to(self.backup_dir))
            if rel_path not in existing_paths:
                try:
                    entry = self._create_file_entry(filepath)
                    manifest.files.append(entry)
                    manifest.total_size_bytes += entry.size_bytes
                    added += 1
                except Exception as e:
                    logger.warning(f"Failed to add {filepath}: {e}")

        manifest.total_files = len(manifest.files)
        manifest.updated_at = datetime.now().isoformat()
        self.save_manifest(manifest)

        logger.info(f"Updated manifest: added {added} files")

        return manifest

    def get_file_entry(self, relative_path: str) -> FileEntry | None:
        """Get file entry by relative path."""
        manifest = self.load_manifest()
        if not manifest:
            return None

        for entry in manifest.files:
            if entry.path == relative_path:
                return entry

        return None

    def get_stats(self) -> dict[str, Any]:
        """Get manifest statistics."""
        manifest = self.load_manifest()
        if not manifest:
            return {'error': 'No manifest found'}

        # Group by content type
        by_type = {}
        for entry in manifest.files:
            ct = entry.content_type or 'unknown'
            if ct not in by_type:
                by_type[ct] = {'count': 0, 'size_bytes': 0}
            by_type[ct]['count'] += 1
            by_type[ct]['size_bytes'] += entry.size_bytes

        return {
            'version': manifest.version,
            'created_at': manifest.created_at,
            'updated_at': manifest.updated_at,
            'total_files': manifest.total_files,
            'total_size_bytes': manifest.total_size_bytes,
            'total_size_mb': manifest.total_size_bytes / 1024 / 1024,
            'by_content_type': by_type,
            'metadata': manifest.metadata
        }

    def export_file_list(self, output_file: Path) -> int:
        """
        Export list of files to text file.

        Args:
            output_file: Output file path

        Returns:
            Number of files exported
        """
        manifest = self.load_manifest()
        if not manifest:
            return 0

        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in sorted(manifest.files, key=lambda e: e.path):
                f.write(f"{entry.path}\t{entry.sha256}\t{entry.size_bytes}\n")

        return len(manifest.files)

    def find_duplicates(self) -> dict[str, list[str]]:
        """
        Find duplicate files by checksum.

        Returns:
            Dictionary mapping sha256 to list of file paths
        """
        manifest = self.load_manifest()
        if not manifest:
            return {}

        by_hash = {}
        for entry in manifest.files:
            if entry.sha256 not in by_hash:
                by_hash[entry.sha256] = []
            by_hash[entry.sha256].append(entry.path)

        # Return only duplicates
        return {h: paths for h, paths in by_hash.items() if len(paths) > 1}
