"""Property-based tests for hash verification.

This module contains property-based tests using Hypothesis to verify
the correctness of SHA-256 hash calculation and validation state determination.
"""

import json
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from src.sample_size_calculator.hash_verifier import HashVerifier


class TestHashVerification:
    """Property-based tests for hash verification functionality."""

    @given(content=st.binary(min_size=0, max_size=10000))
    def test_property_28_hash_calculation_idempotence(self, content: bytes) -> None:
        """Property 28: Hash Calculation Idempotence.

        **Validates: Requirements 28.4**

        For any file content, calculating the SHA-256 hash multiple times
        should produce identical results (idempotence property).
        """
        # Create a temporary file with the given content
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        try:
            # Calculate hash multiple times
            hash1 = HashVerifier.calculate_file_hash(tmp_path)
            hash2 = HashVerifier.calculate_file_hash(tmp_path)
            hash3 = HashVerifier.calculate_file_hash(tmp_path)

            # All hashes should be identical
            assert hash1 == hash2 == hash3, (
                f"Hash calculation is not idempotent: "
                f"got {hash1}, {hash2}, {hash3}"
            )

            # Verify hash is a valid hexadecimal string of correct length (64 chars for SHA-256)
            assert len(hash1) == 64, f"SHA-256 hash should be 64 characters, got {len(hash1)}"
            assert all(c in "0123456789abcdef" for c in hash1), (
                f"Hash should be hexadecimal, got {hash1}"
            )

        finally:
            # Clean up temporary file
            tmp_path.unlink()

    @given(
        content1=st.binary(min_size=1, max_size=1000),
        content2=st.binary(min_size=1, max_size=1000),
    )
    def test_property_28_hash_uniqueness(self, content1: bytes, content2: bytes) -> None:
        """Property 28: Hash Uniqueness (additional validation).

        **Validates: Requirements 28.4**

        Different file contents should produce different hashes (with overwhelming probability).
        """
        # Skip if contents are identical
        if content1 == content2:
            return

        # Create temporary files with different content
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file1:
            tmp_file1.write(content1)
            tmp_path1 = Path(tmp_file1.name)

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file2:
            tmp_file2.write(content2)
            tmp_path2 = Path(tmp_file2.name)

        try:
            # Calculate hashes
            hash1 = HashVerifier.calculate_file_hash(tmp_path1)
            hash2 = HashVerifier.calculate_file_hash(tmp_path2)

            # Different contents should produce different hashes
            assert hash1 != hash2, (
                f"Different contents produced same hash: {hash1}"
            )

        finally:
            # Clean up temporary files
            tmp_path1.unlink()
            tmp_path2.unlink()

    @given(hash_value=st.text(min_size=64, max_size=64, alphabet="0123456789abcdef"))
    def test_property_29_validation_state_determination(self, hash_value: str) -> None:
        """Property 29: Validation State Determination.

        **Validates: Requirements 29.1, 29.2, 29.3**

        The validation state should be determined correctly by comparing
        the current engine hash against the stored validated hash:
        - If hashes match: validated state is True
        - If hashes don't match: validated state is False
        - If no validated hash stored: validated state is False
        """
        # Create a temporary config directory for testing
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_config_dir = Path(tmp_dir)
            tmp_validated_hash_file = tmp_config_dir / "validated_hash.json"

            # Temporarily override the config paths
            original_config_dir = HashVerifier.CONFIG_DIR
            original_validated_hash_file = HashVerifier.VALIDATED_HASH_FILE

            try:
                HashVerifier.CONFIG_DIR = tmp_config_dir
                HashVerifier.VALIDATED_HASH_FILE = tmp_validated_hash_file

                # Test Case 1: No validated hash stored
                # Validation state should be False
                assert not HashVerifier.is_validated_state(), (
                    "Validation state should be False when no validated hash is stored"
                )
                assert HashVerifier.get_validated_hash() is None, (
                    "get_validated_hash() should return None when file doesn't exist"
                )

                # Test Case 2: Store a validated hash
                HashVerifier.set_validated_hash(hash_value)

                # Verify the hash was stored correctly
                stored_hash = HashVerifier.get_validated_hash()
                assert stored_hash == hash_value, (
                    f"Stored hash {stored_hash} doesn't match set hash {hash_value}"
                )

                # Verify the config file was created with correct structure
                assert tmp_validated_hash_file.exists(), (
                    "Validated hash file should be created"
                )

                with open(tmp_validated_hash_file) as f:
                    config = json.load(f)
                    assert "validated_hash" in config, (
                        "Config should contain 'validated_hash' key"
                    )
                    assert config["validated_hash"] == hash_value, (
                        f"Config hash {config['validated_hash']} doesn't match {hash_value}"
                    )

                # Test Case 3: Current engine hash vs stored hash
                current_hash = HashVerifier.get_engine_hash()

                if current_hash == hash_value:
                    # Hashes match: validation state should be True
                    assert HashVerifier.is_validated_state(), (
                        "Validation state should be True when hashes match"
                    )
                else:
                    # Hashes don't match: validation state should be False
                    assert not HashVerifier.is_validated_state(), (
                        "Validation state should be False when hashes don't match"
                    )

                # Test Case 4: Idempotence of validation state check
                state1 = HashVerifier.is_validated_state()
                state2 = HashVerifier.is_validated_state()
                state3 = HashVerifier.is_validated_state()

                assert state1 == state2 == state3, (
                    f"Validation state check is not idempotent: "
                    f"got {state1}, {state2}, {state3}"
                )

            finally:
                # Restore original config paths
                HashVerifier.CONFIG_DIR = original_config_dir
                HashVerifier.VALIDATED_HASH_FILE = original_validated_hash_file

    def test_property_29_engine_hash_consistency(self) -> None:
        """Property 29: Engine Hash Consistency (additional validation).

        **Validates: Requirements 29.1, 29.2, 29.3**

        The engine hash should remain consistent across multiple calls
        as long as the calculations.py file hasn't changed.
        """
        # Get engine hash multiple times
        hash1 = HashVerifier.get_engine_hash()
        hash2 = HashVerifier.get_engine_hash()
        hash3 = HashVerifier.get_engine_hash()

        # All should be identical
        assert hash1 == hash2 == hash3, (
            f"Engine hash is not consistent: got {hash1}, {hash2}, {hash3}"
        )

        # Verify it's a valid SHA-256 hash
        assert len(hash1) == 64, f"Engine hash should be 64 characters, got {len(hash1)}"
        assert all(c in "0123456789abcdef" for c in hash1), (
            f"Engine hash should be hexadecimal, got {hash1}"
        )
