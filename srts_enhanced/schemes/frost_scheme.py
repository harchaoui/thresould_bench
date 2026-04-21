"""
FROST (Flexible Round-Optimized Schnorr Threshold) signature scheme.
Based on pyfrost implementation with enhancements.
"""

from typing import List, Dict, Tuple, Any
import hashlib
import json


class FROST:
    """
    FROST threshold Schnorr signature scheme.
    Two-round signing with presignature optimization.
    """
    
    def __init__(self, curve_name: str = "secp256k1", scheme_id: str = "frost_v1"):
        from ..curves import get_curve
        self.curve = get_curve(curve_name)
        self.curve_name = curve_name
        self.scheme_id = scheme_id
        self.order = self.curve.get_order()
        self.G = self.curve.get_generator()
        
        self.nonce_storage = {}
    
    def _tagged_hash(self, tag: str, *data_parts: bytes) -> bytes:
        h = hashlib.sha256(f"{self.scheme_id}:{tag}".encode()).digest()
        hasher = hashlib.sha256(h + h)
        for part in data_parts:
            hasher.update(part)
        return hasher.digest()
    
    def keygen(self, n: int, t: int, secret: int = None) -> Dict:
        """Generate threshold keys using trusted dealer."""
        from ..utils.polynomial import Polynomial
        
        if secret is None:
            secret = self.curve.generate_private_key()
        
        poly = Polynomial(t, self.order, secret)
        shares = [(i + 1, poly.evaluate(i + 1)) for i in range(n)]
        
        pk = self.curve.multiply_point(self.G, secret)
        
        public_commits = []
        for coef in poly.get_coefficients():
            commit = self.curve.multiply_point(self.G, coef)
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
            "scheme": "frost",
            "curve": self.curve_name,
        }
    
    def generate_nonces(self, participant_id: int, count: int = 10) -> Dict:
        """Generate nonce pairs for FROST signing."""
        nonces_public = []
        nonces_private = []
        
        for _ in range(count):
            d = self.curve.generate_private_key()
            e = self.curve.generate_private_key()
            
            D = self.curve.public_key_from_private(d)
            E = self.curve.public_key_from_private(e)
            
            nonces_public.append({
                "id": participant_id,
                "D": self.curve.serialize_point(D).hex(),
                "E": self.curve.serialize_point(E).hex(),
            })
            
            nonces_private.append({
                "d": d,
                "e": e,
            })
        
        return {
            "participant_id": participant_id,
            "public_nonces": nonces_public,
            "private_nonces": nonces_private,
        }
    
    def presign(self, message: bytes, participants: List[int]) -> Dict:
        """Round 1 of FROST: Generate and exchange nonces."""
        all_nonces = {}
        
        for pid in participants:
            nonce_data = self.generate_nonces(pid, count=1)
            all_nonces[pid] = nonce_data
        
        return {
            "message": message,
            "participants": participants,
            "nonces": all_nonces,
        }
    
    def _compute_challenge(self, R: Any, pk: Any, message: bytes) -> int:
        """Compute Schnorr challenge c = H(R, PK, m)."""
        c_hash = self._tagged_hash("challenge",
                                    self.curve.serialize_point(R),
                                    self.curve.serialize_point(pk),
                                    message)
        return int.from_bytes(c_hash, 'big') % self.order
    
    def _compute_rho(self, participant_id: int, message: bytes,
                     all_nonces: Dict, index: int = 0) -> int:
        """Compute binding value rho_i."""
        nonce_data = b""
        for pid in sorted(all_nonces.keys()):
            pn = all_nonces[pid]["public_nonces"][index]
            nonce_data += pid.to_bytes(8, 'big')
            nonce_data += bytes.fromhex(pn["D"])
            nonce_data += bytes.fromhex(pn["E"])
        
        h_input = (
            participant_id.to_bytes(8, 'big') +
            message +
            nonce_data
        )
        
        h = self._tagged_hash("rho", h_input)
        return int.from_bytes(h, 'big') % self.order
    
    def sign(self, message: bytes, share: int, participant_id: int,
             presign_data: Dict, nonce_index: int = 0,
             lagrange_coef: int = None) -> Dict:
        """Round 2 of FROST: Generate partial signature."""
        all_nonces = presign_data["nonces"]
        
        if participant_id not in all_nonces:
            raise ValueError(f"Participant {participant_id} not in presign data")
        
        my_nonces_priv = all_nonces[participant_id]["private_nonces"][nonce_index]
        my_nonces_pub = all_nonces[participant_id]["public_nonces"][nonce_index]
        
        d = my_nonces_priv["d"]
        e = my_nonces_priv["e"]
        
        # Compute rho
        rho = self._compute_rho(participant_id, message, all_nonces, nonce_index)
        
        # Compute personal nonce R_i = D_i + rho_i * E_i
        Di = self.curve.deserialize_point(bytes.fromhex(my_nonces_pub["D"]))
        Ei = self.curve.deserialize_point(bytes.fromhex(my_nonces_pub["E"]))
        Ri = self.curve.add_points(Di, self.curve.multiply_point(Ei, rho))
        
        # Compute aggregated R
        R_agg = None
        for pid, nonce_data in all_nonces.items():
            pub = nonce_data["public_nonces"][nonce_index]
            rho_j = self._compute_rho(pid, message, all_nonces, nonce_index)
            Dj = self.curve.deserialize_point(bytes.fromhex(pub["D"]))
            Ej = self.curve.deserialize_point(bytes.fromhex(pub["E"]))
            Rj = self.curve.add_points(Dj, self.curve.multiply_point(Ej, rho_j))
            if R_agg is None:
                R_agg = Rj
            else:
                R_agg = self.curve.add_points(R_agg, Rj)
        
        # Get public key
        pk_hex = presign_data.get("public_key", "")
        if pk_hex:
            pk = self.curve.deserialize_point(bytes.fromhex(pk_hex))
        else:
            pk = self.G
        
        # Compute challenge
        c = self._compute_challenge(R_agg, pk, message)
        
        # Compute Lagrange coefficient
        if lagrange_coef is None:
            from ..utils.polynomial import lagrange_coefficient
            pids = list(all_nonces.keys())
            idx = pids.index(participant_id)
            lagrange_coef = lagrange_coefficient(idx, 0, pids, self.order)
        
        # Compute z_i = d_i + rho_i * e_i + c * lambda_i * share_i
        z = (d + rho * e + c * lagrange_coef * share) % self.order
        
        return {
            "participant_id": participant_id,
            "z": z,
            "R": self.curve.serialize_point(Ri).hex(),
            "c": c,
        }
    
    def aggregate(self, partial_sigs: List[Dict], presign_data: Dict) -> Dict:
        """Aggregate partial signatures into final signature."""
        if len(partial_sigs) == 0:
            raise ValueError("Need at least one partial signature")
        
        z_total = sum(psig["z"] for psig in partial_sigs) % self.order
        
        R_agg = None
        for psig in partial_sigs:
            R_i = self.curve.deserialize_point(bytes.fromhex(psig["R"]))
            if R_agg is None:
                R_agg = R_i
            else:
                R_agg = self.curve.add_points(R_agg, R_i)
        
        pk_hex = presign_data.get("public_key", "")
        if not pk_hex:
            raise ValueError("Public key required")
        pk = self.curve.deserialize_point(bytes.fromhex(pk_hex))
        
        message = presign_data.get("message", b"")
        c = self._compute_challenge(R_agg, pk, message)
        
        # Verify
        lhs = self.curve.multiply_point(self.G, z_total)
        rhs = self.curve.add_points(R_agg, self.curve.multiply_point(pk, c))
        
        return {
            "R": self.curve.serialize_point(R_agg).hex(),
            "z": z_total,
            "c": c,
            "valid": lhs == rhs,
        }
    
    def verify(self, message: bytes, signature: Dict, public_key: Any) -> bool:
        """Verify final signature."""
        if isinstance(public_key, str):
            pk = self.curve.deserialize_point(bytes.fromhex(public_key))
        else:
            pk = public_key
        
        R = self.curve.deserialize_point(bytes.fromhex(signature["R"]))
        z = signature["z"]
        
        c = self._compute_challenge(R, pk, message)
        
        if c != signature.get("c", c):
            return False
        
        lhs = self.curve.multiply_point(self.G, z)
        rhs = self.curve.add_points(R, self.curve.multiply_point(pk, c))
        
        return lhs == rhs
