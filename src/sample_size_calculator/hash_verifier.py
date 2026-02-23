"""SHA-256 hash verification for calculation engine integrity.

This module provides functionality to calculate and verify SHA-256 hashes
of the calculation engine to ensure code integrity for QMS compliance.
"""

import hashlib
import json
from pathlib import Path


class HashVerifier:
    """Manages calculation engine hash verification for QMS compliance."""

    # Path to the calculation engine file
    ENGINE_FILE = Path(__file__).parent / "calculations.py"

    # Path to the validated hash configuration file
    CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
    VALIDATED_HASH_FILE = CONFIG_DIR / "validated_hash.json"

    @staticmethod
    def calculate_file_hash(filepath: str | Path) -> str:
        """Calculate SHA-256 hash of a file.

        Args:
            filepath: Path to the file to hash

        Returns:
            Hexadecimal SHA-256 hash string

        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If the file cannot be read
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        sha256_hash = hashlib.sha256()

        try:
            with open(filepath, "rb") as f:
                # Read file in chunks to handle large files efficiently
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
        except OSError as e:
            raise OSError(f"Failed to read file {filepath}: {e}") from e

        return sha256_hash.hexdigest()

    @staticmethod
    def get_engine_hash() -> str:
        """Get current SHA-256 hash of calculations.py.

        Returns:
            Hexadecimal SHA-256 hash string of the calculation engine
        """
        return HashVerifier.calculate_file_hash(HashVerifier.ENGINE_FILE)

    @staticmethod
    def get_validated_hash() -> str | None:
        """Retrieve stored validated hash from configuration file.

        Returns:
            Stored validated hash string, or None if not found or file doesn't exist
        """
        if not HashVerifier.VALIDATED_HASH_FILE.exists():
            return None

        try:
            with open(HashVerifier.VALIDATED_HASH_FILE) as f:
                config = json.load(f)
                return config.get("validated_hash")
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def set_validated_hash(hash_value: str) -> None:
        """Store validated hash to configuration file.

        Args:
            hash_value: SHA-256 hash string to store as validated

        Raises:
            IOError: If the configuration file cannot be written
        """
        # Ensure config directory exists
        HashVerifier.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        config = {
            "validated_hash": hash_value,
            "validation_date": None,  # To be set by validation suite
            "validator": None,  # To be set by validation suite
        }

        try:
            with open(HashVerifier.VALIDATED_HASH_FILE, "w") as f:
                json.dump(config, f, indent=2)
        except OSError as e:
            raise OSError(f"Failed to write validated hash: {e}") from e

    @staticmethod
    def is_validated_state() -> bool:
        """Check if current engine hash matches validated hash.

        Returns:
            True if current hash matches validated hash, False otherwise
        """
        current_hash = HashVerifier.get_engine_hash()
        validated_hash = HashVerifier.get_validated_hash()

        if validated_hash is None:
            return False

        return current_hash == validated_hash
