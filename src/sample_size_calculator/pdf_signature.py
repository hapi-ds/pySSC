"""PDF Digital Signature Module.

This module provides functionality for signing and verifying PDF reports
using SHA-256 hash verification to ensure document integrity and detect tampering.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path


class PDFSignature:
    """Handles PDF signing and verification using hash-based integrity checks."""

    @staticmethod
    def sign_pdf(pdf_bytes: bytes, engine_hash: str) -> dict:
        """
        Sign a PDF document by generating hash metadata.

        Args:
            pdf_bytes: PDF content as bytes
            engine_hash: Current calculation engine hash (SHA-256)

        Returns:
            Signature metadata dictionary containing:
                - pdf_hash: SHA-256 of the PDF content
                - engine_hash: Hash of the calculation engine
                - timestamp: When the signature was created
                - integrity_verified: Flag indicating successful signing

        Example:
            >>> with open("report.pdf", "rb") as f:
            ...     signature = PDFSignature.sign_pdf(f.read(), "abc123...")
            >>> print(signature["integrity_verified"])  # True
        """
        # Generate hash of PDF content for tamper detection
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
        
        signature = {
            "pdf_hash": pdf_hash,  # Hash of PDF content (for tamper detection)
            "engine_hash": engine_hash,  # Hash of calculation engine that generated it
            "timestamp": datetime.now().isoformat(),
            "integrity_verified": True,
            "signature_type": "SHA-256 hash verification"
        }
        
        return signature

    @staticmethod
    def verify_signature(pdf_path: Path) -> tuple[bool, dict | None]:
        """
        Verify PDF integrity against stored signature.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (verification_passed, signature_metadata)
            
        The verification checks if:
            1. A signature file exists (.sig.json)
            2. The current PDF hash matches the stored hash
            
        Note: This provides integrity verification but not cryptographic authentication
              (since no private key is used). For true digital signatures, use 
              cryptographic libraries like cryptography with PKCS#7.
        """
        try:
            # Load signature metadata if it exists
            sig_path = pdf_path.with_suffix('.sig.json')
            if not sig_path.exists():
                return False, None
            
            with open(sig_path) as f:
                sig_meta = json.load(f)
            
            # Recalculate hash of current PDF content
            current_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
            
            # Compare hashes
            if current_hash == sig_meta.get("pdf_hash"):
                return True, sig_meta
            
            return False, sig_meta
            
        except (json.JSONDecodeError, IOError):
            return False, None

    @staticmethod
    def save_signature(pdf_path: Path, signature: dict) -> Path:
        """
        Save signature metadata to a JSON file alongside the PDF.

        Args:
            pdf_path: Path to the PDF file
            signature: Signature metadata dictionary from sign_pdf()

        Returns:
            Path to the saved signature file (.sig.json)
        """
        sig_path = pdf_path.with_suffix('.sig.json')
        
        with open(sig_path, 'w') as f:
            json.dump(signature, f, indent=2)
        
        return sig_path

    @staticmethod
    def load_signature(pdf_path: Path) -> dict | None:
        """
        Load signature metadata from JSON file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Signature metadata dictionary if it exists and is valid, None otherwise
        """
        sig_path = pdf_path.with_suffix('.sig.json')
        
        try:
            with open(sig_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None


def sign_pdf(pdf_bytes: bytes, engine_hash: str) -> dict:
    """Convenience function for PDF signing."""
    return PDFSignature.sign_pdf(pdf_bytes, engine_hash)


def verify_signature(pdf_path: Path) -> tuple[bool, dict | None]:
    """Convenience function for PDF signature verification."""
    return PDFSignature.verify_signature(pdf_path)
