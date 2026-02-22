"""Core calculation engine for sample size and tolerance interval calculations.

This module implements the mathematical formulas for:
- Module A: Attribute data analysis (Success Run Theorem, Cumulative Binomial)
- Module V: Variable data analysis (Tolerance factors, Non-parametric methods)

All methods are static and stateless for deterministic calculations.
"""

import math

from scipy.stats import binom, nct, norm


class CalculationEngine:
    """Core calculation engine for sample size and tolerance interval calculations."""

    @staticmethod
    def success_run_theorem(confidence: float, reliability: float) -> int:
        """Calculate sample size using Success Run Theorem (c=0).

        Formula: n = ceiling(ln(1-C) / ln(R))
        where C and R are expressed as decimals (e.g., 95% = 0.95)

        This method is used when zero failures are allowed in the test.

        Args:
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            Required sample size (integer)

        Raises:
            ValueError: If confidence or reliability are not in range (0, 100)

        Example:
            >>> CalculationEngine.success_run_theorem(95.0, 95.0)
            59
        """
        if not (0 < confidence < 100):
            raise ValueError("Confidence must be between 0 and 100")
        if not (0 < reliability < 100):
            raise ValueError("Reliability must be between 0 and 100")

        # Convert percentages to decimals
        c_conf = confidence / 100.0
        r_rel = reliability / 100.0

        # Apply Success Run Theorem formula
        n = math.ceil(math.log(1 - c_conf) / math.log(r_rel))
        return n

    @staticmethod
    def cumulative_binomial(
        confidence: float, reliability: float, allowable_failures: int
    ) -> int:
        """Calculate sample size using cumulative binomial distribution (c>0).

        Find minimum n where:
        sum(k=0 to c) [C(n,k) * (1-R)^k * R^(n-k)] <= 1-C

        Uses scipy.stats.binom.cdf for cumulative probability calculation.

        Args:
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)
            allowable_failures: Number of allowable failures (c), must be > 0

        Returns:
            Required sample size (integer)

        Raises:
            ValueError: If inputs are invalid or allowable_failures <= 0

        Example:
            >>> CalculationEngine.cumulative_binomial(95.0, 95.0, 1)
            93
        """
        if not (0 < confidence < 100):
            raise ValueError("Confidence must be between 0 and 100")
        if not (0 < reliability < 100):
            raise ValueError("Reliability must be between 0 and 100")
        if allowable_failures <= 0:
            raise ValueError(
                "Allowable failures must be greater than 0 for cumulative binomial"
            )

        # Convert percentages to decimals
        c_conf = confidence / 100.0
        r_rel = reliability / 100.0
        c = allowable_failures

        # Start with Success Run Theorem result as lower bound
        n = CalculationEngine.success_run_theorem(confidence, reliability)

        # Iterate until constraint is satisfied
        # The cumulative probability of c or fewer failures should be <= 1-C
        max_iterations = 100000  # Safety limit
        for _ in range(max_iterations):
            # Calculate cumulative binomial probability
            # P(X <= c) where X ~ Binomial(n, 1-R)
            cumulative_prob = binom.cdf(c, n, 1 - r_rel)

            if cumulative_prob <= 1 - c_conf:
                return n
            n += 1

        raise RuntimeError("Sample size calculation did not converge")

    @staticmethod
    def sensitivity_analysis(
        confidence: float, reliability: float
    ) -> list[tuple[int, int]]:
        """Calculate sample sizes for c=0,1,2,3.

        Performs sensitivity analysis by calculating required sample sizes
        for multiple allowable failure scenarios.

        Args:
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            List of (c, n) tuples where c is allowable failures and n is sample size

        Example:
            >>> CalculationEngine.sensitivity_analysis(95.0, 95.0)
            [(0, 59), (1, 93), (2, 124), (3, 153)]
        """
        results = []
        for c in [0, 1, 2, 3]:
            if c == 0:
                n = CalculationEngine.success_run_theorem(confidence, reliability)
            else:
                n = CalculationEngine.cumulative_binomial(
                    confidence, reliability, c
                )
            results.append((c, n))
        return results

    @staticmethod
    def one_sided_tolerance_factor(
        n: int, confidence: float, reliability: float
    ) -> float:
        """Calculate one-sided tolerance factor k1 using non-central t-distribution.

        The one-sided tolerance factor is used to calculate tolerance intervals
        for parametric data with one-sided specifications.

        Args:
            n: Sample size
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            One-sided tolerance factor k1

        Raises:
            ValueError: If inputs are invalid or n < 2

        Reference:
            ISO 16269-6:2014 Statistical interpretation of data
        """
        if n < 2:
            raise ValueError("Sample size must be at least 2")
        if not (0 < confidence < 100):
            raise ValueError("Confidence must be between 0 and 100")
        if not (0 < reliability < 100):
            raise ValueError("Reliability must be between 0 and 100")

        # Convert percentages to decimals
        c_conf = confidence / 100.0
        r_rel = reliability / 100.0

        # Degrees of freedom
        df = n - 1

        # Non-centrality parameter for one-sided tolerance interval
        # We need to find k such that the probability is C
        # Using the non-central t-distribution
        z_r = norm.ppf(r_rel)  # Standard normal quantile for reliability

        # For one-sided tolerance factor:
        # k1 = (z_r * sqrt(n) + t_alpha * sqrt(1 + z_R^2)) / sqrt(n)
        # where t_alpha is the t-quantile at confidence level C

        # Non-centrality parameter
        ncp = z_r * math.sqrt(n)

        # Find the t-value such that P(T <= t) = C where T ~ nct(df, ncp)
        k1 = nct.ppf(c_conf, df, ncp) / math.sqrt(n)

        return k1

    @staticmethod
    def two_sided_tolerance_factor(
        n: int, confidence: float, reliability: float
    ) -> float:
        """Calculate two-sided tolerance factor k2 using Howe-Guenther approximation.

        The two-sided tolerance factor is used to calculate tolerance intervals
        for parametric data with two-sided specifications.

        Args:
            n: Sample size
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            Two-sided tolerance factor k2

        Raises:
            ValueError: If inputs are invalid or n < 2

        Reference:
            Howe, W.G. (1969). Two-sided tolerance limits for normal populations
        """
        if n < 2:
            raise ValueError("Sample size must be at least 2")
        if not (0 < confidence < 100):
            raise ValueError("Confidence must be between 0 and 100")
        if not (0 < reliability < 100):
            raise ValueError("Reliability must be between 0 and 100")

        # Convert percentages to decimals
        c_conf = confidence / 100.0
        r_rel = reliability / 100.0

        # Degrees of freedom
        df = n - 1

        # For two-sided tolerance intervals, we use the Howe-Guenther approximation
        # k2 is approximately related to k1 but accounts for both tails

        # Standard normal quantile for two-sided reliability
        z_r = norm.ppf((1 + r_rel) / 2)  # Two-sided quantile

        # Non-centrality parameter
        ncp = z_r * math.sqrt(n)

        # Find the t-value for two-sided interval
        k2 = nct.ppf(c_conf, df, ncp) / math.sqrt(n)

        return k2

    @staticmethod
    def non_parametric_one_sided_sample_size(
        confidence: float, reliability: float
    ) -> int:
        """Calculate non-parametric sample size for one-sided specification.

        Uses the same formula as Success Run Theorem: n = ceiling(ln(1-C)/ln(R))
        This is because non-parametric one-sided tolerance intervals use
        extreme order statistics (minimum or maximum).

        Args:
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            Required sample size (integer)

        Example:
            >>> CalculationEngine.non_parametric_one_sided_sample_size(95.0, 95.0)
            59
        """
        # Non-parametric one-sided uses the same formula as Success Run Theorem
        return CalculationEngine.success_run_theorem(confidence, reliability)

    @staticmethod
    def non_parametric_two_sided_sample_size(
        confidence: float, reliability: float
    ) -> int:
        """Calculate non-parametric sample size for two-sided specification.

        Iterates N until the constraint is satisfied:
        1 - N*R^(N-1) + (N-1)*R^N >= c_conf

        This formula accounts for using both minimum and maximum order statistics
        for two-sided tolerance intervals.

        Args:
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            Required sample size (integer)

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If calculation does not converge
        """
        if not (0 < confidence < 100):
            raise ValueError("Confidence must be between 0 and 100")
        if not (0 < reliability < 100):
            raise ValueError("Reliability must be between 0 and 100")

        # Convert percentages to decimals
        c_conf = confidence / 100.0
        r_rel = reliability / 100.0

        # Start with one-sided result as lower bound
        n = CalculationEngine.non_parametric_one_sided_sample_size(
            confidence, reliability
        )

        # Iterate until constraint is satisfied
        max_iterations = 100000  # Safety limit
        for _ in range(max_iterations):
            # Calculate the probability that both min and max are within tolerance
            # Formula: 1 - N*R^(N-1) + (N-1)*R^N >= c_conf
            prob = 1 - n * (r_rel ** (n - 1)) + (n - 1) * (r_rel ** n)

            if prob >= c_conf:
                return n
            n += 1

        raise RuntimeError("Sample size calculation did not converge")
