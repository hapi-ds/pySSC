#!/usr/bin/env python3
"""URS Coverage Calculator.

This script calculates URS (User Requirement Specification) coverage by:
1. Parsing the official URS document to extract all URS IDs
2. Extracting URS IDs from test markers in validation test files
3. Calculating coverage metrics (total, covered, uncovered, percentage)
4. Calculating coverage by category (IQ, FUNC_A, V, UI, REP, VTM, PQ, OQ)
5. Calculating coverage by suite (IQ/OQ/PQ)

Usage:
    from scripts.calculate_coverage import calculate_coverage

    coverage = calculate_coverage(
        urs_document_path="requirements/02_URS_SampleSizeCalculator.md",
        test_files=[
            "tests/validation/test_iq.py",
            "tests/validation/test_oq.py",
            "tests/validation/test_pq.py"
        ]
    )
"""

import re
from pathlib import Path
from typing import Any


def parse_urs_document(urs_document_path: str) -> set[str]:
    """Parse the official URS document to extract all URS IDs.

    Args:
        urs_document_path: Path to the official URS document

    Returns:
        Set of URS IDs found in the document
    """
    urs_path = Path(urs_document_path)

    if not urs_path.exists():
        raise FileNotFoundError(f"URS document not found: {urs_document_path}")

    content = urs_path.read_text()

    # Pattern to match URS IDs like URS-IQ-01, URS-FUNC_A-02, URS-V-13, etc.
    # Matches: URS-<CATEGORY>-<NUMBER>
    pattern = r"\*\*URS-([A-Z_]+)-(\d+)\*\*"

    matches = re.findall(pattern, content)

    # Reconstruct URS IDs from matches
    urs_ids = {f"URS-{category}-{number}" for category, number in matches}

    return urs_ids


def extract_urs_ids_from_tests(test_files: list[str]) -> set[str]:
    """Extract URS IDs from @pytest.mark.urs() decorators in test files.

    Args:
        test_files: List of test file paths

    Returns:
        Set of URS IDs found in test markers
    """
    urs_ids = set()

    for test_file in test_files:
        test_path = Path(test_file)

        if not test_path.exists():
            print(f"Warning: Test file not found: {test_file}")
            continue

        content = test_path.read_text()

        # Pattern to match @pytest.mark.urs("URS-ID-01") or @pytest.mark.urs("URS-ID-01", "URS-ID-02")
        # This matches the decorator and captures all quoted strings inside
        pattern = r"@pytest\.mark\.urs\((.*?)\)"

        matches = re.findall(pattern, content)

        for match in matches:
            # Extract all quoted strings from the decorator arguments
            urs_pattern = r'["\']([^"\']+)["\']'
            found_ids = re.findall(urs_pattern, match)

            # Only add IDs that match the URS-* format
            for urs_id in found_ids:
                if urs_id.startswith("URS-"):
                    urs_ids.add(urs_id)

    return urs_ids


def extract_category_from_urs_id(urs_id: str) -> str:
    """Extract the category from a URS ID.

    Args:
        urs_id: URS ID like "URS-IQ-01" or "URS-FUNC_A-02"

    Returns:
        Category string like "IQ" or "FUNC_A"
    """
    # Pattern: URS-<CATEGORY>-<NUMBER>
    match = re.match(r"URS-([A-Z_]+)-\d+", urs_id)
    if match:
        return match.group(1)
    return "UNKNOWN"


def calculate_category_coverage(
    official_urs_ids: set[str], covered_urs_ids: set[str]
) -> dict[str, dict[str, Any]]:
    """Calculate coverage breakdown by category.

    Args:
        official_urs_ids: Set of all URS IDs from official document
        covered_urs_ids: Set of URS IDs covered by tests

    Returns:
        Dictionary mapping category to coverage metrics
    """
    # Get all categories
    categories = {extract_category_from_urs_id(urs_id) for urs_id in official_urs_ids}

    coverage_by_category = {}

    for category in sorted(categories):
        # Get all URS IDs for this category
        category_ids = {
            urs_id
            for urs_id in official_urs_ids
            if extract_category_from_urs_id(urs_id) == category
        }

        # Get covered IDs for this category
        category_covered = category_ids.intersection(covered_urs_ids)

        # Calculate percentage
        total = len(category_ids)
        covered = len(category_covered)
        percentage = (covered / total * 100) if total > 0 else 0.0

        coverage_by_category[category] = {
            "total": total,
            "covered": covered,
            "uncovered": total - covered,
            "percentage": percentage,
            "covered_ids": sorted(category_covered),
            "uncovered_ids": sorted(category_ids - category_covered),
        }

    return coverage_by_category


def extract_suite_from_test_file(test_file: str) -> str:
    """Extract the test suite name from a test file path.

    Args:
        test_file: Path to test file

    Returns:
        Suite name (IQ, OQ, or PQ)
    """
    if "test_iq.py" in test_file:
        return "IQ"
    elif "test_oq.py" in test_file:
        return "OQ"
    elif "test_pq.py" in test_file:
        return "PQ"
    return "UNKNOWN"


def calculate_suite_coverage(test_files: list[str]) -> dict[str, dict[str, Any]]:
    """Calculate coverage breakdown by test suite (IQ/OQ/PQ).

    Args:
        test_files: List of test file paths

    Returns:
        Dictionary mapping suite to coverage metrics
    """
    coverage_by_suite = {}

    for test_file in test_files:
        suite = extract_suite_from_test_file(test_file)

        if suite == "UNKNOWN":
            continue

        test_path = Path(test_file)

        if not test_path.exists():
            continue

        content = test_path.read_text()

        # Count tests in this file
        test_pattern = r"def (test_\w+)\("
        tests = re.findall(test_pattern, content)

        # Extract URS IDs from this file
        urs_pattern = r"@pytest\.mark\.urs\((.*?)\)"
        marker_matches = re.findall(urs_pattern, content)

        urs_ids = set()
        for match in marker_matches:
            urs_id_pattern = r'["\']([^"\']+)["\']'
            found_ids = re.findall(urs_id_pattern, match)
            for urs_id in found_ids:
                if urs_id.startswith("URS-"):
                    urs_ids.add(urs_id)

        coverage_by_suite[suite] = {
            "test_count": len(tests),
            "urs_ids_covered": sorted(urs_ids),
            "unique_urs_count": len(urs_ids),
        }

    return coverage_by_suite


def calculate_coverage(urs_document_path: str, test_files: list[str]) -> dict[str, Any]:
    """Calculate URS coverage metrics.

    Args:
        urs_document_path: Path to official URS document
        test_files: List of test file paths

    Returns:
        Dictionary with coverage metrics including:
        - total_requirements: Total number of URS requirements
        - covered_requirements: Number of requirements covered by tests
        - uncovered_requirements: Number of requirements not covered
        - coverage_percentage: Percentage of requirements covered
        - uncovered_ids: List of URS IDs not covered by any test
        - coverage_by_category: Coverage breakdown by category
        - coverage_by_suite: Coverage breakdown by test suite
    """
    # Parse official URS document
    official_urs_ids = parse_urs_document(urs_document_path)

    # Extract URS IDs from test markers
    test_urs_ids = extract_urs_ids_from_tests(test_files)

    # Calculate coverage
    covered_ids = official_urs_ids.intersection(test_urs_ids)
    uncovered_ids = official_urs_ids - covered_ids

    # Calculate overall coverage percentage
    total = len(official_urs_ids)
    covered = len(covered_ids)
    coverage_percentage = (covered / total * 100) if total > 0 else 0.0

    # Calculate category coverage
    coverage_by_category = calculate_category_coverage(official_urs_ids, covered_ids)

    # Calculate suite coverage
    coverage_by_suite = calculate_suite_coverage(test_files)

    return {
        "total_requirements": total,
        "covered_requirements": covered,
        "uncovered_requirements": len(uncovered_ids),
        "coverage_percentage": coverage_percentage,
        "covered_ids": sorted(covered_ids),
        "uncovered_ids": sorted(uncovered_ids),
        "coverage_by_category": coverage_by_category,
        "coverage_by_suite": coverage_by_suite,
    }


def print_coverage_report(coverage: dict[str, Any]) -> None:
    """Print a formatted coverage report to console.

    Args:
        coverage: Coverage metrics dictionary from calculate_coverage()
    """
    print("\n" + "=" * 70)
    print("URS COVERAGE REPORT")
    print("=" * 70)

    print(f"\nTotal URS Requirements:     {coverage['total_requirements']}")
    print(f"Covered by Tests:           {coverage['covered_requirements']}")
    print(f"Uncovered:                  {coverage['uncovered_requirements']}")
    print(f"Coverage:                   {coverage['coverage_percentage']:.1f}%")

    if coverage["uncovered_ids"]:
        print(f"\nUncovered Requirements ({len(coverage['uncovered_ids'])}):")
        for urs_id in coverage["uncovered_ids"]:
            print(f"  - {urs_id}")

    print("\n" + "-" * 70)
    print("COVERAGE BY CATEGORY")
    print("-" * 70)
    print(
        f"{'Category':<12} {'Total':>6} {'Covered':>8} {'Uncovered':>10} {'Coverage':>10}"
    )
    print("-" * 70)

    for category, metrics in coverage["coverage_by_category"].items():
        print(
            f"{category:<12} "
            f"{metrics['total']:>6} "
            f"{metrics['covered']:>8} "
            f"{metrics['uncovered']:>10} "
            f"{metrics['percentage']:>9.1f}%"
        )

    print("\n" + "-" * 70)
    print("COVERAGE BY TEST SUITE")
    print("-" * 70)
    print(f"{'Suite':<8} {'Tests':>6} {'Unique URS':>12}")
    print("-" * 70)

    for suite, metrics in coverage["coverage_by_suite"].items():
        print(
            f"{suite:<8} {metrics['test_count']:>6} {metrics['unique_urs_count']:>12}"
        )

    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Example usage
    coverage = calculate_coverage(
        urs_document_path="requirements/02_URS_SampleSizeCalculator.md",
        test_files=[
            "tests/validation/test_iq.py",
            "tests/validation/test_oq.py",
            "tests/validation/test_pq.py",
        ],
    )

    print_coverage_report(coverage)
