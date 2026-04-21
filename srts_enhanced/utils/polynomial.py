"""
Utility functions for polynomial operations, Shamir sharing, and Lagrange interpolation.
Inspired by pyfrost crypto_utils.py
"""

from typing import List, Tuple, Dict, Any
import hashlib


class Polynomial:
    """
    Polynomial class for Shamir's Secret Sharing over a field.
    Works with both scalar fields and elliptic curve points.
    """
    
    def __init__(self, threshold: int, order: int, secret: int = None):
        """
        Initialize polynomial with random coefficients.
        
        Args:
            threshold: t value (degree + 1)
            order: Field order (curve order)
            secret: Optional secret (coefficient_0), otherwise random
        """
        self.threshold = threshold
        self.order = order
        self.coefficients = []
        
        if secret is not None:
            self.coefficients.append(secret % order)
        else:
            import random
            self.coefficients.append(random.randint(1, order - 1))
        
        # Generate remaining t-1 random coefficients
        import random
        while len(self.coefficients) < threshold:
            self.coefficients.append(random.randint(1, order - 1))
    
    def evaluate(self, x: int) -> int:
        """Evaluate polynomial at point x using Horner's method."""
        result = 0
        for i, coef in enumerate(self.coefficients):
            result = (result + coef * pow(x, i, self.order)) % self.order
        return result
    
    def get_coefficients(self) -> List[int]:
        """Return list of coefficients."""
        return self.coefficients.copy()


def lagrange_coefficient(i, x: int, x_values: List[int], order: int) -> int:
    """
    Compute Lagrange basis polynomial coefficient at point x.
    
    λ_i(x) = ∏_{j≠i} (x - x_j) / (x_i - x_j)
    
    Args:
        i: Index in the x_values list (0-based)
        x: Point to evaluate at
        x_values: List of x-values (participant IDs)
        order: Field order
    
    Returns:
        Lagrange coefficient
    """
    numerator = 1
    denominator = 1
    
    # i is the index, get the actual x-value
    xi = x_values[i]
    
    for j, xj in enumerate(x_values):
        if i != j:  # j != i means we skip when indices match
            numerator = (numerator * (x - xj)) % order
            denominator = (denominator * (xi - xj)) % order
    
    # Modular inverse
    denom_inv = pow(denominator, -1, order)
    return (numerator * denom_inv) % order


def interpolate_at_zero(shares: List[Tuple[int, int]], order: int) -> int:
    """
    Reconstruct secret from shares using Lagrange interpolation at x=0.
    
    Args:
        shares: List of (index, value) tuples
        order: Field order
    
    Returns:
        Reconstructed secret
    """
    if len(shares) == 0:
        raise ValueError("Need at least one share")
    
    x_values = [s[0] for s in shares]
    secret = 0
    
    for i, (xi, yi) in enumerate(shares):
        lam = lagrange_coefficient(i, 0, x_values, order)
        secret = (secret + lam * yi) % order
    
    return secret


def interpolate_at_point(shares: List[Tuple[int, int]], x: int, order: int) -> int:
    """
    Interpolate polynomial at arbitrary point x.
    
    Args:
        shares: List of (index, value) tuples
        x: Point to evaluate at
        order: Field order
    
    Returns:
        Polynomial value at x
    """
    x_values = [s[0] for s in shares]
    result = 0
    
    for i, (xi, yi) in enumerate(shares):
        lam = lagrange_coefficient(i, x, x_values, order)
        result = (result + lam * yi) % order
    
    return result


def interpolate_points_at_zero(shares: List[Tuple[int, Any]], curve) -> Any:
    """
    Lagrange interpolation in the exponent (for elliptic curve points).
    Computes g^P(0) from shares (i, g^P(i)).
    
    Args:
        shares: List of (index, point) tuples
        curve: CurveAdapter instance
    
    Returns:
        Interpolated point
    """
    if len(shares) == 0:
        raise ValueError("Need at least one share")
    
    x_values = [s[0] for s in shares]
    order = curve.get_order()
    result = None
    
    for i, (xi, Pi) in enumerate(shares):
        lam = lagrange_coefficient(i, 0, x_values, order)
        scaled = curve.multiply_point(Pi, lam)
        if result is None:
            result = scaled
        else:
            result = curve.add_points(result, scaled)
    
    return result


def generate_shares(n: int, t: int, secret: int, order: int) -> List[Tuple[int, int]]:
    """
    Generate n Shamir secret shares with threshold t.
    
    Args:
        n: Number of shares
        t: Threshold
        secret: Secret to share
        order: Field order
    
    Returns:
        List of (index, share_value) tuples
    """
    poly = Polynomial(t, order, secret)
    shares = [(i + 1, poly.evaluate(i + 1)) for i in range(n)]
    return shares


def verify_share(share: Tuple[int, int], public_poly: List[Any], curve) -> bool:
    """
    Verify a share against public polynomial commitments (Feldman VSS).
    
    Args:
        share: (index, value) tuple
        public_poly: List of g^{coeff_i} points
        curve: CurveAdapter instance
    
    Returns:
        True if share is valid
    """
    idx, val = share
    order = curve.get_order()
    
    # Compute g^share
    expected = curve.multiply_point(curve.get_generator(), val)
    
    # Compute ∏ (g^{a_i})^{idx^i}
    actual = None
    for i, commit in enumerate(public_poly):
        power = pow(idx, i, order)
        term = curve.multiply_point(commit, power)
        if actual is None:
            actual = term
        else:
            actual = curve.add_points(actual, term)
    
    return expected == actual


def tagged_hash(tag: str, data: bytes) -> bytes:
    """
    Compute tagged hash similar to BIP340/BTC taproot.
    H(tag) || H(tag) || data
    """
    tag_hash = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()


def hash_to_scalar(data: bytes, order: int) -> int:
    """Hash arbitrary data to a field element."""
    h = hashlib.sha256(data).digest()
    return int.from_bytes(h, 'big') % order
