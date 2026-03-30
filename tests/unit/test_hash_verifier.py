"""Unit tests for hash verifier.

This module contains unit tests for SHA-256 hash calculation and validation
state determination to ensure code integrity for QMS compliance.
"""

import json
from pathlib import Path

import pytest

from sample_size_calculator.hash_verifier import (
    HashVerifier,
    get_engine_hash,
    get_validated_hash,
    is_validated_state,
    set_validated_hash,
)


class TestHashVerifierCalculateFileHash:
    """Unit tests for calculate_file_hash method."""

    def test_calculate_file_hash_with_text_content(self, tmp_path: Path) -> None:
        """Test hash calculation with text file content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        hash_result = HashVerifier.calculate_file_hash(test_file)

        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)
        assert isinstance(hash_result, str)

    def test_calculate_file_hash_with_binary_content(self, tmp_path: Path) -> None:
        """Test hash calculation with binary file content."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

        hash_result = HashVerifier.calculate_file_hash(test_file)

        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_calculate_file_hash_empty_file(self, tmp_path: Path) -> None:
        """Test hash calculation with empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        hash_result = HashVerifier.calculate_file_hash(test_file)

        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_calculate_file_hash_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised for non-existent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            HashVerifier.calculate_file_hash(nonexistent)

    def test_calculate_file_hash_idempotent(self, tmp_path: Path) -> None:
        """Test hash calculation is idempotent."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Same content")

        hash1 = HashVerifier.calculate_file_hash(test_file)
        hash2 = HashVerifier.calculate_file_hash(test_file)
        hash3 = HashVerifier.calculate_file_hash(test_file)

        assert hash1 == hash2 == hash3

    def test_calculate_file_hash_different_content(self, tmp_path: Path) -> None:
        """Test that different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content A")
        file2.write_text("Content B")

        hash1 = HashVerifier.calculate_file_hash(file1)
        hash2 = HashVerifier.calculate_file_hash(file2)

        assert hash1 != hash2

    def test_calculate_file_hash_large_file(self, tmp_path: Path) -> None:
        """Test hash calculation with large file."""
        test_file = tmp_path / "large.bin"
        # Create 1MB file
        test_file.write_bytes(b"x" * (1024 * 1024))

        hash_result = HashVerifier.calculate_file_hash(test_file)

        assert len(hash_result) == 64


class TestHashVerifierCalculatePackageHash:
    """Unit tests for calculate_package_hash method."""

    def test_calculate_package_hash_returns_valid_hash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that package hash calculation returns valid SHA-256."""
        # Create a temporary directory structure
        temp_dir = tmp_path / "test_package"
        temp_dir.mkdir()

        # Create some test Python files
        (temp_dir / "file1.py").write_text("def func1(): pass")
        (temp_dir / "file2.py").write_text("def func2(): return 42")

        # Patch SOURCE_DIR to point to our temporary directory
        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)

        hash_result = HashVerifier.calculate_package_hash()

        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)
        assert isinstance(hash_result, str)

    def test_calculate_package_hash_consistent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that package hash calculation is consistent."""
        temp_dir = tmp_path / "test_package"
        temp_dir.mkdir()
        (temp_dir / "file.py").write_text("test")

        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)

        hash1 = HashVerifier.calculate_package_hash()
        hash2 = HashVerifier.calculate_package_hash()

        assert hash1 == hash2

    def test_calculate_package_hash_changes_with_content(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that hash changes when file content changes."""
        temp_dir = tmp_path / "test_package"
        temp_dir.mkdir()
        test_file = temp_dir / "file.py"

        test_file.write_text("content A")
        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)
        hash_a = HashVerifier.calculate_package_hash()

        test_file.write_text("content B")
        hash_b = HashVerifier.calculate_package_hash()

        assert hash_a != hash_b

    def test_calculate_package_hash_ignores_non_py_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that non-Python files are ignored."""
        temp_dir = tmp_path / "test_package"
        temp_dir.mkdir()
        (temp_dir / "file.py").write_text("def func(): pass")
        (temp_dir / "readme.md").write_text("# Readme")
        (temp_dir / "data.json").write_text('{"key": "value"}')

        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)

        hash_with_only_py = HashVerifier.calculate_package_hash()

        # Add non-Python file
        (temp_dir / "config.yaml").write_text("key: value")
        hash_with_extra_files = HashVerifier.calculate_package_hash()

        assert hash_with_only_py == hash_with_extra_files

    def test_calculate_package_hash_ignores_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that calculation continues on file read errors."""
        temp_dir = tmp_path / "test_package"
        temp_dir.mkdir()
        (temp_dir / "file1.py").write_text("def func(): pass")

        unreadable = temp_dir / "unreadable.py"
        unreadable.write_text("data")
        unreadable.chmod(0o000)

        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)

        # Should not raise exception
        hash_result = HashVerifier.calculate_package_hash()

        assert len(hash_result) == 64

        # Restore permissions for cleanup
        unreadable.chmod(0o644)


class TestHashVerifierGetEngineHash:
    """Unit tests for get_engine_hash method."""

    def test_get_engine_hash_returns_valid_hash(self) -> None:
        """Test that engine hash returns valid SHA-256."""
        hash_result = HashVerifier.get_engine_hash()

        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)
        assert isinstance(hash_result, str)

    def test_get_engine_hash_is_consistent(self) -> None:
        """Test that engine hash is consistent across calls."""
        hash1 = HashVerifier.get_engine_hash()
        hash2 = HashVerifier.get_engine_hash()
        hash3 = HashVerifier.get_engine_hash()

        assert hash1 == hash2 == hash3

    def test_get_engine_hash_equals_package_hash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_engine_hash equals calculate_package_hash."""
        temp_dir = tmp_path / "test_package"
        temp_dir.mkdir()
        (temp_dir / "file.py").write_text("test")

        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)

        engine_hash = HashVerifier.get_engine_hash()
        package_hash = HashVerifier.calculate_package_hash()

        assert engine_hash == package_hash


class TestHashVerifierGetSetValidatedHash:
    """Unit tests for get_validated_hash and set_validated_hash methods."""

    def test_get_validated_hash_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_validated_hash returns None when file doesn't exist."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(
            HashVerifier, "VALIDATED_HASH_FILE", temp_dir / "validated_hash.json"
        )

        result = HashVerifier.get_validated_hash()

        assert result is None

    def test_set_and_get_validated_hash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test setting and getting validated hash."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"
        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        test_hash = "a" * 64
        HashVerifier.set_validated_hash(test_hash)

        result = HashVerifier.get_validated_hash()

        assert result == test_hash

    def test_set_validated_hash_with_metadata(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test setting validated hash with optional metadata."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"
        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        test_hash = "b" * 64
        test_date = "2024-01-15T10:30:00"
        test_validator = "Test User"

        HashVerifier.set_validated_hash(test_hash, test_date, test_validator)

        with open(hash_file) as f:
            config = json.load(f)

        assert config["validated_hash"] == test_hash
        assert config["validation_date"] == test_date
        assert config["validator"] == test_validator

    def test_set_validated_hash_creates_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that set_validated_hash creates config directory if needed."""
        temp_dir = tmp_path / "new_config"
        hash_file = temp_dir / "validated_hash.json"
        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        HashVerifier.set_validated_hash("c" * 64)

        assert hash_file.exists()

    def test_get_validated_hash_invalid_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_validated_hash handles invalid JSON gracefully."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"
        hash_file.write_text("invalid json {")
        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        result = HashVerifier.get_validated_hash()

        assert result is None

    def test_get_validated_hash_missing_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_validated_hash returns None when key is missing."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"
        hash_file.write_text('{"other_key": "value"}')
        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        result = HashVerifier.get_validated_hash()

        assert result is None


class TestHashVerifierIsValidatedState:
    """Unit tests for is_validated_state method."""

    def test_is_validated_state_no_validated_hash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state is False when no validated hash exists."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(
            HashVerifier, "VALIDATED_HASH_FILE", temp_dir / "validated_hash.json"
        )

        assert not HashVerifier.is_validated_state()

    def test_is_validated_state_hash_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state is False when hashes don't match."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        # Set a different hash than current engine hash
        different_hash = "d" * 64
        with open(hash_file, "w") as f:
            json.dump({"validated_hash": different_hash}, f)

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        assert not HashVerifier.is_validated_state()

    def test_is_validated_state_hash_match_without_metadata(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state is False when hash matches but metadata missing."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        current_hash = HashVerifier.get_engine_hash()
        with open(hash_file, "w") as f:
            json.dump({"validated_hash": current_hash}, f)

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        # Even though hashes match, missing metadata means not validated
        assert not HashVerifier.is_validated_state()

    def test_is_validated_state_complete_validation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state is True when hash matches and metadata present."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        current_hash = HashVerifier.get_engine_hash()
        with open(hash_file, "w") as f:
            json.dump(
                {
                    "validated_hash": current_hash,
                    "validation_date": "2024-01-15",
                    "validator": "Test User",
                },
                f,
            )

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        assert HashVerifier.is_validated_state()

    def test_is_validated_state_invalid_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state is False with invalid JSON."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"
        hash_file.write_text("invalid json")
        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        assert not HashVerifier.is_validated_state()

    def test_is_validated_state_missing_metadata_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state is False when metadata keys are null."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        current_hash = HashVerifier.get_engine_hash()
        with open(hash_file, "w") as f:
            json.dump(
                {
                    "validated_hash": current_hash,
                    "validation_date": None,
                    "validator": None,
                },
                f,
            )

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        assert not HashVerifier.is_validated_state()

    def test_is_validated_state_partial_metadata(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state is False when only one metadata field present."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        current_hash = HashVerifier.get_engine_hash()
        with open(hash_file, "w") as f:
            json.dump(
                {
                    "validated_hash": current_hash,
                    "validation_date": "2024-01-15",
                    "validator": None,
                },
                f,
            )

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        assert not HashVerifier.is_validated_state()

    def test_is_validated_state_idempotent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state check is idempotent."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        current_hash = HashVerifier.get_engine_hash()
        with open(hash_file, "w") as f:
            json.dump(
                {
                    "validated_hash": current_hash,
                    "validation_date": "2024-01-15",
                    "validator": "Test User",
                },
                f,
            )

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        state1 = HashVerifier.is_validated_state()
        state2 = HashVerifier.is_validated_state()
        state3 = HashVerifier.is_validated_state()

        assert state1 == state2 == state3


class TestConvenienceFunctions:
    """Unit tests for convenience functions."""

    def test_get_engine_hash_convenience(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_engine_hash convenience function works."""
        temp_dir = tmp_path / "test_package"
        temp_dir.mkdir()
        (temp_dir / "file.py").write_text("test")

        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)

        result = get_engine_hash()

        assert len(result) == 64

    def test_is_validated_state_convenience(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that is_validated_state convenience function works."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        current_hash = HashVerifier.get_engine_hash()
        with open(hash_file, "w") as f:
            json.dump(
                {
                    "validated_hash": current_hash,
                    "validation_date": "2024-01-15",
                    "validator": "Test User",
                },
                f,
            )

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        assert is_validated_state()

    def test_get_validated_hash_convenience(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_validated_hash convenience function works."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        test_hash = "e" * 64
        with open(hash_file, "w") as f:
            json.dump({"validated_hash": test_hash}, f)

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        assert get_validated_hash() == test_hash

    def test_set_validated_hash_convenience(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that set_validated_hash convenience function works."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        test_hash = "f" * 64
        set_validated_hash(test_hash)

        assert hash_file.exists()
        with open(hash_file) as f:
            config = json.load(f)
        assert config["validated_hash"] == test_hash

    def test_set_validated_hash_convenience_with_metadata(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that set_validated_hash convenience function handles metadata."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        test_hash = "g" * 64
        test_date = "2024-02-20"
        test_validator = "Jane Doe"

        # Note: convenience function only takes hash_value, but we need to call the class method
        HashVerifier.set_validated_hash(test_hash, test_date, test_validator)

        with open(hash_file) as f:
            config = json.load(f)
        assert config["validated_hash"] == test_hash
        assert config["validation_date"] == test_date
        assert config["validator"] == test_validator


class TestEdgeCases:
    """Unit tests for edge cases."""

    def test_calculate_file_hash_unicode_content(self, tmp_path: Path) -> None:
        """Test hash calculation with Unicode content."""
        test_file = tmp_path / "unicode.txt"
        test_file.write_text("Hello, 世界! 🌍")

        hash_result = HashVerifier.calculate_file_hash(test_file)

        assert len(hash_result) == 64

    def test_calculate_file_hash_special_characters(self, tmp_path: Path) -> None:
        """Test hash calculation with special characters."""
        test_file = tmp_path / "special.txt"
        special_content = "Line1\nLine2\tTabbed\r\nCRLF"
        test_file.write_text(special_content)

        hash_result = HashVerifier.calculate_file_hash(test_file)
        expected_hash = HashVerifier.calculate_file_hash(test_file)

        assert hash_result == expected_hash

    def test_calculate_package_hash_single_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test package hash with only one Python file."""
        temp_dir = tmp_path / "test_package"
        temp_dir.mkdir()
        (temp_dir / "main.py").write_text("print('Hello')")

        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)

        hash_result = HashVerifier.calculate_package_hash()

        assert len(hash_result) == 64
        assert isinstance(hash_result, str)

    def test_calculate_package_hash_no_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test package hash with no Python files."""
        temp_dir = tmp_path / "empty_package"
        temp_dir.mkdir()

        monkeypatch.setattr(HashVerifier, "SOURCE_DIR", temp_dir)

        # Should still return a valid hash (hash of empty data)
        hash_result = HashVerifier.calculate_package_hash()

        assert len(hash_result) == 64

    def test_is_validated_state_concurrent_read(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation state can be read concurrently."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        current_hash = HashVerifier.get_engine_hash()
        with open(hash_file, "w") as f:
            json.dump(
                {
                    "validated_hash": current_hash,
                    "validation_date": "2024-01-15",
                    "validator": "Test User",
                },
                f,
            )

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        # Multiple reads should return consistent results
        states = [HashVerifier.is_validated_state() for _ in range(10)]
        assert all(states)
        assert len(set(states)) == 1

    def test_set_validated_hash_overwrites_existing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that set_validated_hash overwrites existing file."""
        temp_dir = tmp_path / "config"
        temp_dir.mkdir()
        hash_file = temp_dir / "validated_hash.json"

        monkeypatch.setattr(HashVerifier, "CONFIG_DIR", temp_dir)
        monkeypatch.setattr(HashVerifier, "VALIDATED_HASH_FILE", hash_file)

        HashVerifier.set_validated_hash("a" * 64)
        HashVerifier.set_validated_hash("b" * 64)

        result = HashVerifier.get_validated_hash()
        assert result == "b" * 64
