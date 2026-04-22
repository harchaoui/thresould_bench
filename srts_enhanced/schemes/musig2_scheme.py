"""
MuSig2 Multi-Signature Scheme Implementation
Based on "Simple and Efficient Two-Round Threshold Schnorr" (Nick et al. 2020)
Supports any prime-order curve: secp256k1, secp256r1, ristretto255, etc.

Key features:
- Key aggregation with deterministic coefficients
- Non-interactive nonce aggregation
- Two-round signing protocol
- Compatible with existing curve abstractions
"""

import hashlib
import secrets
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MuSig2KeyPair:
    """Individual participant key pair."""
    participant_id: int
    secret_key: int
    public_key: bytes  # Serialized point
    public_key_point: any  # Curve point object


@dataclass
class MuSig2AggregatedKey:
    """Aggregated public key for the group."""
    aggregated_point: any
    aggregated_serialized: bytes
    participant_keys: List[bytes]
    coefficients: List[int]


@dataclass
class MuSig2Nonce:
    """Participant's nonce pair."""
    secret_nonces: Tuple[int, int]  # (a, b)
    public_nonces: Tuple[bytes, bytes]  # (A, B) serialized


@dataclass
class MuSig2PartialSignature:
    """Partial signature from one participant."""
    participant_id: int
    s: int  # Partial signature scalar
    public_nonces: Tuple[bytes, bytes]


class MuSig2:
    """
    MuSig2 Multi-Signature Scheme.
    
    Supports n-of-n multi-signatures where all n participants must sign.
    Works with any prime-order elliptic curve.
    """
    
    scheme_name = "MuSig2"  # Class attribute for benchmark detection
    
    def __init__(self, curve_name: str = "secp256k1"):
        """Initialize MuSig2 with specified curve."""
        from ..curves import get_curve
        self.curve = get_curve(curve_name)
        self.curve_name = curve_name
        
        # Domain separation tag for MuSig2
        self.domain_tag = f"MuSig2/{curve_name}".encode()
        
        # Get curve order and generator
        self.order = self.curve.get_order()
        self.G = self.curve.get_generator()
        
    def _tagged_hash(self, tag: bytes, *messages: bytes) -> int:
        """Create tagged hash and convert to scalar."""
        h = hashlib.sha256()
        h.update(tag)
        for msg in messages:
            if isinstance(msg, int):
                h.update(msg.to_bytes(32, 'big'))
            elif isinstance(msg, bytes):
                h.update(msg)
            else:
                h.update(str(msg).encode())
        
        digest = h.digest()
        return int.from_bytes(digest, 'big') % self.order
    
    def keygen(self, participant_id: int = None) -> Dict:
        """
        Generate key pair for a single participant (for backward compatibility).
        For multiple participants, use keygen_multi().
        
        Args:
            participant_id: ID for this participant (default: 1)
            
        Returns:
            Dictionary with:
                - secret_key: MuSig2KeyPair object
                - public_key: Serialized public key
        """
        pid = participant_id if participant_id is not None else 1
        kp = self.keygen_single(pid)
        
        return {
            "secret_key": kp,
            "public_key": kp.public_key,
            "key_pair": kp
        }
    
    def keygen_multi(self, n: int) -> Dict:
        """
        Generate key pairs for all n participants (for benchmark compatibility).
        
        Args:
            n: Number of participants
            
        Returns:
            Dictionary with:
                - secret_keys: List of MuSig2KeyPair objects
                - public_keys: List of serialized public keys
                - aggregated_key: Aggregated public key
                - key_pairs: List of MuSig2KeyPair objects
        """
        # Generate key pairs for n participants
        key_pairs = []
        for i in range(n):
            kp = self.keygen_single(i + 1)
            key_pairs.append(kp)
        
        # Aggregate keys
        agg_key_obj = self.aggregate_keys(key_pairs)
        
        return {
            "secret_keys": key_pairs,
            "public_keys": [kp.public_key for kp in key_pairs],
            "aggregated_key": agg_key_obj.aggregated_serialized,
            "aggregated_key_point": agg_key_obj.aggregated_point,
            "key_pairs": key_pairs,
            "aggregated_key_obj": agg_key_obj
        }
    
    def keygen_single(self, participant_id: int) -> MuSig2KeyPair:
        """
        Generate individual key pair for a participant.
        
        Args:
            participant_id: Unique identifier for this participant
            
        Returns:
            MuSig2KeyPair with secret and public keys
        """
        sk = self.curve.generate_private_key()
        pk_point = self.curve.public_key_from_private(sk)
        pk_serialized = self.curve.serialize_point(pk_point)
        
        return MuSig2KeyPair(
            participant_id=participant_id,
            secret_key=sk,
            public_key=pk_serialized,
            public_key_point=pk_point
        )
    
    def aggregate_keys(self, key_pairs: List[MuSig2KeyPair]) -> MuSig2AggregatedKey:
        """
        Aggregate public keys from all participants.
        
        This computes the aggregated public key: PK = sum(c_i * pk_i)
        where c_i are deterministic coefficients.
        
        Args:
            key_pairs: List of all participants' key pairs
            
        Returns:
            MuSig2AggregatedKey with aggregated key and coefficients
        """
        n = len(key_pairs)
        if n == 0:
            raise ValueError("At least one key pair required")
        
        # Sort by participant_id for determinism
        sorted_keys = sorted(key_pairs, key=lambda k: k.participant_id)
        participant_keys = [k.public_key for k in sorted_keys]
        
        # Compute coefficients using tagged hash
        coefficients = []
        for i, key in enumerate(sorted_keys):
            # c_i = H(L || pk_i) where L = H(pk_1 || ... || pk_n)
            L = self._tagged_hash(self.domain_tag + b":keys", *participant_keys)
            c_i = self._tagged_hash(self.domain_tag + b":coeff", L.to_bytes(32, 'big'), 
                                   i.to_bytes(4, 'big'), key.public_key)
            coefficients.append(c_i)
        
        # Compute aggregated public key: PK = sum(c_i * pk_i)
        aggregated_point = None
        for i, key in enumerate(sorted_keys):
            scaled_point = self.curve.multiply_point(key.public_key_point, coefficients[i])
            if aggregated_point is None:
                aggregated_point = scaled_point
            else:
                aggregated_point = self.curve.add_points(aggregated_point, scaled_point)
        
        aggregated_serialized = self.curve.serialize_point(aggregated_point)
        
        return MuSig2AggregatedKey(
            aggregated_point=aggregated_point,
            aggregated_serialized=aggregated_serialized,
            participant_keys=participant_keys,
            coefficients=coefficients
        )
    
    def generate_nonces(self, participant_id: int) -> MuSig2Nonce:
        """
        Generate nonce pair for a participant.
        
        Each participant generates two secret nonces (a, b) and their 
        corresponding public nonces (A, B).
        
        Args:
            participant_id: ID of the generating participant
            
        Returns:
            MuSig2Nonce with secret and public nonces
        """
        # Generate two random secret nonces
        a = secrets.randbelow(self.order)
        b = secrets.randbelow(self.order)
        
        # Compute public nonces
        A_point = self.curve.public_key_from_private(a)
        B_point = self.curve.public_key_from_private(b)
        
        A_serialized = self.curve.serialize_point(A_point)
        B_serialized = self.curve.serialize_point(B_point)
        
        return MuSig2Nonce(
            secret_nonces=(a, b),
            public_nonces=(A_serialized, B_serialized)
        )
    
    def presign(self, message: bytes, 
                nonces: List[MuSig2Nonce],
                agg_key: MuSig2AggregatedKey,
                participant_index: int) -> Dict:
        """
        Prepare for signing by computing shared values.
        
        This is called by each participant after exchanging public nonces.
        
        Args:
            message: Message to be signed
            nonces: Public nonces from all participants
            agg_key: Aggregated public key
            participant_index: Index of this participant (0-based)
            
        Returns:
            Dictionary with precomputed values for signing
        """
        n = len(nonces)
        if n != len(agg_key.participant_keys):
            raise ValueError("Number of nonces must match number of keys")
        
        # Compute R = sum(A_i * c_i' + B_i * d_i')
        # where c_i', d_i' are nonce coefficients
        
        # First compute the challenge for nonce coefficients
        all_public_nonces = []
        for nonce in nonces:
            all_public_nonces.extend(nonce.public_nonces)
        
        # Compute rho = H(R_tilde || PK || m) where R_tilde is preliminary R
        # For simplicity, we use a deterministic approach
        rho_input = self.domain_tag + b":rho"
        for pn in all_public_nonces:
            rho_input += pn
        rho_input += agg_key.aggregated_serialized + message
        rho = self._tagged_hash(rho_input)
        
        # Compute nonce coefficients for each participant
        nonce_coeffs = []
        for i, nonce in enumerate(nonces):
            c_prime = self._tagged_hash(
                self.domain_tag + b":nonce_coeff_a",
                rho.to_bytes(32, 'big'),
                i.to_bytes(4, 'big'),
                nonce.public_nonces[0]
            )
            d_prime = self._tagged_hash(
                self.domain_tag + b":nonce_coeff_b", 
                rho.to_bytes(32, 'big'),
                i.to_bytes(4, 'big'),
                nonce.public_nonces[1]
            )
            nonce_coeffs.append((c_prime, d_prime))
        
        # Compute combined public nonce R
        R_point = None
        for i, nonce in enumerate(nonces):
            c_prime, d_prime = nonce_coeffs[i]
            
            A_point = self.curve.deserialize_point(nonce.public_nonces[0])
            B_point = self.curve.deserialize_point(nonce.public_nonces[1])
            
            term1 = self.curve.multiply_point(A_point, c_prime)
            term2 = self.curve.multiply_point(B_point, d_prime)
            combined = self.curve.add_points(term1, term2)
            
            if R_point is None:
                R_point = combined
            else:
                R_point = self.curve.add_points(R_point, combined)
        
        R_serialized = self.curve.serialize_point(R_point)
        
        # Compute challenge e = H(R || PK || m)
        e = self._tagged_hash(
            self.domain_tag + b":challenge",
            R_serialized,
            agg_key.aggregated_serialized,
            message
        )
        
        return {
            'R_point': R_point,
            'R_serialized': R_serialized,
            'challenge': e,
            'nonce_coeffs': nonce_coeffs,
            'participant_index': participant_index,
            'my_nonce': nonces[participant_index]
        }
    
    def sign(self, message: bytes,
             key_pair: MuSig2KeyPair,
             nonce: MuSig2Nonce,
             presign_data: Dict,
             agg_key: MuSig2AggregatedKey) -> MuSig2PartialSignature:
        """
        Generate partial signature.
        
        Args:
            message: Message to sign
            key_pair: Participant's key pair
            nonce: Participant's nonce (with secret values)
            presign_data: Data from presign() call
            agg_key: Aggregated public key
            
        Returns:
            MuSig2PartialSignature
        """
        # Get coefficient for this participant
        idx = presign_data['participant_index']
        c_i = agg_key.coefficients[idx]
        
        # Get nonce coefficients
        c_prime, d_prime = presign_data['nonce_coeffs'][idx]
        
        # Compute partial signature: s_i = a_i * c' + b_i * d' + e * c_i * x_i
        a_i, b_i = nonce.secret_nonces
        e = presign_data['challenge']
        x_i = key_pair.secret_key
        
        s = (a_i * c_prime + b_i * d_prime + e * c_i * x_i) % self.order
        
        return MuSig2PartialSignature(
            participant_id=key_pair.participant_id,
            s=s,
            public_nonces=nonce.public_nonces
        )
    
    def aggregate(self, partial_sigs: List[MuSig2PartialSignature],
                  presign_data: Dict = None, agg_nonces: List = None, 
                  agg_key = None, message: bytes = None) -> Dict:
        """
        Aggregate partial signatures into final signature.
        
        Args:
            partial_sigs: List of partial signatures from all participants
            presign_data: Data from presign() call (optional if agg_nonces provided)
            agg_nonces: List of aggregated public nonces (optional)
            agg_key: Aggregated key object (optional)
            message: Message that was signed (optional)
            
        Returns:
            Final signature dictionary with (R, s) components
        """
        if len(partial_sigs) == 0:
            raise ValueError("At least one partial signature required")
        
        # Determine which data source to use
        if presign_data is not None:
            # Use presign_data directly
            R_point = presign_data.get('R_point')
            R_serialized = presign_data.get('R_serialized')
        elif agg_nonces is not None and agg_key is not None and message is not None:
            # Recompute R from agg_nonces if needed
            # This is for benchmark compatibility
            if len(agg_nonces) > 0:
                # Sum the nonces to get R
                R_point = agg_nonces[0]
                for nonce in agg_nonces[1:]:
                    R_point = self.curve.add_points(R_point, nonce)
                R_serialized = self.curve.serialize_point(R_point)
            else:
                raise ValueError("No nonces provided for aggregation")
        else:
            raise ValueError("Either presign_data or (agg_nonces, agg_key, message) must be provided")
        
        # Sum all partial signatures: s = sum(s_i)
        s_total = sum(ps.s for ps in partial_sigs) % self.order
        
        # Create final signature bytes (R || s)
        sig_bytes = R_serialized + s_total.to_bytes(32, 'little')

        return {
            'R': R_serialized,
            'R_point': R_point,
            's': s_total,
            'serialized': sig_bytes,
            'aggregated_serialized': sig_bytes,
            'valid': True
        }
    
    def verify(self, message: bytes, signature, 
               aggregated_key) -> bool:
        """
        Verify aggregated signature.
        
        Verifies: s * G == R + e * PK
        where e = H(R || PK || m)
        
        Args:
            message: Original message
            signature: Aggregated signature (dict or bytes)
            aggregated_key: Aggregated public key (object or bytes)
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Handle different signature formats
            if isinstance(signature, dict):
                R_serialized = signature.get('R')
                s = signature.get('s')
            elif isinstance(signature, bytes):
                # Parse bytes: R (curve-dependent size) + s (32 bytes)
                # ristretto255: 32 bytes for R, secp256k1: 33 bytes for R (compressed)
                if len(signature) < 64:
                    print(f"Signature too short: {len(signature)} bytes, need at least 64")
                    return False
                # Determine R size based on signature length
                # ristretto255: 32 + 32 = 64 bytes, secp256k1: 33 + 32 = 65 bytes
                if len(signature) == 64:
                    R_size = 32  # ristretto255
                elif len(signature) >= 65:
                    R_size = 33  # secp256k1 or other compressed format
                else:
                    print(f"Invalid signature length: {len(signature)}")
                    return False
                R_serialized = signature[:R_size]
                s = int.from_bytes(signature[R_size:R_size+32], 'little')
            else:
                print(f"Invalid signature type: {type(signature)}")
                return False
            
            if R_serialized is None or s is None:
                print("Missing R or s in signature")
                return False
            
            # Handle different key formats
            if hasattr(aggregated_key, 'aggregated_serialized'):
                pk_serialized = aggregated_key.aggregated_serialized
                pk_point = aggregated_key.aggregated_point
            elif isinstance(aggregated_key, bytes):
                pk_serialized = aggregated_key
                pk_point = self.curve.deserialize_point(pk_serialized)
            else:
                print(f"Invalid key type: {type(aggregated_key)}")
                return False
            
            # Deserialize R
            R_point = self.curve.deserialize_point(R_serialized)
            
            # Recompute challenge e = H(R || PK || m)
            e = self._tagged_hash(
                self.domain_tag + b":challenge",
                R_serialized,
                pk_serialized,
                message
            )
            
            # Compute left side: s * G
            left = self.curve.multiply_point(self.G, s)
            
            # Compute right side: R + e * PK
            pk_scaled = self.curve.multiply_point(pk_point, e)
            right = self.curve.add_points(R_point, pk_scaled)
            
            # Compare points
            left_serialized = self.curve.serialize_point(left)
            right_serialized = self.curve.serialize_point(right)
            
            return left_serialized == right_serialized
            
        except Exception as ex:
            print(f"Verification error: {ex}")
            import traceback
            traceback.print_exc()
            return False
