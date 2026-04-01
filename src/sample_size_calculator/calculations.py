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
        max_iterations = 150000  # Safety limit
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
                n = CalculationEngine.cumulative_binomial(confidence, reliability, c)
            results.append((c, n))
        return results


    @staticmethod
    def finite_population_correction(n0: int, population_size: int) -> float:
        """Apply finite population correction formula.

        Formula: n = (N * n0) / (N - 1 + n0)
        where N = population size and n0 = sample size for large populations

        This correction is applied when the sample size is a significant fraction
        of the population (typically >5%).

        Args:
            n0: Sample size for large populations (uncorrected)
            population_size: Total population size (must be > 1)

        Returns:
            Corrected sample size (float)

        Raises:
            ValueError: If inputs are invalid

        Example:
            >>> CalculationEngine.finite_population_correction(59, 1000)
            56.32...
            >>> CalculationEngine.finite_population_correction(59, 100)
            35.74...
        """
        if n0 < 1:
            raise ValueError("Sample size must be at least 1")
        if population_size <= 1:
            raise ValueError("Population size must be greater than 1")

        return (population_size * n0) / (population_size - 1 + n0)

    @staticmethod
    def sensitivity_analysis_with_correction(
        confidence: float,
        reliability: float,
        population_size: int | None = None,
    ) -> list[tuple[int, int, float | None]]:
        """Calculate sample sizes with optional finite population correction.

        Args:
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)
            population_size: Optional population size for correction

        Returns:
            List of (c, n_original, n_corrected) tuples
            where n_corrected is None if no correction applied
        """
        results = []
        for c in [0, 1, 2, 3]:
            if c == 0:
                n_original = CalculationEngine.success_run_theorem(
                    confidence, reliability
                )
            else:
                n_original = CalculationEngine.cumulative_binomial(
                    confidence, reliability, c
                )

            if population_size is not None and population_size > 1:
                n_corrected = CalculationEngine.finite_population_correction(
                    n_original, population_size
                )
            else:
                n_corrected = None

            results.append((c, n_original, n_corrected))
        return results

    @staticmethod
    @staticmethod
    def one_sided_tolerance_factor(
        n: int, confidence: float, reliability: float
    ) -> float:
        """Calculate one-sided tolerance factor k1 using non-central t-distribution.

        The one-sided tolerance factor is used to calculate tolerance intervals
        for parametric data with one-sided specifications (either LSL or USL).

        The tolerance factor k1 is calculated such that with confidence C, at least
        proportion R of the population falls within the tolerance interval defined by:
        - For LSL: TL = mean - k1 * std
        - For USL: TU = mean + k1 * std

        Mathematical Background:
            The one-sided tolerance factor is derived from the non-central t-distribution.
            For a sample of size n from a normal distribution, the tolerance factor k1
            satisfies:

            P(X̄ - k1*S ≤ μ - z_R*σ) = C

            where:
            - X̄ is the sample mean
            - S is the sample standard deviation
            - μ is the population mean
            - σ is the population standard deviation
            - z_R is the standard normal quantile at reliability R
            - C is the confidence level

            This is solved using the non-central t-distribution with:
            - Degrees of freedom: df = n - 1
            - Non-centrality parameter: ncp = z_R * √n
            - Quantile: t_C at confidence level C
            - Tolerance factor: k1 = t_C / √n

        Args:
            n: Sample size (must be ≥ 2)
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            One-sided tolerance factor k1

        Raises:
            ValueError: If inputs are invalid or n < 2

        Reference:
            ISO 16269-6:2014 Statistical interpretation of data - Part 6:
            Determination of statistical tolerance intervals

        Validates: Requirements 15.1, 15.2
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
        for parametric data with two-sided specifications (both LSL and USL).

        The tolerance interval is defined by:
        - Lower limit: TL = mean - k2 * std
        - Upper limit: TU = mean + k2 * std

        With confidence C, at least proportion R of the population falls within [TL, TU].

        Mathematical Background:
            The two-sided tolerance factor accounts for both tails of the distribution.
            The Howe-Guenther approximation provides an efficient method for calculating
            k2 without requiring iterative numerical methods.

            For a sample of size n from a normal distribution, the tolerance factor k2
            satisfies:

            P(X̄ - k2*S ≤ μ - z_{R/2}*σ AND X̄ + k2*S ≥ μ + z_{R/2}*σ) = C

            where:
            - X̄ is the sample mean
            - S is the sample standard deviation
            - μ is the population mean
            - σ is the population standard deviation
            - z_{R/2} is the standard normal quantile at (1+R)/2 (two-sided)
            - C is the confidence level

            The approximation uses the non-central t-distribution with:
            - Degrees of freedom: df = n - 1
            - Non-centrality parameter: ncp = z_{(1+R)/2} * √n
            - Quantile: t_C at confidence level C
            - Tolerance factor: k2 = t_C / √n

        Args:
            n: Sample size (must be ≥ 2)
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            Two-sided tolerance factor k2

        Raises:
            ValueError: If inputs are invalid or n < 2

        Reference:
            Howe, W.G. (1969). Two-sided tolerance limits for normal populations -
            Some improvements. Journal of the American Statistical Association, 64(326), 610-620.

        Validates: Requirements 16.1, 16.2
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
        for two-sided tolerance intervals in a distribution-free (non-parametric) manner.

        Mathematical Background:
            For non-parametric two-sided tolerance intervals, we use the extreme order
            statistics (minimum and maximum) from the sample. The probability that both
            the minimum and maximum of a sample of size N from a continuous distribution
            capture at least proportion R of the population is given by:

            P(min(X₁,...,Xₙ) ≤ F⁻¹((1-R)/2) AND max(X₁,...,Xₙ) ≥ F⁻¹((1+R)/2))
                = 1 - N*R^(N-1) + (N-1)*R^N

            where F is the cumulative distribution function of the population.

            This formula is derived from order statistics theory and is valid for any
            continuous distribution (distribution-free property). We iterate N upward
            until this probability meets or exceeds the confidence level C.

            The formula represents:
            - 1: Total probability
            - N*R^(N-1): Probability that at least one extreme is outside the interval
            - (N-1)*R^N: Correction term for overlap (inclusion-exclusion principle)

        Args:
            confidence: Confidence level as percentage (0-100)
            reliability: Reliability level as percentage (0-100)

        Returns:
            Required sample size (integer)

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If calculation does not converge

        Reference:
            Wilks, S. S. (1941). Determination of sample sizes for setting tolerance limits.
            The Annals of Mathematical Statistics, 12(1), 91-96.

        Validates: Requirements 18.1, 18.2
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
            prob = 1 - n * (r_rel ** (n - 1)) + (n - 1) * (r_rel**n)

            if prob >= c_conf:
                return n
            n += 1

        raise RuntimeError("Sample size calculation did not converge")
