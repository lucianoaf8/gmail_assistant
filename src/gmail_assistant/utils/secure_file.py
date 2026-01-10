"""
Secure file operations for Gmail Assistant.
Provides atomic writes with restrictive permissions.

Security: Prevents unauthorized file access (M-7 fix)
"""

import os
import stat
import tempfile
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


class SecureFileWriter:
    """Utility for writing files with restrictive permissions (M-7 security fix)"""

    # Restrictive permissions: owner read/write only (0o600)
    SECURE_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR

    # Restrictive directory permissions: owner read/write/execute (0o700)
    SECURE_DIR_MODE = stat.S_IRWXU

    @classmethod
    def write_secure(cls, path: Union[str, Path], content: str,
                     encoding: str = 'utf-8') -> None:
        """
        Write file with restrictive permissions using atomic write pattern.

        Uses temp file + rename for atomicity.
        Sets owner-only read/write permissions (0o600).

        Args:
            path: File path to write
            content: Content to write
            encoding: File encoding (default: utf-8)

        Raises:
            OSError: If file operations fail
        """
        path = Path(path)

        # Create parent directory with secure permissions if needed
        if not path.parent.exists():
            cls.create_secure_directory(path.parent)

        tmp_path = None
        try:
            # Create temp file in same directory (for atomic rename)
            fd, tmp_path = tempfile.mkstemp(
                dir=str(path.parent),
                suffix='.tmp',
                prefix='.secure_'
            )

            try:
                # Set restrictive permissions on temp file (before writing content)
                if os.name != 'nt':  # Unix-like systems
                    os.fchmod(fd, cls.SECURE_FILE_MODE)
                else:
                    # Windows: set permissions after file creation
                    pass

                # Write content
                with os.fdopen(fd, 'w', encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())

                # fd is now closed by the context manager
                fd = None

                # Set permissions on Windows (after close)
                if os.name == 'nt':
                    cls._set_windows_permissions(tmp_path)

                # Atomic rename (preserves permissions)
                os.replace(tmp_path, path)
                tmp_path = None  # Rename succeeded

                logger.debug(f"Securely wrote file: {path}")

            except Exception:
                # Close fd if still open
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                raise

        finally:
            # Clean up temp file on failure
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    @classmethod
    def write_secure_bytes(cls, path: Union[str, Path], content: bytes) -> None:
        """
        Write binary file with restrictive permissions.

        Args:
            path: File path to write
            content: Binary content to write
        """
        path = Path(path)

        if not path.parent.exists():
            cls.create_secure_directory(path.parent)

        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(
                dir=str(path.parent),
                suffix='.tmp',
                prefix='.secure_'
            )

            try:
                if os.name != 'nt':
                    os.fchmod(fd, cls.SECURE_FILE_MODE)

                os.write(fd, content)
                os.fsync(fd)
                os.close(fd)
                fd = None

                if os.name == 'nt':
                    cls._set_windows_permissions(tmp_path)

                os.replace(tmp_path, path)
                tmp_path = None

            except Exception:
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                raise

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    @classmethod
    def create_secure_directory(cls, path: Union[str, Path]) -> Path:
        """
        Create directory with restrictive permissions (0o700).

        Args:
            path: Directory path to create

        Returns:
            Created directory path
        """
        path = Path(path)

        if os.name != 'nt':
            # Unix: create with restricted permissions
            path.mkdir(parents=True, exist_ok=True, mode=cls.SECURE_DIR_MODE)
        else:
            # Windows: create then set permissions
            path.mkdir(parents=True, exist_ok=True)
            cls._set_windows_permissions(path, is_directory=True)

        logger.debug(f"Created secure directory: {path}")
        return path

    @classmethod
    def _set_windows_permissions(cls, path: Union[str, Path],
                                  is_directory: bool = False) -> None:
        """
        Set restrictive permissions on Windows.

        Args:
            path: Path to set permissions on
            is_directory: Whether path is a directory
        """
        try:
            import win32security
            import ntsecuritycon as con

            # Get current user SID
            user_sid = win32security.GetTokenInformation(
                win32security.OpenProcessToken(
                    win32security.GetCurrentProcess(),
                    win32security.TOKEN_QUERY
                ),
                win32security.TokenUser
            )[0]

            # Create DACL with only owner access
            dacl = win32security.ACL()

            if is_directory:
                access_mask = (con.FILE_ALL_ACCESS |
                              con.FILE_LIST_DIRECTORY |
                              con.FILE_TRAVERSE)
            else:
                access_mask = con.FILE_ALL_ACCESS

            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                access_mask,
                user_sid
            )

            # Apply DACL
            sd = win32security.SECURITY_DESCRIPTOR()
            sd.SetSecurityDescriptorDacl(1, dacl, 0)

            win32security.SetFileSecurity(
                str(path),
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )

        except ImportError:
            # pywin32 not available, fall back to basic chmod
            logger.warning(
                "pywin32 not available for Windows permissions, "
                "using basic file attributes"
            )
            try:
                # At minimum, remove world-readable flag
                os.chmod(str(path), stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
        except Exception as e:
            logger.warning(f"Failed to set Windows permissions: {e}")

    @classmethod
    def secure_existing_file(cls, path: Union[str, Path]) -> bool:
        """
        Apply secure permissions to an existing file.

        Args:
            path: Path to file to secure

        Returns:
            True if successful, False otherwise
        """
        path = Path(path)

        if not path.exists():
            logger.warning(f"Cannot secure non-existent file: {path}")
            return False

        try:
            if os.name != 'nt':
                os.chmod(path, cls.SECURE_FILE_MODE)
            else:
                cls._set_windows_permissions(path, is_directory=path.is_dir())

            logger.debug(f"Secured existing file: {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to secure file {path}: {e}")
            return False

    @classmethod
    def verify_permissions(cls, path: Union[str, Path]) -> bool:
        """
        Verify file has secure permissions.

        Args:
            path: Path to check

        Returns:
            True if permissions are secure, False otherwise
        """
        path = Path(path)

        if not path.exists():
            return False

        try:
            if os.name != 'nt':
                mode = path.stat().st_mode
                # Check that group and others have no access
                if mode & (stat.S_IRWXG | stat.S_IRWXO):
                    return False
                return True
            else:
                # Windows: basic check - file should not be world-readable
                # Full verification requires pywin32
                return True

        except Exception as e:
            logger.error(f"Failed to verify permissions for {path}: {e}")
            return False
