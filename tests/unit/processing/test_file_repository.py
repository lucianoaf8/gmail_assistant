"""Unit tests for FileEmailRepository (C-2 fix)."""

import json
import pytest
import tempfile
from pathlib import Path

from gman.core.processing.file_repository import FileEmailRepository
from gman.core.exceptions import ValidationError


class TestFileEmailRepository:
    """Test suite for FileEmailRepository implementation."""

    @pytest.fixture
    def temp_repo_path(self, tmp_path):
        """Create a temporary directory for repository."""
        return tmp_path / "email_storage"

    @pytest.fixture
    def repo(self, temp_repo_path):
        """Create a FileEmailRepository instance."""
        return FileEmailRepository(temp_repo_path)

    @pytest.fixture
    def sample_email(self):
        """Sample email data for testing."""
        return {
            'id': 'test_email_123',
            'subject': 'Test Subject',
            'sender': 'test@example.com',
            'date': '2025-03-15',
            'body': 'This is a test email body.',
            'snippet': 'Test snippet...',
        }

    def test_init_creates_directory(self, temp_repo_path):
        """Test that initialization creates the base directory."""
        assert not temp_repo_path.exists()
        FileEmailRepository(temp_repo_path)
        assert temp_repo_path.exists()

    def test_init_no_create_dirs(self, temp_repo_path):
        """Test initialization without creating directories at init time."""
        # With create_dirs=False, base directory is not auto-created at init
        repo = FileEmailRepository(temp_repo_path, create_dirs=False)
        # Base path doesn't exist initially
        assert not temp_repo_path.exists()
        # But save() creates necessary directories on demand
        result = repo.save({'id': 'test', 'date': '2025-01-01'})
        assert result is True
        assert repo.exists('test')

    def test_save_email(self, repo, sample_email):
        """Test saving an email."""
        result = repo.save(sample_email)
        assert result is True
        assert repo.exists('test_email_123')

    def test_save_email_without_id_raises(self, repo):
        """Test that saving email without 'id' raises ValidationError."""
        with pytest.raises(ValidationError, match="must have 'id' field"):
            repo.save({'subject': 'No ID email'})

    def test_get_email(self, repo, sample_email):
        """Test retrieving an email."""
        repo.save(sample_email)
        retrieved = repo.get('test_email_123')
        assert retrieved is not None
        assert retrieved['id'] == 'test_email_123'
        assert retrieved['subject'] == 'Test Subject'
        assert retrieved['sender'] == 'test@example.com'

    def test_get_nonexistent_email(self, repo):
        """Test retrieving a non-existent email returns None."""
        result = repo.get('nonexistent_id')
        assert result is None

    def test_exists(self, repo, sample_email):
        """Test exists method."""
        assert not repo.exists('test_email_123')
        repo.save(sample_email)
        assert repo.exists('test_email_123')

    def test_delete_email(self, repo, sample_email):
        """Test deleting an email."""
        repo.save(sample_email)
        assert repo.exists('test_email_123')

        result = repo.delete('test_email_123')
        assert result is True
        assert not repo.exists('test_email_123')

    def test_delete_nonexistent_email(self, repo):
        """Test deleting a non-existent email returns False."""
        result = repo.delete('nonexistent_id')
        assert result is False

    def test_count_all(self, repo, sample_email):
        """Test counting all emails."""
        assert repo.count() == 0

        repo.save(sample_email)
        assert repo.count() == 1

        repo.save({'id': 'email_2', 'subject': 'Second', 'date': '2025-03-16'})
        assert repo.count() == 2

    def test_find_by_query(self, repo):
        """Test finding emails by query."""
        repo.save({'id': '1', 'subject': 'Python Newsletter', 'sender': 'news@python.org', 'date': '2025-03-15'})
        repo.save({'id': '2', 'subject': 'JavaScript Update', 'sender': 'news@js.org', 'date': '2025-03-15'})
        repo.save({'id': '3', 'subject': 'Python Tips', 'sender': 'tips@python.org', 'date': '2025-03-15'})

        results = repo.find('Python')
        assert len(results) == 2

        results = repo.find('JavaScript')
        assert len(results) == 1
        assert results[0]['id'] == '2'

    def test_find_with_limit(self, repo):
        """Test finding emails with limit."""
        for i in range(10):
            repo.save({'id': f'email_{i}', 'subject': f'Test {i}', 'date': '2025-03-15'})

        results = repo.find('Test', limit=5)
        assert len(results) == 5

    def test_count_with_query(self, repo):
        """Test counting emails with query filter."""
        repo.save({'id': '1', 'subject': 'Python Newsletter', 'date': '2025-03-15'})
        repo.save({'id': '2', 'subject': 'JavaScript Update', 'date': '2025-03-15'})
        repo.save({'id': '3', 'subject': 'Python Tips', 'date': '2025-03-15'})

        assert repo.count('Python') == 2
        assert repo.count('JavaScript') == 1
        assert repo.count('Ruby') == 0

    def test_clear_repository(self, repo):
        """Test clearing all emails from repository."""
        for i in range(5):
            repo.save({'id': f'email_{i}', 'subject': f'Test {i}', 'date': '2025-03-15'})

        assert repo.count() == 5
        deleted = repo.clear()
        assert deleted == 5
        assert repo.count() == 0

    def test_get_stats(self, repo, sample_email):
        """Test getting repository statistics."""
        stats = repo.get_stats()
        assert stats['email_count'] == 0
        assert stats['total_size_bytes'] == 0

        repo.save(sample_email)
        stats = repo.get_stats()
        assert stats['email_count'] == 1
        assert stats['total_size_bytes'] > 0

    def test_refresh_index(self, repo, sample_email):
        """Test refreshing the index after external changes."""
        repo.save(sample_email)

        # Manually clear cache to simulate external changes
        repo._index_cache.clear()
        assert repo.count() == 0  # Cache is empty

        count = repo.refresh_index()
        assert count == 1
        assert repo.exists('test_email_123')

    def test_date_based_organization(self, repo):
        """Test that emails are organized by date."""
        email = {
            'id': 'dated_email',
            'subject': 'Dated Email',
            'date': '2025-03-15T10:30:00',
        }
        repo.save(email)

        # Check that the file is in a date-organized path
        expected_path = repo.base_path / '2025' / '03'
        assert expected_path.exists()

    def test_special_characters_in_id(self, repo):
        """Test handling of special characters in email ID."""
        email = {
            'id': 'email/with:special*chars<>|"?',
            'subject': 'Special ID',
            'date': '2025-03-15',
        }
        result = repo.save(email)
        assert result is True

        retrieved = repo.get('email/with:special*chars<>|"?')
        assert retrieved is not None
        assert retrieved['subject'] == 'Special ID'

    def test_unicode_content(self, repo):
        """Test handling of unicode content."""
        email = {
            'id': 'unicode_email',
            'subject': '日本語メール 🎉',
            'body': 'Unicode content: 你好世界',
            'date': '2025-03-15',
        }
        repo.save(email)

        retrieved = repo.get('unicode_email')
        assert retrieved['subject'] == '日本語メール 🎉'
        assert retrieved['body'] == 'Unicode content: 你好世界'


class TestFileEmailRepositoryEdgeCases:
    """Edge case tests for FileEmailRepository."""

    @pytest.fixture
    def repo(self, tmp_path):
        """Create a FileEmailRepository instance."""
        return FileEmailRepository(tmp_path / "storage")

    def test_empty_date_field(self, repo):
        """Test handling of missing/empty date field."""
        email = {'id': 'no_date_email', 'subject': 'No Date'}
        result = repo.save(email)
        assert result is True

        # Should be saved in 'unknown' directory
        unknown_path = repo.base_path / 'unknown'
        assert unknown_path.exists()

    def test_overwrite_existing_email(self, repo):
        """Test that saving same ID overwrites existing email."""
        repo.save({'id': 'overwrite_test', 'subject': 'Original', 'date': '2025-03-15'})
        repo.save({'id': 'overwrite_test', 'subject': 'Updated', 'date': '2025-03-15'})

        retrieved = repo.get('overwrite_test')
        assert retrieved['subject'] == 'Updated'
        assert repo.count() == 1

    def test_corrupted_json_file_handling(self, repo):
        """Test handling of corrupted JSON files during index rebuild."""
        # Save a valid email
        repo.save({'id': 'valid_email', 'subject': 'Valid', 'date': '2025-03-15'})

        # Create a corrupted JSON file
        corrupted_path = repo.base_path / 'corrupted.json'
        corrupted_path.write_text('{ invalid json }')

        # Refresh index should skip corrupted file
        count = repo.refresh_index()
        assert count == 1  # Only valid email counted
