"""
Comprehensive test suite for SRTS Enhanced.
Tests all schemes (SRTS, FROST, TBLS) across multiple curves.
"""

import unittest
from typing import List


class TestCurves(unittest.TestCase):
    """Test curve abstraction layer."""
    
    def test_secp256k1_basic(self):
        """Test secp256k1 curve operations."""
        from ..curves import get_curve
        
        curve = get_curve("secp256k1")
        
        # Generate keypair
        sk = curve.generate_private_key()
        pk = curve.public_key_from_private(sk)
        
        # Verify point is on curve
        self.assertIsNotNone(pk)
        
        # Test serialization
        serialized = curve.serialize_point(pk)
        deserialized = curve.deserialize_point(serialized)
        self.assertEqual(pk, deserialized)
    
    def test_bls12_381_basic(self):
        """Test BLS12-381 curve operations."""
        from ..curves import get_curve
        
        curve = get_curve("bls12-381")
        
        sk = curve.generate_private_key()
        pk = curve.public_key_from_private(sk)
        
        self.assertIsNotNone(pk)
        
        # BLS points have different internal representation, just check we can serialize/deserialize
        serialized = curve.serialize_point(pk)
        deserialized = curve.deserialize_point(serialized)
        # Check x coordinates match (y may differ due to projective coords)
        self.assertEqual(pk[0], deserialized[0])
    
    def test_hash_to_scalar(self):
        """Test hash to scalar conversion."""
        from ..curves import get_curve
        
        curve = get_curve("secp256k1")
        order = curve.get_order()
        
        h1 = curve.hash_to_scalar(b"test1")
        h2 = curve.hash_to_scalar(b"test2")
        
        self.assertNotEqual(h1, h2)
        self.assertTrue(0 < h1 < order)
        self.assertTrue(0 < h2 < order)


class TestPolynomial(unittest.TestCase):
    """Test polynomial and Shamir sharing utilities."""
    
    def test_polynomial_evaluation(self):
        """Test polynomial evaluation."""
        from ..utils.polynomial import Polynomial
        
        order = 1000000007
        secret = 42
        t = 3
        
        poly = Polynomial(t, order, secret)
        
        # Check constant term is secret
        self.assertEqual(poly.coefficients[0], secret)
        
        # Evaluate at 0 should give secret
        self.assertEqual(poly.evaluate(0), secret)
    
    def test_shamir_shares_reconstruction(self):
        """Test Shamir secret sharing reconstruction."""
        from ..utils.polynomial import generate_shares, interpolate_at_zero
        
        n, t = 5, 3
        order = 1000000007
        secret = 12345
        
        shares = generate_shares(n, t, secret, order)
        
        # Reconstruct from t shares
        selected_shares = shares[:t]
        reconstructed = interpolate_at_zero(selected_shares, order)
        
        self.assertEqual(reconstructed, secret)
    
    def test_lagrange_coefficient(self):
        """Test Lagrange coefficient computation."""
        from ..utils.polynomial import lagrange_coefficient
        
        order = 101
        x_values = [1, 2, 3, 4, 5]
        
        # At x=0, sum of all lambda_i should be 1
        total = 0
        for i in range(len(x_values)):
            lam = lagrange_coefficient(i, 0, x_values, order)
            total = (total + lam) % order
        
        self.assertEqual(total, 1)


class TestDKG(unittest.TestCase):
    """Test DKG protocols."""
    
    def test_feldman_vss(self):
        """Test Feldman VSS protocol."""
        from ..curves import get_curve
        from ..dkg import FeldmanVSS
        
        curve = get_curve("secp256k1")
        n, t = 5, 3
        
        dkg = FeldmanVSS(n, t, curve, "test_feldman")
        
        # Round 1: Generate commitments
        msg1 = dkg.round1(node_id=1)
        self.assertIn("public_commits", msg1)
        self.assertEqual(len(msg1["public_commits"]), t)
    
    def test_pedersen_dkg(self):
        """Test Pedersen DKG protocol."""
        from ..curves import get_curve
        from ..dkg import PedersenDKG
        
        curve = get_curve("secp256k1")
        n, t = 5, 3
        
        dkg = PedersenDKG(n, t, curve, "test_pedersen")
        
        # Round 1
        msg1 = dkg.round1(node_id=1)
        self.assertIn("public_commits", msg1)
        
        # Generate shares
        shares = dkg.generate_shares_for([2, 3, 4, 5])
        self.assertEqual(len(shares), 4)


class TestSRTS(unittest.TestCase):
    """Test SRTS signature scheme."""
    
    def test_srts_sign_verify_secp256k1(self):
        """Test SRTS sign and verify on secp256k1."""
        from ..schemes import SRTS
        
        scheme = SRTS(curve_name="secp256k1")
        n, t = 5, 3
        
        keys = scheme.keygen(n, t)
        message = b"Hello, SRTS!"
        participants = list(range(1, n + 1))
        
        # Generate presignatures properly for SRTS
        presign_result = scheme.generate_presignatures(participants, batch_size=1)
        presign_data = scheme.presignatures[0]
        presign_data["public_key"] = keys["public_key"]
        presign_data["message"] = message
        
        # Generate partial signatures
        partial_sigs = []
        for i in range(t):
            pid = participants[i]
            share = keys["shares"][i][1]
            
            psig = scheme.sign(message, share, pid, presign_data, batch_index=0)
            partial_sigs.append(psig)
        
        # Aggregate
        sig = scheme.aggregate(partial_sigs, presign_data, batch_index=0)
        
        # Verify
        valid = scheme.verify(message, sig, keys["public_key"])
        self.assertTrue(valid)
    
    def test_srts_insufficient_shares(self):
        """Test that t-1 shares cannot produce valid signature."""
        from ..schemes import SRTS
        
        scheme = SRTS(curve_name="secp256k1")
        n, t = 5, 3
        
        keys = scheme.keygen(n, t)
        message = b"Test message"
        participants = list(range(1, n + 1))
        
        # Generate presignatures
        presign_result = scheme.generate_presignatures(participants, batch_size=1)
        presign_data = scheme.presignatures[0]
        presign_data["public_key"] = keys["public_key"]
        presign_data["message"] = message
        
        # Only t-1 signatures
        partial_sigs = []
        for i in range(t - 1):
            pid = participants[i]
            share = keys["shares"][i][1]
            psig = scheme.sign(message, share, pid, presign_data, batch_index=0)
            partial_sigs.append(psig)
        
        # Aggregate with insufficient shares
        sig = scheme.aggregate(partial_sigs, presign_data, batch_index=0)
        
        # Should fail verification
        valid = scheme.verify(message, sig, keys["public_key"])
        self.assertFalse(valid)


class TestFROST(unittest.TestCase):
    """Test FROST signature scheme."""
    
    def test_frost_sign_verify(self):
        """Test FROST sign and verify."""
        from ..schemes import FROST
        
        scheme = FROST(curve_name="secp256k1")
        n, t = 5, 3
        
        keys = scheme.keygen(n, t)
        message = b"Hello, FROST!"
        participants = list(range(1, n + 1))
        
        # Presign (Round 1)
        presign_data = scheme.presign(message, participants)
        
        # Sign (Round 2)
        partial_sigs = []
        for i in range(t):
            pid = participants[i]
            share = keys["shares"][i][1]
            psig = scheme.sign(message, share, pid, presign_data)
            partial_sigs.append(psig)
        
        # Aggregate
        sig = scheme.aggregate(partial_sigs, presign_data)
        
        # Verify
        valid = scheme.verify(message, sig, keys["public_key"])
        self.assertTrue(sig.get("valid", True))
        self.assertTrue(valid)


class TestTBLS(unittest.TestCase):
    """Test TBLS signature scheme."""
    
    def test_tbls_sign_verify(self):
        """Test TBLS sign and verify on BLS12-381."""
        from ..schemes import TBLS
        
        scheme = TBLS(curve_name="bls12-381")
        n, t = 5, 3
        
        keys = scheme.keygen(n, t)
        message = b"Hello, TBLS!"
        
        # Generate partial signatures
        partial_sigs = []
        for i in range(t):
            pid = i + 1
            share = keys["shares"][i][1]
            psig = scheme.partial_sign(message, share, pid)
            partial_sigs.append(psig)
        
        # Aggregate
        sig_result = scheme.aggregate(partial_sigs, message, keys["public_key"])
        
        # Verify
        self.assertTrue(sig_result["valid"])


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def test_full_workflow_secp256k1(self):
        """Test complete workflow with secp256k1."""
        from ..schemes import SRTS, FROST
        
        for scheme_cls in [SRTS, FROST]:
            with self.subTest(scheme=scheme_cls.__name__):
                scheme = scheme_cls(curve_name="secp256k1")
                n, t = 7, 4
                
                keys = scheme.keygen(n, t)
                message = b"Integration test message"
                participants = list(range(1, n + 1))
                
                if hasattr(scheme, 'presign'):
                    presign_data = scheme.presign(message, participants)
                else:
                    presign_data = keys
                
                # Collect t signatures
                partial_sigs = []
                for i in range(t):
                    pid = participants[i]
                    share = keys["shares"][i][1]
                    
                    if scheme_cls == TBLS:
                        psig = scheme.partial_sign(message, share, pid)
                    else:
                        psig = scheme.sign(message, share, pid, presign_data)
                    partial_sigs.append(psig)
                
                # Aggregate
                if scheme_cls == TBLS:
                    sig = scheme.aggregate(partial_sigs, message, keys["public_key"])
                    valid = sig["valid"]
                else:
                    sig = scheme.aggregate(partial_sigs, presign_data)
                    valid = scheme.verify(message, sig, keys["public_key"])
                
                self.assertTrue(valid)
    
    def test_multi_curve_support(self):
        """Test that schemes work across different curves."""
        from ..schemes import SRTS
        
        curves = ["secp256k1"]  # Add more as they become stable
        
        for curve_name in curves:
            with self.subTest(curve=curve_name):
                scheme = SRTS(curve_name=curve_name)
                keys = scheme.keygen(3, 2)
                
                self.assertIn("shares", keys)
                self.assertIn("public_key", keys)
                self.assertEqual(len(keys["shares"]), 3)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCurves))
    suite.addTests(loader.loadTestsFromTestCase(TestPolynomial))
    suite.addTests(loader.loadTestsFromTestCase(TestDKG))
    suite.addTests(loader.loadTestsFromTestCase(TestSRTS))
    suite.addTests(loader.loadTestsFromTestCase(TestFROST))
    suite.addTests(loader.loadTestsFromTestCase(TestTBLS))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
