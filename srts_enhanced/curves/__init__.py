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
        """Serialize G1 or G2 point to bytes."""
        from py_ecc.optimized_bls12_381 import FQ, FQ2, normalize
        
        # Convert to affine coordinates using py_ecc's normalize
        if len(P) == 3:
            # Projective coordinates - convert to affine
            P_affine = normalize(P)
            # normalize returns (x, y) for affine (length 2)
            x, y = P_affine
        else:
            # Already affine (x, y)
            x, y = P
        
        if hasattr(x, 'n'):
            # G1 case: FQ elements with .n attribute
            x_bytes = x.n.to_bytes(48, 'big')
            y_bytes = y.n.to_bytes(48, 'big')
        elif hasattr(x, 'coeffs'):
            # G2 case: FQ2 elements with coeffs tuple
            x_coeffs = x.coeffs
            y_coeffs = y.coeffs
            x_bytes = x_coeffs[0].to_bytes(48, 'big') + x_coeffs[1].to_bytes(48, 'big')
            y_bytes = y_coeffs[0].to_bytes(48, 'big') + y_coeffs[1].to_bytes(48, 'big')
        else:
            x_bytes = int(x).to_bytes(48, 'big')
            y_bytes = int(y).to_bytes(48, 'big')
        return x_bytes + y_bytes
    
    def deserialize_point(self, data: bytes, is_G2: bool = False):
        """Deserialize G1 or G2 point from bytes."""
        if is_G2 or len(data) == 192:
            # G2 point has FQ2 coordinates (each is c0 + c1*u where u^2 = non-residue)
            from py_ecc.optimized_bls12_381 import FQ2, FQ
            # Each coordinate is 96 bytes (two 48-byte FQ elements)
            x_c0 = int.from_bytes(data[:48], 'big')
            x_c1 = int.from_bytes(data[48:96], 'big')
            y_c0 = int.from_bytes(data[96:144], 'big')
            y_c1 = int.from_bytes(data[144:192], 'big')
            # IMPORTANT: z must be FQ2([1, 0]) for G2 points, not int or FQ
            return (FQ2([x_c0, x_c1]), FQ2([y_c0, y_c1]), FQ2([1, 0]))
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
    """Ristretto255 curve implementation using PyNaCl."""
    
    def __init__(self):
        # Using PyNaCl for proper ristretto255 support
        try:
            from nacl.bindings import (
                crypto_core_ed25519_scalar_add,
                crypto_core_ed25519_scalar_sub,
                crypto_core_ed25519_scalar_mul,
                crypto_core_ed25519_scalar_invert,
                crypto_core_ed25519_scalar_negate,
                crypto_scalarmult_ed25519_base_noclamp,
                crypto_scalarmult_ed25519_noclamp,
                crypto_core_ed25519_is_valid_point,
                crypto_core_ed25519_add,
                crypto_core_ed25519_sub,
            )
            self.crypto_core_ed25519_scalar_add = crypto_core_ed25519_scalar_add
            self.crypto_core_ed25519_scalar_sub = crypto_core_ed25519_scalar_sub
            self.crypto_core_ed25519_scalar_mul = crypto_core_ed25519_scalar_mul
            self.crypto_core_ed25519_scalar_invert = crypto_core_ed25519_scalar_invert
            self.crypto_core_ed25519_scalar_negate = crypto_core_ed25519_scalar_negate
            self.crypto_scalarmult_ed25519_base_noclamp = crypto_scalarmult_ed25519_base_noclamp
            self.crypto_scalarmult_ed25519_noclamp = crypto_scalarmult_ed25519_noclamp
            self.crypto_core_ed25519_is_valid_point = crypto_core_ed25519_is_valid_point
            self.crypto_core_ed25519_add = crypto_core_ed25519_add
            self.crypto_core_ed25519_sub = crypto_core_ed25519_sub
            self.use_pynacl = True
        except ImportError:
            self.use_pynacl = False
        
        # Order of ed25519 subgroup (ristretto255 uses this)
        self.order = 2**252 + 27742317777372353535851937790883648493
        self.p = 2**255 - 19
    
    def generate_private_key(self) -> int:
        import random
        return random.randint(1, self.order - 1)
    
    def public_key_from_private(self, sk: int):
        """Generate public key from private scalar using ristretto255."""
        if self.use_pynacl:
            # Convert scalar to 32-byte little-endian format
            sk_bytes = sk.to_bytes(32, 'little')
            # Use no-clamp scalar multiplication for proper group operation
            pk_bytes = self.crypto_scalarmult_ed25519_base_noclamp(sk_bytes)
            return pk_bytes
        else:
            # Fallback: return bytes placeholder
            raise RuntimeError("PyNaCl required for ristretto255 operations")
    
    def add_points(self, P, Q):
        """Add two ristretto255 points."""
        if self.use_pynacl:
            # P and Q are 32-byte compressed ristretto points
            return self.crypto_core_ed25519_add(P, Q)
        else:
            raise RuntimeError("PyNaCl required for ristretto255 operations")
    
    def multiply_point(self, P, scalar: int):
        """Multiply a ristretto255 point by a scalar."""
        if self.use_pynacl:
            # P is a 32-byte compressed point, scalar must be reduced mod order
            scalar_reduced = scalar % self.order
            scalar_bytes = scalar_reduced.to_bytes(32, 'little')
            return self.crypto_scalarmult_ed25519_noclamp(scalar_bytes, P)
        else:
            raise RuntimeError("PyNaCl required for ristretto255 operations")
    
    def hash_to_scalar(self, data: bytes) -> int:
        h = hashlib.sha512(data).digest()
        return int.from_bytes(h[:32], 'little') % self.order
    
    def serialize_point(self, P) -> bytes:
        """Serialize a ristretto255 point to 32 bytes."""
        if isinstance(P, bytes):
            if len(P) == 32:
                return P
            raise ValueError(f"Expected 32-byte ristretto point, got {len(P)} bytes")
        # If it's not bytes, it's an error - ristretto points should always be bytes
        raise TypeError(f"Ristretto point must be 32 bytes, got {type(P)}")
    
    def deserialize_point(self, data: bytes):
        """Deserialize a 32-byte ristretto255 point."""
        if len(data) != 32:
            raise ValueError(f"Expected 32 bytes for ristretto255 point, got {len(data)}")
        if self.use_pynacl:
            # Validate the point
            if not self.crypto_core_ed25519_is_valid_point(data):
                raise ValueError("Invalid ristretto255 point")
        return data
    
    def get_order(self) -> int:
        return self.order
    
    def get_generator(self):
        """Get the generator point of ristretto255 (base point)."""
        if self.use_pynacl:
            # Generator is 1 * base point
            one_bytes = (1).to_bytes(32, 'little')
            return self.crypto_scalarmult_ed25519_base_noclamp(one_bytes)
        else:
            raise RuntimeError("PyNaCl required for ristretto255 operations")


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
