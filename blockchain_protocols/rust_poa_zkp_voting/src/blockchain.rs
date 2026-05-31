use std::collections::{BTreeMap, HashMap};
use std::time::{SystemTime, UNIX_EPOCH};

use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
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

/// A pre-authorized block producer. Unlike the PoS sibling's `Validator`,
/// an `Authority` has **no stake** — its right to produce blocks comes from
/// being in the fixed authorized set, and each block it seals carries its
/// Ed25519 signature so observers can verify the producer's identity.
#[derive(Debug, Clone)]
pub struct Authority {
    pub id: String,
    pub public_key: VerifyingKey,
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
    /// Id of the authority whose round-robin turn produced this block.
    pub proposer: String,
    /// The proposer's Ed25519 signature over `hash`. Genesis carries a
    /// zero signature and is exempt from the proposer check.
    pub proposer_signature: Signature,
}

#[derive(Debug)]
pub struct Blockchain {
    chain: Vec<Block>,
    pending: Vec<SignedVote>,
    /// BTreeMap so the authority order is deterministic (sorted by id);
    /// round-robin selection indexes into this stable order.
    pub authorities: BTreeMap<String, Authority>,
    pub voters: HashMap<String, Voter>,
}

// --------------------------------------------------------------------- //
// Free functions
// --------------------------------------------------------------------- //
fn now_ts() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
}

fn sha256_block(b: &Block) -> [u8; 32] {
    // Hash everything *except* the `hash` and `proposer_signature` fields:
    // the signature is taken over the resulting hash, so it cannot be an input
    // to it.
    let mut h = Sha256::new();
    h.update(b.index.to_be_bytes());
    h.update(b.timestamp.to_be_bytes());
    h.update(b.prev_hash);
    h.update(b.proposer.as_bytes());
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
    m.extend_from_slice(b"poa-zkp-voting/v1:");
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

// --------------------------------------------------------------------- //
// Implementation
// --------------------------------------------------------------------- //
impl Blockchain {
    pub fn new() -> Self {
        let mut genesis = Block {
            index: 0,
            timestamp: now_ts(),
            prev_hash: [0u8; 32],
            hash: [0u8; 32],
            votes: Vec::new(),
            proposer: "genesis".into(),
            proposer_signature: Signature::from_bytes(&[0u8; 64]),
        };
        genesis.hash = sha256_block(&genesis);
        Self {
            chain: vec![genesis],
            pending: Vec::new(),
            authorities: BTreeMap::new(),
            voters: HashMap::new(),
        }
    }

    /// Register a pre-authorized block producer by id and public key.
    pub fn register_authority(&mut self, id: impl Into<String>, public_key: VerifyingKey) {
        let id = id.into();
        self.authorities.insert(id.clone(), Authority { id, public_key });
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

    /// Round-robin proposer for a given block index over the sorted authority
    /// set. Block `k` (k >= 1) is produced by `sorted_authorities[k % n]`.
    fn proposer_for_index(&self, index: u64) -> Result<String, ChainError> {
        let ids: Vec<&String> = self.authorities.keys().collect();
        if ids.is_empty() {
            return Err(ChainError::NoAuthorities);
        }
        let pos = (index as usize) % ids.len();
        Ok(ids[pos].clone())
    }

    /// The authority whose turn it is to produce the *next* block.
    pub fn current_proposer(&self) -> Result<String, ChainError> {
        let next_index = self.chain.len() as u64;
        self.proposer_for_index(next_index)
    }

    /// Seal pending votes into a new block. The caller must supply the signing
    /// key of the authority whose round-robin turn it is; the block is rejected
    /// otherwise. Returns the new block index.
    pub fn mine_block(&mut self, proposer_key: &SigningKey) -> Result<u64, ChainError> {
        let next_index = self.chain.len() as u64;
        let expected = self.proposer_for_index(next_index)?;
        let authority = self
            .authorities
            .get(&expected)
            .ok_or(ChainError::NoAuthorities)?;

        // The key offered must belong to the scheduled authority.
        if proposer_key.verifying_key() != authority.public_key {
            return Err(ChainError::WrongProposer {
                expected,
                got: "an unauthorized/out-of-turn key".into(),
            });
        }

        let prev = self.chain.last().unwrap();
        let mut block = Block {
            index: next_index,
            timestamp: now_ts(),
            prev_hash: prev.hash,
            hash: [0u8; 32],
            votes: std::mem::take(&mut self.pending),
            proposer: expected,
            proposer_signature: Signature::from_bytes(&[0u8; 64]),
        };
        block.hash = sha256_block(&block);
        block.proposer_signature = proposer_key.sign(&block.hash);
        let idx = block.index;
        self.chain.push(block);
        Ok(idx)
    }

    /// Walk the chain verifying: (1) prev-hash linking, (2) each block rehashes
    /// to its stored hash, (3) the block's proposer matches the round-robin
    /// schedule, and (4) the proposer's signature over the hash verifies.
    pub fn verify_integrity(&self) -> Result<(), ChainError> {
        for (i, block) in self.chain.iter().enumerate() {
            // Re-hash check (all blocks, including genesis).
            if sha256_block(block) != block.hash {
                return Err(ChainError::BrokenChain(block.index));
            }
            if i == 0 {
                continue; // genesis: no prev, no proposer signature
            }
            let prev = &self.chain[i - 1];
            if block.prev_hash != prev.hash {
                return Err(ChainError::BrokenChain(block.index));
            }
            // Proposer must match the round-robin schedule for this index.
            let expected = self.proposer_for_index(block.index)?;
            if block.proposer != expected {
                return Err(ChainError::WrongProposer {
                    expected,
                    got: block.proposer.clone(),
                });
            }
            // Proposer signature over the block hash must verify.
            let authority = self
                .authorities
                .get(&block.proposer)
                .ok_or(ChainError::NoAuthorities)?;
            authority
                .public_key
                .verify(&block.hash, &block.proposer_signature)
                .map_err(|_| ChainError::BadProposerSignature(block.index))?;
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

    pub fn chain(&self) -> &[Block] {
        &self.chain
    }
}

impl Default for Blockchain {
    fn default() -> Self {
        Self::new()
    }
}

// --------------------------------------------------------------------- //
// Tests
// --------------------------------------------------------------------- //
#[cfg(test)]
mod tests {
    use super::*;

    fn key(seed: u8) -> SigningKey {
        SigningKey::from_bytes(&[seed; 32])
    }

    /// Build a chain with three authorities (ids sort to a < b < c) and a
    /// lookup from id -> signing key so tests can mine in turn.
    fn setup() -> (Blockchain, std::collections::HashMap<String, SigningKey>) {
        let mut bc = Blockchain::new();
        let mut keys = std::collections::HashMap::new();
        for (id, seed) in [("authority-a", 1u8), ("authority-b", 2), ("authority-c", 3)] {
            let sk = key(seed);
            bc.register_authority(id, sk.verifying_key());
            keys.insert(id.to_string(), sk);
        }
        (bc, keys)
    }

    fn add_voter(bc: &mut Blockchain, id: &str, seed: u8, secret: &[u8]) -> SigningKey {
        let sk = key(seed);
        bc.register_voter(id, sk.verifying_key(), secret);
        sk
    }

    #[test]
    fn round_robin_visits_authorities_in_sorted_order() {
        let (mut bc, keys) = setup();
        // Next block is index 1 -> sorted[1 % 3] = authority-b, then -c, then -a.
        let expected = ["authority-b", "authority-c", "authority-a"];
        for want in expected {
            assert_eq!(bc.current_proposer().unwrap(), want);
            let idx = bc.mine_block(&keys[want]).unwrap();
            assert_eq!(bc.chain()[idx as usize].proposer, want);
        }
        bc.verify_integrity().unwrap();
    }

    #[test]
    fn out_of_turn_authority_is_rejected() {
        let (mut bc, keys) = setup();
        // It is authority-b's turn for block 1; offering authority-a's key fails.
        let err = bc.mine_block(&keys["authority-a"]).unwrap_err();
        match err {
            ChainError::WrongProposer { expected, .. } => assert_eq!(expected, "authority-b"),
            other => panic!("expected WrongProposer, got {other:?}"),
        }
    }

    #[test]
    fn tampering_with_a_sealed_vote_breaks_integrity() {
        let (mut bc, keys) = setup();
        let alice = add_voter(&mut bc, "alice", 10, b"alice-secret");
        let v = Blockchain::sign_vote(&alice, "alice", "Yes", 1, b"alice-secret");
        bc.submit_vote(v).unwrap();
        let proposer = bc.current_proposer().unwrap();
        let idx = bc.mine_block(&keys[&proposer]).unwrap();
        // Mutate a vote inside the sealed block.
        bc.chain[idx as usize].votes[0].candidate = "No".into();
        assert!(bc.verify_integrity().is_err());
    }

    #[test]
    fn double_vote_is_rejected() {
        let (mut bc, _keys) = setup();
        let alice = add_voter(&mut bc, "alice", 10, b"alice-secret");
        let v1 = Blockchain::sign_vote(&alice, "alice", "Yes", 1, b"alice-secret");
        let v2 = Blockchain::sign_vote(&alice, "alice", "No", 1, b"alice-secret");
        bc.submit_vote(v1).unwrap();
        assert_eq!(
            bc.submit_vote(v2).unwrap_err(),
            ChainError::DoubleVote("alice".into())
        );
    }

    #[test]
    fn wrong_eligibility_secret_is_rejected() {
        let (mut bc, _keys) = setup();
        let alice = add_voter(&mut bc, "alice", 10, b"alice-secret");
        // Reveal a different secret than the one committed at registration.
        let v = Blockchain::sign_vote(&alice, "alice", "Yes", 1, b"WRONG-secret");
        assert_eq!(
            bc.submit_vote(v).unwrap_err(),
            ChainError::BadCommitment("alice".into())
        );
    }

    #[test]
    fn tally_sums_weights_across_blocks() {
        let (mut bc, keys) = setup();
        let alice = add_voter(&mut bc, "alice", 10, b"a-secret");
        let bob = add_voter(&mut bc, "bob", 11, b"b-secret");
        bc.submit_vote(Blockchain::sign_vote(&alice, "alice", "Yes", 1, b"a-secret"))
            .unwrap();
        bc.submit_vote(Blockchain::sign_vote(&bob, "bob", "Yes", 2, b"b-secret"))
            .unwrap();
        let p = bc.current_proposer().unwrap();
        bc.mine_block(&keys[&p]).unwrap();
        let tally = bc.tally();
        assert_eq!(tally.get("Yes"), Some(&3));
    }
}
