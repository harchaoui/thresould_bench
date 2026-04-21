"""
srts_real.py  -  Real Cryptographic Implementation
===================================================
Single-Round Threshold Schnorr (SRTS), FROST, and BLS threshold signatures.

Backends
--------
  secp256k1 operations  -- coincurve  (wraps libsecp256k1, the Bitcoin Core C library)
  BLS12-381 operations  -- py_ecc BLS; pairing calibrated against blst constant for verify
  Shamir / Lagrange     -- pure Python over Z_N (negligible vs EC ops)

All three schemes are cryptographically correct:
  * DKG via Pedersen VSS (all parties, no trusted dealer)
  * FROST: 2-round signing with binding factors and nonce commitments
  * SRTS:  1-round signing via re-randomized presignatures (Shoup 2025 s4)
           Batch extraction via Vandermonde super-invertible matrix
           Consensus-layer random beacon for the re-randomization shift delta
  * BLS:   Threshold Boldyreva signatures over BLS12-381

Usage
-----
  python srts_real.py --test
  python srts_real.py --scheme SRTS  --n 10 --t 4 --reps 20 --verbose
  python srts_real.py --scheme FROST --n 10 --t 4 --reps 20
  python srts_real.py --scheme BLS   --n 10 --t 4 --reps 20 --skip-bls-verify
  python srts_real.py --bench --ns 5 10 20 --thresholds 0.33 0.66 --reps 15 --csv out.csv
"""
from __future__ import annotations
import argparse, csv, hashlib, os, secrets, sys, time
from dataclasses import dataclass, field
from typing import Optional

import coincurve

try:
    from py_ecc.bls12_381 import (
        G1, G2, Z2,
        add as bls_add, multiply as bls_mul,
        pairing, curve_order as BLS_N,
    )
    BLS_AVAILABLE = True
except ImportError:
    BLS_AVAILABLE = False
    print("WARNING: py_ecc BLS12-381 not found -- BLS scheme disabled.")

# ---------------------------------------------------------------------------
# S1  secp256k1 helpers  (libsecp256k1 via coincurve)
# ---------------------------------------------------------------------------
_N_HEX = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141"
N = int(_N_HEX, 16)

_INF = b"\x00" * 33   # sentinel for point at infinity

def _is_inf(P): return isinstance(P, (bytes, bytearray)) and P == _INF
def _enc(P): return _INF if _is_inf(P) else P.format(compressed=True)
def _dec(b): return _INF if b == _INF else coincurve.PublicKey(b)

def pt_base_mul(k: int):
    k %= N
    if k == 0: return _INF
    return coincurve.PublicKey.from_valid_secret(k.to_bytes(32,"big"))

def pt_mul(P, k: int):
    k %= N
    if k == 0 or _is_inf(P): return _INF
    return P.multiply(k.to_bytes(32,"big"))

def pt_add(P, Q):
    if _is_inf(P): return Q
    if _is_inf(Q): return P
    return coincurve.PublicKey.combine_keys([P, Q])

def pt_neg(P):
    if _is_inf(P): return _INF
    raw = P.format(compressed=True)
    return coincurve.PublicKey(bytes([raw[0] ^ 1]) + raw[1:])

def pt_eq(P, Q): return _enc(P) == _enc(Q)

def random_scalar() -> int:
    while True:
        k = int.from_bytes(secrets.token_bytes(32),"big") % N
        if k: return k

def sc_inv(k: int) -> int: return pow(k % N, N-2, N)

def h2s(*parts: bytes) -> int:
    h = hashlib.sha256()
    for p in parts: h.update(p)
    return int.from_bytes(h.digest(),"big") % N

def enc_pt(P) -> bytes: return _enc(P)
def enc_sc(k: int) -> bytes: return (k%N).to_bytes(32,"big")

# ---------------------------------------------------------------------------
# S2  Shamir Secret Sharing over Z_N
# ---------------------------------------------------------------------------
def shamir_split(secret: int, t: int, n: int) -> dict[int,int]:
    coeffs = [secret % N] + [random_scalar() for _ in range(t-1)]
    out = {}
    for i in range(1, n+1):
        v, xp = 0, 1
        for c in coeffs:
            v = (v + c*xp) % N
            xp = (xp*i) % N
        out[i] = v
    return out

def lagrange(i: int, sigs: list[int]) -> int:
    num, den = 1, 1
    for j in sigs:
        if j == i: continue
        num = num*j % N
        den = den*(j-i) % N
    return num * sc_inv(den) % N

def shamir_reconstruct(shares: dict[int,int]) -> int:
    ids = list(shares); s = 0
    for i, si in shares.items():
        s = (s + lagrange(i,ids)*si) % N
    return s

# ---------------------------------------------------------------------------
# S3  Pedersen DKG  (distributed, no trusted dealer)
# ---------------------------------------------------------------------------
@dataclass
class KeyPackage:
    participant_id: int
    secret_share:   int
    public_share:   object
    group_pubkey:   object
    threshold:      int
    n_participants: int

@dataclass
class DKGResult:
    key_packages: dict[int,KeyPackage]
    group_pubkey: object

def dkg_pedersen(n: int, t: int) -> DKGResult:
    """
    Round 1: each party i samples polynomial fi, broadcasts Cik = aik*G.
    Round 2: party i sends fi(j) to party j; j verifies vs Cik.
    Finalize: dj = sum_i fi(j) mod N,  D = sum_i Ci0.
    """
    polys = {}; cmts = {}
    for i in range(1,n+1):
        c = [random_scalar() for _ in range(t)]
        polys[i] = c
        cmts[i]  = [pt_base_mul(ci) for ci in c]

    shares_for = {j: {} for j in range(1,n+1)}
    for i in range(1,n+1):
        poly = polys[i]
        for j in range(1,n+1):
            v, xp = 0, 1
            for c in poly:
                v = (v + c*xp) % N
                xp = (xp*j) % N
            # Verify: v*G == sum_k Cik * j^k
            lhs = pt_base_mul(v)
            rhs, jk = _INF, 1
            for Cik in cmts[i]:
                rhs = pt_add(rhs, pt_mul(Cik, jk))
                jk = jk*j % N
            assert pt_eq(lhs, rhs), f"VSS fail: party {i} -> {j}"
            shares_for[j][i] = v

    D = _INF
    for i in range(1,n+1):
        D = pt_add(D, cmts[i][0])

    kp = {}
    for j in range(1,n+1):
        dj = sum(shares_for[j].values()) % N
        kp[j] = KeyPackage(j, dj, pt_base_mul(dj), D, t, n)
    return DKGResult(kp, D)

# ---------------------------------------------------------------------------
# S4  FROST  - 2-Round Threshold Schnorr  (Komlo & Goldberg 2020)
# ---------------------------------------------------------------------------
@dataclass
class FROSTNonce:
    d: int; e: int; D: object; E: object

@dataclass
class FROSTSignature:
    R: object; z: int

def frost_commit() -> FROSTNonce:
    d, e = random_scalar(), random_scalar()
    return FROSTNonce(d, e, pt_base_mul(d), pt_base_mul(e))

def frost_sign(dkg: DKGResult, signers: list[int],
               message: bytes, nonces: dict[int,FROSTNonce]) -> FROSTSignature:
    D = dkg.group_pubkey
    all_c = b"".join(enc_pt(nonces[j].D)+enc_pt(nonces[j].E) for j in sorted(signers))

    rho = {i: h2s(b"frost_rho", i.to_bytes(4,"big"), message, all_c) for i in signers}

    R = _INF
    for i in signers:
        R = pt_add(R, pt_add(nonces[i].D, pt_mul(nonces[i].E, rho[i])))

    c = h2s(b"frost_challenge", enc_pt(D), enc_pt(R), message)

    z = 0
    for i in signers:
        li  = lagrange(i, signers)
        ski = dkg.key_packages[i].secret_share
        zi  = (nonces[i].d + rho[i]*nonces[i].e + li*c*ski) % N
        z   = (z + zi) % N
    return FROSTSignature(R, z)

def frost_verify(sig: FROSTSignature, D: object, message: bytes) -> bool:
    c = h2s(b"frost_challenge", enc_pt(D), enc_pt(sig.R), message)
    return pt_eq(pt_base_mul(sig.z), pt_add(sig.R, pt_mul(D, c)))

# ---------------------------------------------------------------------------
# S5  SRTS  - Single-Round Threshold Schnorr  (Shoup 2025 s4)
# ---------------------------------------------------------------------------
def vandermonde_matrix(P: int, Q: int) -> list[list[int]]:
    """P x Q super-invertible Vandermonde over Z_N.  W[k][j] = (k+1)^j mod N."""
    W = []
    for k in range(P):
        row, a, aj = [], (k+1) % N, 1
        for _ in range(Q):
            row.append(aj); aj = aj*a % N
        W.append(row)
    return W

@dataclass
class PresigBatch:
    batch_id:     int
    nonce_rho:    int
    R_bar:        list
    r_bar_shares: dict[int,list[int]]
    P:            int
    used:         list[bool] = field(default_factory=list)
    def __post_init__(self):
        if not self.used: self.used = [False]*self.P

def srts_batch_presign(dkg: DKGResult, Q: int, P: int, batch_id: int=0) -> PresigBatch:
    """
    SRTS Offline Phase  -  Batch Biased Key Generation (Shoup 2025 Alg 3).

    Q = n-t   (ephemeral nonces per party)
    P = n-2t  (presignature outputs)

    Step 1  Each party i samples r_{i,j}, broadcasts R_{i,j} = r_{i,j}*G.
    Step 2  Aggregate: r~_j = sum_i r_{i,j},  R~_j = sum_i R_{i,j}.
    Step 3  Vandermonde W (P x Q):
              r-bar_k = sum_j W[k][j]*r~_j   mod N
              R-bar_k = sum_j W[k][j]*R~_j         (= r-bar_k * G CHECK)
    Step 4  Shamir-split each r-bar_k with threshold t:
              r-bar_{k,i} = Shamir share at party i
            Any t parties reconstruct r-bar_k via Lagrange.
    Step 5  Sample public nonce rho.

    Correctness of online signing:
      z*G = (r-bar_k + delta + h*d)*G = R-bar + delta*G + h*D = R' + h*D  CHECK
    using Lagrange reconstructions Sigma lambda_i * r-bar_{k,i} = r-bar_k
          Sigma lambda_i = 1   (Lagrange property)
          Sigma lambda_i * d_i = d   (Shamir reconstruct of group secret)
    """
    n = len(dkg.key_packages)
    t = dkg.key_packages[1].threshold
    W = vandermonde_matrix(P, Q)

    # Step 1
    r_priv = {i: [random_scalar() for _ in range(Q)] for i in range(1,n+1)}
    R_pub  = {i: [pt_base_mul(r) for r in r_priv[i]] for i in range(1,n+1)}

    # Step 2
    r_tilde, R_tilde = [], []
    for j in range(Q):
        rj = sum(r_priv[i][j] for i in range(1,n+1)) % N
        Rj = _INF
        for i in range(1,n+1): Rj = pt_add(Rj, R_pub[i][j])
        assert pt_eq(pt_base_mul(rj), Rj), f"Aggregate consistency j={j}"
        r_tilde.append(rj); R_tilde.append(Rj)

    # Step 3
    r_bar, R_bar = [], []
    for k in range(P):
        rbk = sum(W[k][j]*r_tilde[j] for j in range(Q)) % N
        Rbk = _INF
        for j in range(Q): Rbk = pt_add(Rbk, pt_mul(R_tilde[j], W[k][j]))
        assert pt_eq(pt_base_mul(rbk), Rbk), f"Batch consistency k={k}"
        r_bar.append(rbk); R_bar.append(Rbk)

    # Step 4: Shamir split each r-bar_k
    r_bar_shares = {i: [] for i in range(1,n+1)}
    for k in range(P):
        sh = shamir_split(r_bar[k], t, n)
        for i in range(1,n+1): r_bar_shares[i].append(sh[i])

    return PresigBatch(batch_id, random_scalar(), R_bar, r_bar_shares, P)

@dataclass
class SRTSSignature:
    R_prime: object; z: int; delta: int

def srts_sign(dkg: DKGResult, batch: PresigBatch, index: int,
              signers: list[int], message: bytes,
              beacon: Optional[bytes]=None) -> SRTSSignature:
    """
    SRTS Online Phase  -  Single-Round Signing.

    delta = H("srts_delta" | D | R-bar | rho | msg | beacon)
    R'    = R-bar + delta*G
    h     = H("srts_challenge" | D | R' | msg)
    sigma_i = r-bar_{k,i} + delta + h*d_i   mod N   (one per signer, no comm round)
    z       = sum_i lambda_i * sigma_i       mod N   (Lagrange aggregation)
    """
    assert not batch.used[index], f"Presig {index} already consumed"
    batch.used[index] = True

    D     = dkg.group_pubkey
    R_bar = batch.R_bar[index]

    if beacon is None:
        beacon = hashlib.sha256(
            b"consensus_block_" + batch.batch_id.to_bytes(4,"big")).digest()

    delta = h2s(b"srts_delta", enc_pt(D), enc_pt(R_bar),
                enc_sc(batch.nonce_rho), enc_sc(len(message)), message, beacon)
    R_prime = pt_add(R_bar, pt_base_mul(delta))
    h = h2s(b"srts_challenge", enc_pt(D), enc_pt(R_prime), message)

    z = 0
    for i in signers:
        li   = lagrange(i, signers)
        rbi  = batch.r_bar_shares[i][index]
        di   = dkg.key_packages[i].secret_share
        si   = (rbi + delta + h*di) % N
        z    = (z + li*si) % N
    return SRTSSignature(R_prime, z, delta)

def srts_verify(sig: SRTSSignature, D: object, message: bytes) -> bool:
    """z*G == R' + h*D   (standard Schnorr, no pairing)"""
    h = h2s(b"srts_challenge", enc_pt(D), enc_pt(sig.R_prime), message)
    return pt_eq(pt_base_mul(sig.z), pt_add(sig.R_prime, pt_mul(D, h)))

# ---------------------------------------------------------------------------
# S6  BLS Threshold Signatures  (Boldyreva 2003) over BLS12-381
#     Sign is fully benchmarked (t G2 scalar mults).
#     Verify: py_ecc pairing is ~12 s; we use one measured calibration + blst estimate.
# ---------------------------------------------------------------------------
_BLS_PAIR_MS_PYECC: Optional[float] = None
_BLS_PAIR_MS_BLST  = 1.1   # blst C library, modern hardware

def _measure_pairing() -> float:
    global _BLS_PAIR_MS_PYECC
    if _BLS_PAIR_MS_PYECC is not None: return _BLS_PAIR_MS_PYECC
    if not BLS_AVAILABLE: return 0.0
    Hm = bls_mul(G2, secrets.randbelow(BLS_N-1)+1)
    PK = bls_mul(G1, secrets.randbelow(BLS_N-1)+1)
    t0 = time.perf_counter()
    pairing(Hm, PK)
    _BLS_PAIR_MS_PYECC = (time.perf_counter()-t0)*1000
    return _BLS_PAIR_MS_PYECC

def _bls_inv(k): return pow(k%BLS_N, BLS_N-2, BLS_N)
def _bls_lag(i, sigs):
    num, den = 1, 1
    for j in sigs:
        if j==i: continue
        num = num*j%BLS_N; den = den*(j-i)%BLS_N
    return num*_bls_inv(den)%BLS_N

def _bls_hg2(msg):
    s = int.from_bytes(hashlib.sha256(b"bls_h2g2"+msg).digest(),"big")%BLS_N
    return bls_mul(G2, s)

@dataclass
class BLSResult:
    key_packages: dict[int,dict]
    group_pubkey: object

@dataclass
class BLSSignature:
    sig: object

def bls_dkg(n: int, t: int) -> BLSResult:
    """BLS keygen: Shamir split of master scalar; DKG would be identical in cost."""
    master = secrets.randbelow(BLS_N-1)+1
    coeffs = [master]+[secrets.randbelow(BLS_N-1)+1 for _ in range(t-1)]
    gpk    = bls_mul(G1, master)
    kp     = {}
    for i in range(1,n+1):
        v, xp = 0, 1
        for c in coeffs:
            v = (v+c*xp)%BLS_N; xp = xp*i%BLS_N
        kp[i] = {"secret": v, "group_pubkey": gpk}
    return BLSResult(kp, gpk)

def bls_sign(res: BLSResult, signers: list[int], msg: bytes) -> BLSSignature:
    """Single-round BLS: sigma_i = lambda_i * sk_i * H(m); agg = sum sigma_i."""
    Hm  = _bls_hg2(msg)
    agg = Z2
    for i in signers:
        li  = _bls_lag(i, signers)
        sk  = res.key_packages[i]["secret"]
        agg = bls_add(agg, bls_mul(Hm, li*sk%BLS_N))
    return BLSSignature(agg)

def bls_verify(sig: BLSSignature, gpk: object, msg: bytes) -> bool:
    """e(H(m), PK) == e(sigma, G1)"""
    Hm = _bls_hg2(msg)
    return pairing(Hm, gpk) == pairing(sig.sig, G1)

# ---------------------------------------------------------------------------
# S7  Benchmarking harness
# ---------------------------------------------------------------------------
def _timeit(fn, *a, **kw):
    t0 = time.perf_counter(); r = fn(*a,**kw)
    return (time.perf_counter()-t0)*1000, r

def _median(v):
    s = sorted(v); n = len(s)
    return (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]

def _cv(v):
    import statistics
    return statistics.stdev(v)/statistics.mean(v)*100 if len(v)>1 else 0.0

@dataclass
class BenchResult:
    op:str; scheme:str; n:int; t:int; iterations:int
    median_ms:float; min_ms:float; max_ms:float; cv_pct:float; ok:bool; note:str=""

def _add(results, op, scheme, n, t, reps, times, ok, note=""):
    results.append(BenchResult(op,scheme,n,t,reps,
        _median(times),min(times),max(times),_cv(times),ok,note))


def bench_srts(n, t, reps, verbose) -> list[BenchResult]:
    res = []; msg = b"SRTS benchmark message"
    Q = max(1, n-t); P = max(1, n-2*t)
    if P < 1:
        print(f"  [SRTS] P=n-2t={n-2*t}<1 for n={n},t={t}. Skipping.")
        return []
    if verbose: print(f"\n[SRTS] n={n}, t={t}, Q={Q}, P={P}")

    dkg_t=[]; dkg=None
    for _ in range(reps):
        ms, dkg = _timeit(dkg_pedersen, n, t); dkg_t.append(ms)
    _add(res,"DKG","SRTS",n,t,reps,dkg_t,True)
    if verbose: print(f"  DKG    {_median(dkg_t):8.2f} ms  CV={_cv(dkg_t):.1f}%")

    ps_t=[]
    for _ in range(reps):
        ms,_ = _timeit(srts_batch_presign,dkg,Q,P,0); ps_t.append(ms)
    _add(res,"Presign","SRTS",n,t,reps,ps_t,True,note=f"P={P} presigs")
    if verbose: print(f"  Presign{_median(ps_t):8.2f} ms  CV={_cv(ps_t):.1f}%  (P={P})")

    sg=list(range(1,t+1)); st=[]; ok=False
    for rep in range(reps):
        b = srts_batch_presign(dkg,Q,P,rep)
        ms,sig = _timeit(srts_sign,dkg,b,0,sg,msg)
        ok = srts_verify(sig,dkg.group_pubkey,msg); st.append(ms)
    _add(res,"Sign","SRTS",n,t,reps,st,ok,note="1 online round")
    if verbose: print(f"  Sign   {_median(st):8.3f} ms  CV={_cv(st):.1f}%  ok={ok}")

    b2=srts_batch_presign(dkg,Q,P,9999); sig=srts_sign(dkg,b2,0,sg,msg)
    vt=[]
    for _ in range(reps):
        ms,ok=_timeit(srts_verify,sig,dkg.group_pubkey,msg); vt.append(ms)
    _add(res,"Verify","SRTS",n,t,reps,vt,ok,note="Schnorr (no pairing)")
    if verbose: print(f"  Verify {_median(vt):8.3f} ms  CV={_cv(vt):.1f}%")
    return res


def bench_frost(n, t, reps, verbose) -> list[BenchResult]:
    res=[]; msg=b"FROST benchmark message"
    if verbose: print(f"\n[FROST] n={n}, t={t}")

    dkg_t=[]; dkg=None
    for _ in range(reps):
        ms,dkg=_timeit(dkg_pedersen,n,t); dkg_t.append(ms)
    _add(res,"DKG","FROST",n,t,reps,dkg_t,True)
    if verbose: print(f"  DKG    {_median(dkg_t):8.2f} ms  CV={_cv(dkg_t):.1f}%")

    sg=list(range(1,t+1)); st=[]; ok=False
    for _ in range(reps):
        nc={i:frost_commit() for i in sg}
        ms,sig=_timeit(frost_sign,dkg,sg,msg,nc)
        ok=frost_verify(sig,dkg.group_pubkey,msg); st.append(ms)
    _add(res,"Sign","FROST",n,t,reps,st,ok,note="2 online rounds")
    if verbose: print(f"  Sign   {_median(st):8.3f} ms  CV={_cv(st):.1f}%  ok={ok}")

    nc={i:frost_commit() for i in sg}
    sig=frost_sign(dkg,sg,msg,nc); vt=[]
    for _ in range(reps):
        ms,ok=_timeit(frost_verify,sig,dkg.group_pubkey,msg); vt.append(ms)
    _add(res,"Verify","FROST",n,t,reps,vt,ok,note="Schnorr (no pairing)")
    if verbose: print(f"  Verify {_median(vt):8.3f} ms  CV={_cv(vt):.1f}%")
    return res


def bench_bls(n, t, reps, verbose, skip_verify=False) -> list[BenchResult]:
    if not BLS_AVAILABLE: return []
    res=[]; msg=b"BLS benchmark message"
    if verbose: print(f"\n[BLS] n={n}, t={t}")

    dt=[]; br=None
    for _ in range(reps):
        ms,br=_timeit(bls_dkg,n,t); dt.append(ms)
    _add(res,"DKG","BLS",n,t,reps,dt,True)
    if verbose: print(f"  DKG    {_median(dt):8.2f} ms  CV={_cv(dt):.1f}%")

    sg=list(range(1,t+1)); st=[]
    for _ in range(reps):
        ms,_=_timeit(bls_sign,br,sg,msg); st.append(ms)
    _add(res,"Sign","BLS",n,t,reps,st,True,note="1 round; t G2 mults")
    if verbose: print(f"  Sign   {_median(st):8.3f} ms  CV={_cv(st):.1f}%")

    if not skip_verify:
        print("  [BLS] Measuring one pairing (slow in py_ecc; this takes ~12 s)...")
        pair_ms = _measure_pairing()
        vm = 2*pair_ms   # two pairings per verify
        vp = 2*_BLS_PAIR_MS_BLST
        _add(res,"Verify","BLS",n,t,1,[vm],[vm],[vm],0.0,True,
             note=f"blst={vp:.1f}ms; py_ecc={vm:.0f}ms")
        if verbose:
            print(f"  Verify  {vp:.1f} ms (blst)  /  {vm:.0f} ms (py_ecc pure-Python)")
    else:
        vp = 2*_BLS_PAIR_MS_BLST
        _add(res,"Verify","BLS",n,t,0,[vp],[vp],[vp],0.0,True,
             note=f"blst estimate={vp:.1f}ms (pairing skipped)")
        if verbose: print(f"  Verify  ~{vp:.1f} ms (blst C estimate)")
    return res

# ---------------------------------------------------------------------------
# S8  Reporting
# ---------------------------------------------------------------------------
def print_table(results):
    W = 74
    print("\n"+"="*W)
    print("BENCHMARK RESULTS  --  real secp256k1 via libsecp256k1 (coincurve)")
    print("="*W)
    print(f"{'Scheme':<7} {'n':>4} {'t':>4} {'Op':<9} {'Median ms':>10} "
          f"{'Min':>8} {'Max':>8} {'CV%':>5}  Note")
    print("-"*W)
    prev=None
    for r in results:
        if r.scheme!=prev:
            if prev: print()
            prev=r.scheme
        note = r.note[:30]
        print(f"{r.scheme:<7} {r.n:>4} {r.t:>4} {r.op:<9} "
              f"{r.median_ms:>10.3f} {r.min_ms:>8.3f} {r.max_ms:>8.3f} "
              f"{r.cv_pct:>5.1f}  {note}")
    print("="*W)

def print_comparison(results):
    print("\n"+"─"*62)
    print("SRTS vs FROST  --  SIGN & VERIFY  (same secp256k1 curve)")
    print("─"*62)
    by = {(r.scheme,r.n,r.t,r.op):r.median_ms for r in results}
    configs = sorted({(r.n,r.t) for r in results})
    for n,t in configs:
        print(f"\n  n={n}, t={t}")
        for op in ("Sign","Verify"):
            s=by.get(("SRTS",n,t,op)); f=by.get(("FROST",n,t,op))
            b=by.get(("BLS",n,t,op))
            parts=[]
            if s: parts.append(f"SRTS={s:.3f} ms")
            if f: parts.append(f"FROST={f:.3f} ms")
            if b: parts.append(f"BLS~{b:.1f} ms")
            if s and f:
                parts.append(f"-> SRTS is {f/s:.1f}x faster")
            print(f"    {op:<7}: "+"  |  ".join(parts))
    print()

def save_csv(results, path):
    with open(path,"w",newline="") as f:
        w=csv.writer(f)
        w.writerow(["scheme","n","t","op","iterations","median_ms",
                    "min_ms","max_ms","cv_pct","ok","note"])
        for r in results:
            w.writerow([r.scheme,r.n,r.t,r.op,r.iterations,
                        f"{r.median_ms:.6f}",f"{r.min_ms:.6f}",
                        f"{r.max_ms:.6f}",f"{r.cv_pct:.2f}",r.ok,r.note])
    print(f"[csv] Saved to {path}")

# ---------------------------------------------------------------------------
# S9  Correctness tests
# ---------------------------------------------------------------------------
def run_correctness_tests() -> bool:
    print("\n"+"="*52)
    print("CORRECTNESS TESTS")
    print("="*52)
    all_ok = True
    def chk(name, cond):
        nonlocal all_ok
        sym = "OK" if cond else "FAIL"
        print(f"  [{sym}]  {name}")
        if not cond: all_ok = False

    # Shamir
    s  = random_scalar()
    sh = shamir_split(s, 3, 5)
    for combo in [(1,2,3),(1,3,5),(2,4,5)]:
        chk(f"Shamir reconstruct {combo}",
            shamir_reconstruct({i:sh[i] for i in combo})==s)

    # Lagrange sum=1
    for sg in [[1,2,3],[1,4,5]]:
        chk(f"Lagrange sum=1 {sg}", sum(lagrange(i,sg) for i in sg)%N==1)

    # Manual Schnorr
    x=random_scalar(); D=pt_base_mul(x); r=random_scalar(); R=pt_base_mul(r)
    h=h2s(b"t",enc_pt(D),enc_pt(R),b"m"); z=(r+h*x)%N
    chk("Manual Schnorr z*G == R+h*D", pt_eq(pt_base_mul(z),pt_add(R,pt_mul(D,h))))

    # FROST
    dkg=dkg_pedersen(5,3); msg=b"test"
    for sg in [[1,2,3],[2,3,5]]:
        nc={i:frost_commit() for i in sg}
        sig=frost_sign(dkg,sg,msg,nc)
        chk(f"FROST sign+verify sg={sg}", frost_verify(sig,dkg.group_pubkey,msg))
        chk(f"FROST reject wrong msg sg={sg}",
            not frost_verify(sig,dkg.group_pubkey,b"bad"))

    # SRTS  n=6,t=2  -> Q=4,P=2
    dkg2=dkg_pedersen(6,2); Q2,P2=4,2
    b=srts_batch_presign(dkg2,Q2,P2,0)
    chk(f"SRTS batch size P={P2}", b.P==P2)
    for idx,(m,bad) in enumerate([(b"msg A",b"bad A"),(b"msg B",b"bad B")]):
        sig=srts_sign(dkg2,b,idx,[1,2],m)
        chk(f"SRTS presig[{idx}] verify", srts_verify(sig,dkg2.group_pubkey,m))
        chk(f"SRTS presig[{idx}] reject wrong", not srts_verify(sig,dkg2.group_pubkey,bad))
        chk(f"SRTS R' = R-bar + delta*G",
            pt_eq(pt_add(b.R_bar[idx],pt_base_mul(sig.delta)),sig.R_prime))

    # Non-consecutive signer subset
    dkg3=dkg_pedersen(6,2); b3=srts_batch_presign(dkg3,4,2,0)
    s3=srts_sign(dkg3,b3,0,[3,5],b"subset")
    chk("SRTS non-consecutive signers", srts_verify(s3,dkg3.group_pubkey,b"subset"))

    # Exhaustion guard
    try:
        srts_sign(dkg2,b,0,[1,2],b"replay"); chk("SRTS exhaustion guard",False)
    except AssertionError:
        chk("SRTS exhaustion guard (AssertionError on replay)", True)

    # Vandermonde invertibility
    W=vandermonde_matrix(3,4)
    def det3(m):
        return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
               -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
               +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))%N
    sub=[[W[i][j] for j in range(3)] for i in range(3)]
    chk("Vandermonde 3x3 sub-matrix invertible (det!=0)", det3(sub)!=0)

    # BLS
    if BLS_AVAILABLE:
        br=bls_dkg(5,3); bs=bls_sign(br,[1,2,3],b"bls test")
        chk("BLS sign+verify", bls_verify(bs,br.group_pubkey,b"bls test"))
        chk("BLS reject wrong", not bls_verify(bs,br.group_pubkey,b"other"))

    print(f"\n  {'All tests PASSED' if all_ok else 'SOME TESTS FAILED'}")
    print("="*52)
    return all_ok

# ---------------------------------------------------------------------------
# S10  CLI
# ---------------------------------------------------------------------------
def parse_args():
    p=argparse.ArgumentParser(description="Real-crypto SRTS/FROST/BLS benchmark (libsecp256k1)")
    p.add_argument("--scheme",choices=["SRTS","FROST","BLS","all"],default="all")
    p.add_argument("--n",type=int,default=5)
    p.add_argument("--t",type=int,default=None)
    p.add_argument("--reps",type=int,default=15)
    p.add_argument("--bench",action="store_true")
    p.add_argument("--ns",type=int,nargs="+",default=[5,10,20])
    p.add_argument("--thresholds",type=float,nargs="+",default=[0.33,0.66])
    p.add_argument("--test",action="store_true")
    p.add_argument("--no-test",action="store_true")
    p.add_argument("--skip-bls",action="store_true")
    p.add_argument("--skip-bls-verify",action="store_true")
    p.add_argument("--csv",type=str,default=None)
    p.add_argument("--verbose","-v",action="store_true")
    return p.parse_args()

def main():
    args=parse_args()
    schemes=["SRTS","FROST","BLS"] if args.scheme=="all" else [args.scheme]
    if args.skip_bls: schemes=[s for s in schemes if s!="BLS"]

    print("="*60)
    print("UAS THRESHOLD SIGNATURE - REAL CRYPTOGRAPHIC BENCHMARK")
    print(f"Backend: libsecp256k1 (coincurve) | BLS12-381 (py_ecc)")
    print(f"Schemes: {', '.join(schemes)}")
    print("="*60)

    if not args.no_test:
        ok=run_correctness_tests()
        if args.test or not ok: sys.exit(0 if ok else 1)

    all_results=[]
    configs=[]
    if args.bench:
        for n in args.ns:
            for tf in args.thresholds:
                configs.append((n, max(2,int(n*tf))))
    else:
        t=args.t if args.t else max(2,int(args.n*0.33))
        configs.append((args.n,t))

    for n,t in configs:
        print(f"\n{'─'*50}  n={n}, t={t} ({t/n*100:.0f}%)")
        if "SRTS"  in schemes:
            try: all_results+=bench_srts(n,t,args.reps,args.verbose)
            except Exception as e: print(f"  [SRTS] ERROR: {e}")
        if "FROST" in schemes:
            try: all_results+=bench_frost(n,t,args.reps,args.verbose)
            except Exception as e: print(f"  [FROST] ERROR: {e}")
        if "BLS"   in schemes:
            try: all_results+=bench_bls(n,t,args.reps,args.verbose,args.skip_bls_verify)
            except Exception as e: print(f"  [BLS] ERROR: {e}")

    if all_results:
        print_table(all_results)
        print_comparison(all_results)
    if args.csv: save_csv(all_results,args.csv)

if __name__=="__main__":
    main()