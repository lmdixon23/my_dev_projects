use std::collections::{BTreeMap, HashMap};
use std::time::{SystemTime, UNIX_EPOCH};

use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use rand::{rngs::StdRng, Rng, SeedableRng};
use sha2::{Digest, Sha256};

use crate::error::ChainError;

// --------------------------------------------------------------------- //
// Domain types
// --------------------------------------------------------------------- //
#[derive(Debug, Clone)]
pub struct Voter {
    pub id: String,
    pub public_key: VerifyingKey,
    /// SHA-256 commitment over the voter's secret nonce; placeholder for
    /// what a real ZKP eligibility proof would assert.
    pub eligibility_commitment: [u8; 32],
    pub has_voted: bool,
}

#[derive(Debug, Clone)]
pub struct Validator {
    pub id: String,
    pub stake: u64,
}

#[derive(Debug, Clone)]
pub struct SignedVote {
    pub voter_id: String,
    pub candidate: String,
    pub weight: u64,
    pub timestamp: u64,
    pub eligibility_reveal: Vec<u8>, // re-hashed and checked against commitment
    pub signature: Signature,
}

#[derive(Debug, Clone)]
pub struct Block {
    pub index: u64,
    pub timestamp: u64,
    pub prev_hash: [u8; 32],
    pub hash: [u8; 32],
    pub votes: Vec<SignedVote>,
    pub miner: String,
}

#[derive(Debug)]
pub struct Blockchain {
    chain: Vec<Block>,
    pending: Vec<SignedVote>,
    pub validators: HashMap<String, Validator>,
    pub voters: HashMap<String, Voter>,
    rng: StdRng,
}

// --------------------------------------------------------------------- //
// Implementation
// --------------------------------------------------------------------- //
fn now_ts() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
}

fn sha256_block(b: &Block) -> [u8; 32] {
    // Hash everything *except* the `hash` field itself.
    let mut h = Sha256::new();
    h.update(b.index.to_be_bytes());
    h.update(b.timestamp.to_be_bytes());
    h.update(b.prev_hash);
    h.update(b.miner.as_bytes());
    for v in &b.votes {
        h.update(v.voter_id.as_bytes());
        h.update(v.candidate.as_bytes());
        h.update(v.weight.to_be_bytes());
        h.update(v.timestamp.to_be_bytes());
        h.update(v.signature.to_bytes());
    }
    let mut out = [0u8; 32];
    out.copy_from_slice(&h.finalize());
    out
}

/// Domain-separated message that a voter signs.
fn vote_message(v: &SignedVote) -> Vec<u8> {
    let mut m = Vec::new();
    m.extend_from_slice(b"pos-zkp-voting/v1:");
    m.extend_from_slice(v.voter_id.as_bytes());
    m.extend_from_slice(b"|");
    m.extend_from_slice(v.candidate.as_bytes());
    m.extend_from_slice(b"|");
    m.extend_from_slice(&v.weight.to_be_bytes());
    m.extend_from_slice(b"|");
    m.extend_from_slice(&v.timestamp.to_be_bytes());
    m
}

pub fn eligibility_commit(secret: &[u8]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"eligibility:");
    h.update(secret);
    let mut out = [0u8; 32];
    out.copy_from_slice(&h.finalize());
    out
}

impl Blockchain {
    pub fn new() -> Self { Self::with_seed(0xCAFEBABE) }

    pub fn with_seed(seed: u64) -> Self {
        let genesis = Block {
            index: 0,
            timestamp: now_ts(),
            prev_hash: [0u8; 32],
            hash: [0u8; 32],
            votes: Vec::new(),
            miner: "genesis".into(),
        };
        let mut me = Self {
            chain: vec![genesis.clone()],
            pending: Vec::new(),
            validators: HashMap::new(),
            voters: HashMap::new(),
            rng: StdRng::seed_from_u64(seed),
        };
        // Re-hash the genesis so subsequent blocks have a stable prev_hash.
        let h = sha256_block(&me.chain[0]);
        me.chain[0].hash = h;
        me
    }

    pub fn register_validator(&mut self, id: impl Into<String>, stake: u64) {
        let id = id.into();
        self.validators.insert(id.clone(), Validator { id, stake });
    }

    /// Register a voter. `eligibility_secret` is hashed once at registration;
    /// the voter keeps the secret and reveals it inside their vote.
    pub fn register_voter(
        &mut self,
        id: impl Into<String>,
        public_key: VerifyingKey,
        eligibility_secret: &[u8],
    ) {
        let id = id.into();
        self.voters.insert(
            id.clone(),
            Voter {
                id,
                public_key,
                eligibility_commitment: eligibility_commit(eligibility_secret),
                has_voted: false,
            },
        );
    }

    /// Convenience for tests/demos: build a signed vote from a SigningKey.
    pub fn sign_vote(
        signing_key: &SigningKey,
        voter_id: &str,
        candidate: &str,
        weight: u64,
        eligibility_secret: &[u8],
    ) -> SignedVote {
        let mut v = SignedVote {
            voter_id: voter_id.into(),
            candidate: candidate.into(),
            weight,
            timestamp: now_ts(),
            eligibility_reveal: eligibility_secret.to_vec(),
            signature: Signature::from_bytes(&[0u8; 64]),
        };
        let msg = vote_message(&v);
        v.signature = signing_key.sign(&msg);
        v
    }

    pub fn submit_vote(&mut self, vote: SignedVote) -> Result<(), ChainError> {
        let voter = self
            .voters
            .get_mut(&vote.voter_id)
            .ok_or_else(|| ChainError::UnregisteredVoter(vote.voter_id.clone()))?;
        if voter.has_voted {
            return Err(ChainError::DoubleVote(vote.voter_id.clone()));
        }
        if eligibility_commit(&vote.eligibility_reveal) != voter.eligibility_commitment {
            return Err(ChainError::BadCommitment(vote.voter_id.clone()));
        }
        let msg = vote_message(&vote);
        voter
            .public_key
            .verify(&msg, &vote.signature)
            .map_err(|_| ChainError::BadSignature(vote.voter_id.clone()))?;
        voter.has_voted = true;
        self.pending.push(vote);
        Ok(())
    }

    /// Stake-weighted random sampling over active validators.
    pub fn select_validator(&mut self) -> Result<String, ChainError> {
        let total: u64 = self.validators.values().map(|v| v.stake).sum();
        if total == 0 { return Err(ChainError::NoValidators); }
        let r: u64 = self.rng.gen_range(0..total);
        let mut acc = 0u64;
        for v in self.validators.values() {
            acc = acc.saturating_add(v.stake);
            if r < acc { return Ok(v.id.clone()); }
        }
        unreachable!("stake sampling overflow")
    }

    /// Seal pending votes into a new block. Returns the block index.
    pub fn mine_block(&mut self) -> Result<u64, ChainError> {
        let miner = self.select_validator()?;
        let prev = self.chain.last().unwrap();
        let mut block = Block {
            index: prev.index + 1,
            timestamp: now_ts(),
            prev_hash: prev.hash,
            hash: [0u8; 32],
            votes: std::mem::take(&mut self.pending),
            miner,
        };
        block.hash = sha256_block(&block);
        let idx = block.index;
        self.chain.push(block);
        Ok(idx)
    }

    pub fn verify_integrity(&self) -> Result<(), ChainError> {
        for window in self.chain.windows(2) {
            let prev = &window[0];
            let curr = &window[1];
            if curr.prev_hash != prev.hash {
                return Err(ChainError::BrokenChain(curr.index));
            }
            if sha256_block(curr) != curr.hash {
                return Err(ChainError::BrokenChain(curr.index));
            }
        }
        Ok(())
    }

    pub fn tally(&self) -> BTreeMap<String, u64> {
        let mut counts = BTreeMap::new();
        for block in &self.chain {
            for v in &block.votes {
                *counts.entry(v.candidate.clone()).or_insert(0) += v.weight;
            }
        }
        counts
    }

    pub fn chain(&self) -> &[Block] { &self.chain }
}

impl Default for Blockchain {
    fn default() -> Self { Self::new() }
}

// --------------------------------------------------------------------- //
// Tests
// --------------------------------------------------------------------- //
#[cfg(test)]
mod tests {
    use super::*;
    use rand_core::OsRng;

    fn keypair() -> SigningKey { SigningKey::generate(&mut OsRng) }

    fn fresh_chain_with(voters: &[(&str, &[u8])]) -> (Blockchain, HashMap<String, SigningKey>) {
        let mut bc = Blockchain::with_seed(42);
        bc.register_validator("v1", 100);
        bc.register_validator("v2", 50);
        let mut keys = HashMap::new();
        for (id, secret) in voters {
            let sk = keypair();
            let vk = sk.verifying_key();
            bc.register_voter(*id, vk, secret);
            keys.insert((*id).to_string(), sk);
        }
        (bc, keys)
    }

    #[test]
    fn valid_signed_vote_is_accepted_and_mined() {
        let (mut bc, keys) = fresh_chain_with(&[("alice", b"alice-secret")]);
        let v = Blockchain::sign_vote(&keys["alice"], "alice", "yes", 1, b"alice-secret");
        bc.submit_vote(v).unwrap();
        let idx = bc.mine_block().unwrap();
        assert_eq!(idx, 1);
        assert_eq!(bc.tally().get("yes").copied(), Some(1));
        bc.verify_integrity().unwrap();
    }

    #[test]
    fn forged_signature_is_rejected() {
        let (mut bc, _) = fresh_chain_with(&[("alice", b"alice-secret")]);
        let attacker = keypair();
        let v = Blockchain::sign_vote(&attacker, "alice", "yes", 1, b"alice-secret");
        let err = bc.submit_vote(v).unwrap_err();
        assert!(matches!(err, ChainError::BadSignature(_)));
        assert!(bc.tally().is_empty());
    }

    #[test]
    fn wrong_eligibility_reveal_is_rejected() {
        let (mut bc, keys) = fresh_chain_with(&[("alice", b"alice-secret")]);
        let v = Blockchain::sign_vote(&keys["alice"], "alice", "yes", 1, b"NOT-the-secret");
        let err = bc.submit_vote(v).unwrap_err();
        assert!(matches!(err, ChainError::BadCommitment(_)));
    }

    #[test]
    fn double_vote_is_rejected() {
        let (mut bc, keys) = fresh_chain_with(&[("alice", b"s")]);
        let v1 = Blockchain::sign_vote(&keys["alice"], "alice", "yes", 1, b"s");
        let v2 = Blockchain::sign_vote(&keys["alice"], "alice", "no", 1, b"s");
        bc.submit_vote(v1).unwrap();
        assert!(matches!(bc.submit_vote(v2), Err(ChainError::DoubleVote(_))));
    }

    #[test]
    fn integrity_check_catches_tampering() {
        let (mut bc, keys) = fresh_chain_with(&[("alice", b"s")]);
        let v = Blockchain::sign_vote(&keys["alice"], "alice", "yes", 1, b"s");
        bc.submit_vote(v).unwrap();
        bc.mine_block().unwrap();
        bc.verify_integrity().unwrap();

        // Tamper with a vote inside the mined block. The cached `hash`
        // field will no longer match the recomputed hash.
        bc.chain[1].votes[0].candidate = "tampered".into();
        assert!(matches!(bc.verify_integrity(), Err(ChainError::BrokenChain(_))));
    }
}
