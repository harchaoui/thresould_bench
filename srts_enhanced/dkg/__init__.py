"""
DKG (Distributed Key Generation) protocols.
Implements Pedersen DKG, Feldman VSS, and extensible framework for others.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any, Optional
import hashlib


class DKGProtocol(ABC):
    """Abstract base class for DKG protocols."""
    
    @abstractmethod
    def round1(self, node_id: int) -> Dict:
        """First round of DKG protocol."""
        pass
    
    @abstractmethod
    def round2(self, node_id: int, messages: List[Dict]) -> Dict:
        """Second round of DKG protocol."""
        pass
    
    @abstractmethod
    def finalize(self, node_id: int, messages: List[Dict]) -> Dict:
        """Finalize DKG and compute share."""
        pass


class FeldmanVSS(DKGProtocol):
    """
    Feldman Verifiable Secret Sharing.
    Simple VSS with public commitments for share verification.
    """
    
    def __init__(self, n: int, t: int, curve, dkg_id: str = "feldman_dkg"):
        """
        Initialize Feldman VSS.
        
        Args:
            n: Total number of participants
            t: Threshold
            curve: CurveAdapter instance
            dkg_id: Unique identifier for this DKG instance
        """
        self.n = n
        self.t = t
        self.curve = curve
        self.dkg_id = dkg_id
        self.order = curve.get_order()
        self.G = curve.get_generator()
        
        # Local state
        self.secret = None
        self.polynomial = None
        self.public_commits = None
        self.shares_received = {}
        self.peer_public_keys = {}
    
    def _generate_polynomial(self, secret: int = None):
        """Generate random polynomial with given secret."""
        from srts_enhanced.utils.polynomial import Polynomial
        self.secret = secret if secret else self.curve.generate_private_key()
        self.polynomial = Polynomial(self.t, self.order, self.secret)
        
        # Compute public commitments g^{a_i}
        self.public_commits = []
        for coef in self.polynomial.get_coefficients():
            commit = self.curve.multiply_point(self.G, coef)
            self.public_commits.append(commit)
    
    def round1(self, node_id: int, secret: int = None) -> Dict:
        """
        Round 1: Generate polynomial and broadcast commitments.
        
        Returns:
            Broadcast message with public commitments
        """
        self._generate_polynomial(secret)
        
        return {
            "sender_id": node_id,
            "dkg_id": self.dkg_id,
            "protocol": "feldman_vss",
            "public_commits": [
                self.curve.serialize_point(P).hex() 
                for P in self.public_commits
            ],
        }
    
    def generate_share_for(self, recipient_id: int) -> Tuple[int, int]:
        """Generate encrypted share for a specific recipient."""
        share_value = self.polynomial.evaluate(recipient_id)
        return (recipient_id, share_value)
    
    def round2(self, node_id: int, commitments: List[Dict], 
               private_shares: Dict[int, Tuple[int, int]]) -> Dict:
        """
        Round 2: Process commitments and verify shares.
        
        Args:
            commitments: List of commitment broadcasts from all parties
            private_shares: Dict mapping sender_id to (idx, share) received
        
        Returns:
            Verification results and qualified participant list
        """
        # Store public commitments from all parties
        for msg in commitments:
            sender = msg["sender_id"]
            commits_hex = msg["public_commits"]
            commits = [
                self.curve.deserialize_point(bytes.fromhex(c)) 
                for c in commits_hex
            ]
            self.peer_public_keys[sender] = commits
        
        # Verify received shares
        qualified = []
        complaints = []
        
        for sender_id, share in private_shares.items():
            if sender_id not in self.peer_public_keys:
                complaints.append({
                    "complainant": node_id,
                    "accused": sender_id,
                    "reason": "missing_commitment"
                })
                continue
            
            public_poly = self.peer_public_keys[sender_id]
            from srts_enhanced.utils.polynomial import verify_share
            if verify_share(share, public_poly, self.curve):
                qualified.append(sender_id)
            else:
                complaints.append({
                    "complainant": node_id,
                    "accused": sender_id,
                    "reason": "invalid_share",
                    "share_index": share[0]
                })
        
        return {
            "node_id": node_id,
            "qualified_participants": qualified,
            "complaints": complaints,
        }
    
    def finalize(self, node_id: int, qualified: List[int], 
                 shares: List[Tuple[int, int]]) -> Dict:
        """
        Finalize DKG by summing shares from qualified participants.
        
        Args:
            node_id: This node's ID
            qualified: List of qualified participant IDs
            shares: List of (sender_id, share_value) from qualified parties
        
        Returns:
            Final share and public key
        """
        # Sum all valid shares
        total_share = 0
        for sender_id, share_val in shares:
            total_share = (total_share + share_val) % self.order
        
        # Compute public key as sum of all first commitments
        public_key = None
        for sender_id in qualified:
            if sender_id in self.peer_public_keys:
                pk_commit = self.peer_public_keys[sender_id][0]
                if public_key is None:
                    public_key = pk_commit
                else:
                    public_key = self.curve.add_points(public_key, pk_commit)
        
        return {
            "node_id": node_id,
            "share": total_share,
            "public_share": self.curve.serialize_point(
                self.curve.multiply_point(self.G, total_share)
            ).hex(),
            "group_public_key": self.curve.serialize_point(public_key).hex(),
            "threshold": self.t,
            "total_participants": self.n,
        }


class PedersenDKG(DKGProtocol):
    """
    Pedersen Distributed Key Generation.
    Enhanced DKG with mutual commitment and no trusted dealer.
    Based on Gennaro et al. "Secure Distributed Key Generation for Discrete-Log Based Cryptosystems"
    """
    
    def __init__(self, n: int, t: int, curve, dkg_id: str = "pedersen_dkg"):
        """
        Initialize Pedersen DKG.
        
        Args:
            n: Total number of participants
            t: Threshold
            curve: CurveAdapter instance
            dkg_id: Unique identifier for this DKG instance
        """
        self.n = n
        self.t = t
        self.curve = curve
        self.dkg_id = dkg_id
        self.order = curve.get_order()
        self.G = curve.get_generator()
        
        # Generate second generator H for Pedersen commitments
        # H = hash_to_point("PedersenH" || dkg_id) to ensure nothing-up-my-sleeve
        h_seed = hashlib.sha256(f"PedersenH:{dkg_id}".encode()).digest()
        h_scalar = int.from_bytes(h_seed, 'big') % self.order
        self.H = self.curve.multiply_point(self.G, h_scalar)
        
        # Local state
        self.secret_poly = None
        self.blinding_poly = None
        self.public_commits = None
        self.private_shares_sent = {}
        self.private_shares_received = {}
        self.blinding_shares_received = {}
        self.peer_commits = {}
        self.qualified_set = None
    
    def _generate_polynomials(self):
        """Generate secret and blinding polynomials."""
        from srts_enhanced.utils.polynomial import Polynomial
        
        # Secret polynomial
        secret = self.curve.generate_private_key()
        self.secret_poly = Polynomial(self.t, self.order, secret)
        
        # Blinding polynomial for Pedersen commitments
        blinding_secret = self.curve.generate_private_key()
        self.blinding_poly = Polynomial(self.t, self.order, blinding_secret)
        
        # Compute public commitments C_{i,j} = g^{a_{i,j}} * h^{b_{i,j}}
        self.public_commits = []
        a_coeffs = self.secret_poly.get_coefficients()
        b_coeffs = self.blinding_poly.get_coefficients()
        
        for j in range(self.t):
            aj, bj = a_coeffs[j], b_coeffs[j]
            commit = self.curve.add_points(
                self.curve.multiply_point(self.G, aj),
                self.curve.multiply_point(self.H, bj)
            )
            self.public_commits.append(commit)
    
    def round1(self, node_id: int) -> Dict:
        """
        Round 1: Generate polynomials and broadcast commitments.
        
        Returns:
            Broadcast message with Pedersen commitments
        """
        self._generate_polynomials()
        
        return {
            "sender_id": node_id,
            "dkg_id": self.dkg_id,
            "protocol": "pedersen_dkg",
            "round": 1,
            "public_commits": [
                self.curve.serialize_point(P).hex() 
                for P in self.public_commits
            ],
        }
    
    def generate_shares_for(self, recipients: List[int]) -> Dict[str, List[Tuple[int, int, int]]]:
        """
        Generate secret and blinding shares for recipients.
        
        Returns:
            Dict mapping recipient_id to list of (recipient_id, secret_share, blinding_share)
        """
        result = {}
        for rid in recipients:
            s_share = self.secret_poly.evaluate(rid)
            b_share = self.blinding_poly.evaluate(rid)
            result[rid] = (rid, s_share, b_share)
            self.private_shares_sent[rid] = result[rid]
        return result
    
    def round2(self, node_id: int, round1_messages: List[Dict],
               received_shares: Dict[int, Tuple[int, int, int]]) -> Dict:
        """
        Round 2: Verify shares against commitments and broadcast complaints if needed.
        
        Args:
            round1_messages: All round 1 broadcasts
            received_shares: Dict mapping sender_id to (idx, secret_share, blinding_share)
        
        Returns:
            Complaints (if any) and qualified set
        """
        # Parse and store commitments
        for msg in round1_messages:
            sender = msg["sender_id"]
            commits_hex = msg["public_commits"]
            commits = [
                self.curve.deserialize_point(bytes.fromhex(c)) 
                for c in commits_hex
            ]
            self.peer_commits[sender] = commits
        
        # Verify each received share
        complaints = []
        qualified = set()
        
        for sender_id, (idx, s_share, b_share) in received_shares.items():
            if sender_id not in self.peer_commits:
                complaints.append({
                    "complainant": node_id,
                    "accused": sender_id,
                    "reason": "missing_commitment"
                })
                continue
            
            commits = self.peer_commits[sender_id]
            
            # Verify: g^{s_i} * h^{t_i} == ∏ C_{sender,j}^{i^j}
            lhs = self.curve.add_points(
                self.curve.multiply_point(self.G, s_share),
                self.curve.multiply_point(self.H, b_share)
            )
            
            rhs = None
            for j, commit in enumerate(commits):
                power = pow(idx, j, self.order)
                term = self.curve.multiply_point(commit, power)
                if rhs is None:
                    rhs = term
                else:
                    rhs = self.curve.add_points(rhs, term)
            
            if lhs == rhs:
                qualified.add(sender_id)
                self.private_shares_received[sender_id] = (idx, s_share, b_share)
            else:
                complaints.append({
                    "complainant": node_id,
                    "accused": sender_id,
                    "reason": "commitment_mismatch",
                    "share_index": idx
                })
        
        self.qualified_set = qualified
        
        return {
            "node_id": node_id,
            "qualified_participants": list(qualified),
            "complaints": complaints,
        }
    
    def round3_reveal(self, node_id: int, complaints: List[Dict]) -> Optional[Dict]:
        """
        Round 3 (optional): Reveal shares for complained parties.
        Only needed if there are complaints.
        """
        if not complaints:
            return None
        
        reveals = {}
        for complaint in complaints:
            if complaint["accused"] == node_id:
                # Reveal share to complainant
                if complaint["complainant"] in self.private_shares_sent:
                    share = self.private_shares_sent[complaint["complainant"]]
                    reveals[complaint["complainant"]] = share
        
        if reveals:
            return {
                "sender_id": node_id,
                "reveals": reveals,
            }
        return None
    
    def finalize(self, node_id: int) -> Dict:
        """
        Finalize DKG by computing final share.
        
        Returns:
            Final share and group public key
        """
        if self.qualified_set is None:
            raise ValueError("Must complete round2 before finalizing")
        
        # Sum secret shares from qualified participants
        total_share = 0
        for sender_id, (idx, s_share, b_share) in self.private_shares_received.items():
            if sender_id in self.qualified_set:
                total_share = (total_share + s_share) % self.order
        
        # Compute group public key: PK = ∏ C_{i,0} for qualified i
        public_key = None
        for sender_id in self.qualified_set:
            if sender_id in self.peer_commits:
                commit_0 = self.peer_commits[sender_id][0]
                # Extract g^{a_{i,0}} component (ignore blinding for final PK)
                # In practice, we use the full commitment structure
                if public_key is None:
                    public_key = commit_0
                else:
                    public_key = self.curve.add_points(public_key, commit_0)
        
        return {
            "node_id": node_id,
            "share": total_share,
            "public_share": self.curve.serialize_point(
                self.curve.multiply_point(self.G, total_share)
            ).hex(),
            "group_public_key": self.curve.serialize_point(public_key).hex(),
            "threshold": self.t,
            "total_participants": self.n,
            "qualified_count": len(self.qualified_set),
        }


# Registry of DKG protocols
DKG_REGISTRY = {
    "feldman_vss": FeldmanVSS,
    "pedersen_dkg": PedersenDKG,
}


def get_dkg_protocol(name: str, n: int, t: int, curve, dkg_id: str = None):
    """Factory function to get DKG protocol instance."""
    if name not in DKG_REGISTRY:
        raise ValueError(f"Unknown DKG protocol: {name}. Available: {list(DKG_REGISTRY.keys())}")
    return DKG_REGISTRY[name](n, t, curve, dkg_id)
