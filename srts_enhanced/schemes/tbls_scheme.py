"""
TBLS (Threshold BLS) signature scheme.
Based on threshold_bls implementation with multi-curve support.
"""

from typing import List, Dict, Tuple, Any
import hashlib


class TBLS:
    """
    Threshold BLS signature scheme using BLS12-381 pairing-friendly curve.
    Supports threshold signing with Lagrange interpolation in the exponent.
    """
    
    def __init__(self, curve_name: str = "bls12-381", scheme_id: str = "tbls_v1"):
        from ..curves import get_curve
        self.curve = get_curve(curve_name)
        self.curve_name = curve_name
        self.scheme_id = scheme_id
        self.order = self.curve.get_order()
        self.G1 = self.curve.get_generator()
        
        # For BLS, we also need G2
        if curve_name == "bls12-381":
            from py_ecc.optimized_bls12_381 import G2
            self.G2 = G2
        else:
            self.G2 = None
    
    def _hash_to_G2(self, message: bytes) -> Any:
        """Hash message to G2 point."""
        if self.curve_name == "bls12-381":
            return self.curve.hash_to_G2(message, self.scheme_id.encode())
        raise NotImplementedError(f"hash_to_G2 not implemented for {self.curve_name}")
    
    def keygen(self, n: int, t: int, secret: int = None) -> Dict:
        """Generate threshold BLS keys using trusted dealer."""
        from ..utils.polynomial import Polynomial
        
        if secret is None:
            secret = self.curve.generate_private_key()
        
        poly = Polynomial(t, self.order, secret)
        shares = [(i + 1, poly.evaluate(i + 1)) for i in range(n)]
        
        # Public key in G1: pk = sk * G1
        pk = self.curve.multiply_point(self.G1, secret)
        
        # Public commitments for verification
        public_commits = []
        for coef in poly.get_coefficients():
            commit = self.curve.multiply_point(self.G1, coef)
            public_commits.append(commit)
        
        return {
            "n": n,
            "t": t,
            "shares": shares,
            "public_key": self.curve.serialize_point(pk).hex(),
            "public_commits": [
                self.curve.serialize_point(P).hex() 
                for P in public_commits
            ],
            "scheme": "tbls",
            "curve": self.curve_name,
        }
    
    def partial_sign(self, message: bytes, share: int, participant_id: int) -> Dict:
        """Generate partial BLS signature."""
        # Hash message to G2
        H = self._hash_to_G2(message)
        
        # Partial signature: sigma_i = share * H(m)
        sigma = self.curve.multiply_G2(H, share)
        
        return {
            "participant_id": participant_id,
            "signature": self.curve.serialize_point(sigma).hex(),
            "message_hash": hashlib.sha256(message).hexdigest(),
            "is_G2": True,  # Mark this as G2 point for deserialization
        }
    
    def aggregate(self, partial_sigs: List[Dict], message: bytes,
                  public_key: str) -> Dict:
        """
        Aggregate partial BLS signatures using Lagrange interpolation in exponent.
        
        Args:
            partial_sigs: List of partial signatures with participant IDs
            message: Original message
            public_key: Group public key (hex)
        
        Returns:
            Aggregated signature
        """
        if len(partial_sigs) < 1:
            raise ValueError("Need at least one partial signature")
        
        # Extract shares and signatures
        shares_data = []
        sig_points = []
        
        for psig in partial_sigs:
            pid = psig["participant_id"]
            sig_hex = psig["signature"]
            is_G2 = psig.get("is_G2", False)
            sig_point = self.curve.deserialize_point(bytes.fromhex(sig_hex), is_G2=is_G2)
            shares_data.append((pid, sig_point))
            sig_points.append(sig_point)
        
        # Interpolate in the exponent to get g2^P(0) where P(0) = secret
        # This gives us the full signature sigma = secret * H(m)
        aggregated_sig = self._interpolate_at_zero_g2(shares_data)
        
        # Verify aggregation
        pk_point = self.curve.deserialize_point(bytes.fromhex(public_key))
        valid = self.verify(message, aggregated_sig, pk_point)
        
        return {
            "signature": self.curve.serialize_point(aggregated_sig).hex(),
            "valid": valid,
            "partial_count": len(partial_sigs),
        }
    
    def _interpolate_at_zero_g2(self, shares: List[Tuple[int, Any]]) -> Any:
        """
        Lagrange interpolation in G2 exponent.
        Computes sum_i(lambda_i * sigma_i) where lambda_i are Lagrange coefficients.
        """
        x_values = [s[0] for s in shares]
        result = None
        
        for i, (xi, sigma_i) in enumerate(shares):
            # Compute Lagrange coefficient at x=0
            lam = self._lagrange_coefficient(i, 0, x_values)
            
            # Scale signature by lambda
            scaled = self.curve.multiply_G2(sigma_i, lam)
            
            if result is None:
                result = scaled
            else:
                result = self.curve.add_points(result, scaled)
        
        return result
    
    def _lagrange_coefficient(self, i: int, x: int, x_values: List[int]) -> int:
        """Compute Lagrange basis polynomial coefficient."""
        numerator = 1
        denominator = 1
        
        xi = x_values[i]
        for j, xj in enumerate(x_values):
            if i != j:
                numerator = (numerator * (x - xj)) % self.order
                denominator = (denominator * (xi - xj)) % self.order
        
        denom_inv = pow(denominator, -1, self.order)
        return (numerator * denom_inv) % self.order
    
    def verify(self, message: bytes, signature: Any, public_key: Any) -> bool:
        """
        Verify BLS signature using pairing.
        
        e(sigma, G1) == e(H(m), pk)
        
        Or equivalently: e(sigma, G1) / e(H(m), pk) == 1
        """
        # Deserialize if needed
        if isinstance(signature, str):
            sigma = self.curve.deserialize_point(bytes.fromhex(signature))
        else:
            sigma = signature
        
        if isinstance(public_key, str):
            pk = self.curve.deserialize_point(bytes.fromhex(public_key))
        else:
            pk = public_key
        
        # Hash message to G2
        H = self._hash_to_G2(message)
        
        # Pairing check: e(sigma, G1) == e(H, pk)
        left = self.curve.pairing(sigma, self.G1)
        right = self.curve.pairing(H, pk)
        
        return left == right
    
    def aggregate_public_keys(self, pub_keys: List[Tuple[int, str]], 
                               threshold: int) -> str:
        """
        Aggregate multiple public keys into combined threshold public key.
        Uses Lagrange interpolation to combine.
        """
        points = []
        for idx, pk_hex in pub_keys:
            pk = self.curve.deserialize_point(bytes.fromhex(pk_hex))
            points.append((idx, pk))
        
        combined = self._interpolate_at_zero_g1(points)
        return self.curve.serialize_point(combined).hex()
    
    def _interpolate_at_zero_g1(self, shares: List[Tuple[int, Any]]) -> Any:
        """Lagrange interpolation in G1 exponent."""
        x_values = [s[0] for s in shares]
        result = None
        
        for i, (xi, Pi) in enumerate(shares):
            lam = self._lagrange_coefficient(i, 0, x_values)
            scaled = self.curve.multiply_point(Pi, lam)
            
            if result is None:
                result = scaled
            else:
                result = self.curve.add_points(result, scaled)
        
        return result
    
    def verify_partial_signature(self, partial_sig: Dict, message: bytes,
                                  public_share: str, participant_id: int) -> bool:
        """Verify a single partial signature."""
        sig_hex = partial_sig["signature"]
        sigma = self.curve.deserialize_point(bytes.fromhex(sig_hex))
        
        pk_share = self.curve.deserialize_point(bytes.fromhex(public_share))
        H = self._hash_to_G2(message)
        
        # Check: e(sigma, G1) == e(H, pk_share)
        left = self.curve.pairing(sigma, self.G1)
        right = self.curve.pairing(H, pk_share)
        
        return left == right
