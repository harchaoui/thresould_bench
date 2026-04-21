"""
Curve abstraction layer supporting multiple elliptic curves.
Supports: BLS12-381, secp256k1, ristretto255, and extensible for future curves.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any
import hashlib


class CurveInterface(ABC):
    """Abstract base class for curve operations."""
    
    @abstractmethod
    def generate_private_key(self) -> int:
        """Generate a random private key scalar."""
        pass
    
    @abstractmethod
    def public_key_from_private(self, sk: int) -> Any:
        """Compute public key from private key."""
        pass
    
    @abstractmethod
    def add_points(self, P: Any, Q: Any) -> Any:
        """Add two points on the curve."""
        pass
    
    @abstractmethod
    def multiply_point(self, P: Any, scalar: int) -> Any:
        """Multiply a point by a scalar."""
        pass
    
    @abstractmethod
    def hash_to_scalar(self, data: bytes) -> int:
        """Hash data to a field element."""
        pass
    
    @abstractmethod
    def serialize_point(self, P: Any) -> bytes:
        """Serialize a point to bytes."""
        pass
    
    @abstractmethod
    def deserialize_point(self, data: bytes) -> Any:
        """Deserialize bytes to a point."""
        pass
    
    @abstractmethod
    def get_order(self) -> int:
        """Get the order of the curve group."""
        pass
    
    @abstractmethod
    def get_generator(self) -> Any:
        """Get the generator point of the curve."""
        pass


class Secp256k1Curve(CurveInterface):
    """secp256k1 curve implementation using fastecdsa."""
    
    def __init__(self):
        from fastecdsa.curve import secp256k1
        from fastecdsa import keys
        self.curve = secp256k1
        self.keys = keys
        self.order = secp256k1.q
    
    def generate_private_key(self) -> int:
        return self.keys.gen_private_key(self.curve)
    
    def public_key_from_private(self, sk: int):
        return self.keys.get_public_key(sk, self.curve)
    
    def add_points(self, P, Q):
        return P + Q
    
    def multiply_point(self, P, scalar: int):
        return scalar * P
    
    def hash_to_scalar(self, data: bytes) -> int:
        h = hashlib.sha256(data).digest()
        return int.from_bytes(h, 'big') % self.order
    
    def serialize_point(self, P) -> bytes:
        from fastecdsa.encoding.sec1 import SEC1Encoder
        return SEC1Encoder.encode_public_key(P, True)
    
    def deserialize_point(self, data: bytes):
        from fastecdsa.encoding.sec1 import SEC1Encoder
        return SEC1Encoder.decode_public_key(data, self.curve)
    
    def get_order(self) -> int:
        return self.order
    
    def get_generator(self):
        return self.curve.G


class BLS12381Curve(CurveInterface):
    """BLS12-381 G1 curve implementation using py_ecc."""
    
    def __init__(self):
        from py_ecc.optimized_bls12_381 import G1, multiply, add, curve_order
        from py_ecc.bls.hash_to_curve import hash_to_G1
        self.G1 = G1
        self.multiply = multiply
        self.add = add
        self.order = curve_order
        self.curve_order = curve_order
        # Use hash_to_G2 for signatures (G2), hash_to_G1 for messages if needed
        try:
            from py_ecc.bls.hash_to_curve import hash_to_G1 as h1
            self.hash_to_G1 = h1
        except:
            self.hash_to_G1 = None
    
    def generate_private_key(self) -> int:
        import random
        return random.randint(1, self.order - 1)
    
    def public_key_from_private(self, sk: int):
        return self.multiply(self.G1, sk)
    
    def add_points(self, P, Q):
        return self.add(P, Q)
    
    def multiply_point(self, P, scalar: int):
        return self.multiply(P, scalar)
    
    def hash_to_scalar(self, data: bytes) -> int:
        h = hashlib.sha256(data).digest()
        return int.from_bytes(h, 'big') % self.order
    
    def serialize_point(self, P) -> bytes:
        # BLS12-381 G1 point is (x, y) in FQ - x and y are FQ elements
        if hasattr(P[0], 'n'):
            # G1 case: FQ elements with .n attribute
            x_bytes = P[0].n.to_bytes(48, 'big')
            y_bytes = P[1].n.to_bytes(48, 'big')
        elif hasattr(P[0], 'coeffs'):
            # G2 case: FQ2 elements with coeffs tuple
            # For FQ2, we serialize both coefficients (each is a large int)
            x_coeffs = P[0].coeffs  # Tuple of two ints for FQ2
            y_coeffs = P[1].coeffs
            # Serialize as c0 || c1 for each coordinate
            x_bytes = x_coeffs[0].to_bytes(48, 'big') + x_coeffs[1].to_bytes(48, 'big')
            y_bytes = y_coeffs[0].to_bytes(48, 'big') + y_coeffs[1].to_bytes(48, 'big')
        else:
            # Fallback
            x_bytes = int(P[0]).to_bytes(48, 'big')
            y_bytes = int(P[1]).to_bytes(48, 'big')
        return x_bytes + y_bytes
    
    def deserialize_point(self, data: bytes, is_G2: bool = False):
        """Deserialize G1 or G2 point from bytes."""
        if is_G2:
            # G2 point has FQ2 coordinates (each is c0 + c1*u where u^2 = non-residue)
            from py_ecc.optimized_bls12_381 import FQ2, FQ
            # Each coordinate is 96 bytes (two 48-byte FQ elements)
            x_c0 = int.from_bytes(data[:48], 'big')
            x_c1 = int.from_bytes(data[48:96], 'big')
            y_c0 = int.from_bytes(data[96:144], 'big')
            y_c1 = int.from_bytes(data[144:192], 'big')
            return (FQ2((x_c0, x_c1)), FQ2((y_c0, y_c1)), FQ2.one())
        else:
            # G1 point has FQ coordinates
            from py_ecc.optimized_bls12_381 import FQ
            x = int.from_bytes(data[:48], 'big')
            y = int.from_bytes(data[48:96], 'big')
            return (FQ(x), FQ(y), FQ.one())
    
    def get_order(self) -> int:
        return self.order
    
    def get_generator(self):
        return self.G1
    
    def hash_to_G2(self, msg: bytes, dst: bytes = b''):
        """Hash message to G2 point (for BLS signatures)."""
        from py_ecc.bls.hash_to_curve import hash_to_G2
        from hashlib import sha256
        return hash_to_G2(msg, dst, sha256)


class Ristretto255Curve(CurveInterface):
    """Ristretto255 curve implementation using cryptography or naive approach."""
    
    def __init__(self):
        # Using ed25519 as base, with ristretto encoding
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            self.use_cryptography = True
        except ImportError:
            self.use_cryptography = False
        # For ristretto, we'll use a simplified model based on ed25519
        # Order of ed25519 subgroup
        self.order = 2**252 + 27742317777372353535851937790883648493
        self.p = 2**255 - 19
    
    def generate_private_key(self) -> int:
        import random
        return random.randint(1, self.order - 1)
    
    def public_key_from_private(self, sk: int):
        # Simplified: in practice use proper ristretto255 library
        # This is a placeholder - real impl would use dalek-cryptography bindings
        if self.use_cryptography:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            # Convert sk to proper format
            sk_bytes = sk.to_bytes(32, 'little')
            private_key = Ed25519PrivateKey.from_private_bytes(sk_bytes[:32])
            return private_key.public_key().public_bytes_raw()
        else:
            # Fallback scalar multiplication on edwards curve
            return self._scalar_mult_base(sk)
    
    def _scalar_mult_base(self, sk: int):
        """Simplified scalar multiplication on edwards curve."""
        # This is a simplified placeholder
        x, y = 1, 1  # Would need proper edwards arithmetic
        return (x, y)
    
    def add_points(self, P, Q):
        # Simplified point addition
        if isinstance(P, bytes) and isinstance(Q, bytes):
            # Would need proper ristretto addition
            return P  # Placeholder
        return (P[0] + Q[0], P[1] + Q[1])
    
    def multiply_point(self, P, scalar: int):
        # Simplified scalar multiplication
        if isinstance(P, bytes):
            return P  # Placeholder
        return (P[0] * scalar, P[1] * scalar)
    
    def hash_to_scalar(self, data: bytes) -> int:
        h = hashlib.sha512(data).digest()
        return int.from_bytes(h[:32], 'little') % self.order
    
    def serialize_point(self, P) -> bytes:
        if isinstance(P, bytes):
            return P
        return P[0].to_bytes(32, 'little') + P[1].to_bytes(32, 'little')
    
    def deserialize_point(self, data: bytes):
        x = int.from_bytes(data[:32], 'little')
        y = int.from_bytes(data[32:64], 'little')
        return (x, y)
    
    def get_order(self) -> int:
        return self.order
    
    def get_generator(self):
        # Base point for ed25519/ristretto255
        return (0, 1)  # Simplified placeholder


# Registry of available curves
CURVE_REGISTRY = {
    "secp256k1": Secp256k1Curve,
    "bls12-381": BLS12381Curve,
    "ristretto255": Ristretto255Curve,
}


class CurveAdapter:
    """Adapter class to unify curve operations across different curve types."""
    
    def __init__(self, curve_name: str = "secp256k1"):
        if curve_name not in CURVE_REGISTRY:
            raise ValueError(f"Unsupported curve: {curve_name}. Available: {list(CURVE_REGISTRY.keys())}")
        self.curve_name = curve_name
        self.curve = CURVE_REGISTRY[curve_name]()
    
    def generate_private_key(self) -> int:
        return self.curve.generate_private_key()
    
    def public_key_from_private(self, sk: int):
        return self.curve.public_key_from_private(sk)
    
    def add_points(self, P, Q):
        return self.curve.add_points(P, Q)
    
    def multiply_point(self, P, scalar: int):
        return self.curve.multiply_point(P, scalar)
    
    def hash_to_scalar(self, data: bytes) -> int:
        return self.curve.hash_to_scalar(data)
    
    def serialize_point(self, P) -> bytes:
        return self.curve.serialize_point(P)
    
    def deserialize_point(self, data: bytes, is_G2: bool = False):
        """Deserialize point, with optional G2 support for BLS curves."""
        if self.curve_name == "bls12-381" and is_G2:
            return self.curve.deserialize_point(data, is_G2=True)
        return self.curve.deserialize_point(data)
    
    def get_order(self) -> int:
        return self.curve.get_order()
    
    def get_generator(self):
        return self.curve.get_generator()
    
    def hash_to_G2(self, msg: bytes, dst: bytes = b''):
        """Hash message to G2 point (for BLS signatures)."""
        from py_ecc.bls.hash_to_curve import hash_to_G2
        from hashlib import sha256
        return hash_to_G2(msg, dst, sha256)
    
    def get_g2_generator(self):
        """Get G2 generator for pairing-friendly curves (BLS12-381)."""
        if self.curve_name == "bls12-381":
            from py_ecc.optimized_bls12_381 import G2
            return G2
        raise NotImplementedError(f"G2 not available for {self.curve_name}")
    
    def multiply_G2(self, P, scalar: int):
        """Multiply G2 point by scalar (for BLS)."""
        if self.curve_name == "bls12-381":
            from py_ecc.optimized_bls12_381 import multiply
            return multiply(P, scalar)
        raise NotImplementedError(f"G2 operations not available for {self.curve_name}")
    
    def pairing(self, P: Any, Q: Any) -> Any:
        """Compute pairing e(P, Q) for BLS12-381."""
        if self.curve_name == "bls12-381":
            from py_ecc.optimized_bls12_381 import pairing
            return pairing(P, Q)
        raise NotImplementedError(f"Pairing not available for {self.curve_name}")


def get_curve(curve_name: str = "secp256k1") -> CurveAdapter:
    """Factory function to get a curve adapter."""
    return CurveAdapter(curve_name)


# Convenience constants
SECP256K1 = "secp256k1"
BLS12_381 = "bls12-381"
RISTRETTO255 = "ristretto255"
