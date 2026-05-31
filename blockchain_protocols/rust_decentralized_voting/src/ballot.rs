//! Commit-reveal ballot box.
//!
//! Phase 1 (commit): a registered voter publishes `commitment = SHA-256(
//! candidate_bytes || nonce)`. No information about `candidate` leaks
//! beyond the commitment.
//!
//! Phase 2 (reveal): the voter publishes `(candidate, nonce)`. The
//! ballot box verifies the hash matches the original commitment; if not,
//! the ballot is rejected and not tallied.
//!
//! Tally produces both the candidate -> count map and a Merkle root over
//! the ordered list of all commitments, which acts as a verifiable
//! "snapshot" of the committed-ballot set.

use std::collections::{BTreeMap, HashMap, HashSet};

use sha2::{Digest, Sha256};

use crate::error::VotingError;
use crate::merkle::{merkle_root, Hash};

/// A ballot commitment. Opaque to anyone but the voter until reveal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Commitment(pub Hash);

impl Commitment {
    /// `H(candidate_bytes || nonce)`. Domain-separated via `H("ballot:")` prefix
    /// to prevent commitment confusion with other SHA-256 uses elsewhere.
    pub fn new(candidate: &str, nonce: &[u8]) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(b"ballot:");
        hasher.update(candidate.as_bytes());
        hasher.update(nonce);
        let mut out = [0u8; 32];
        out.copy_from_slice(&hasher.finalize());
        Commitment(out)
    }

    pub fn to_hex(&self) -> String { hex::encode(self.0) }
}

#[derive(Debug, Clone)]
pub struct Reveal {
    pub candidate: String,
    pub nonce: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct Ballot {
    pub commitment: Commitment,
    pub reveal: Option<Reveal>,
}

#[derive(Debug)]
pub struct TallyResult {
    pub counts: BTreeMap<String, u64>,
    pub commitment_root: Hash,
    pub total_committed: usize,
    pub total_revealed: usize,
}

/// Tracks registered voters and their (commitment, optional reveal).
#[derive(Debug, Default)]
pub struct BallotBox {
    registered: HashSet<String>,
    ballots: HashMap<String, Ballot>,
    commit_order: Vec<(String, Commitment)>, // for deterministic Merkle root
}

impl BallotBox {
    pub fn new() -> Self { Self::default() }

    pub fn register(&mut self, voter_id: impl Into<String>) {
        self.registered.insert(voter_id.into());
    }

    pub fn commit(
        &mut self,
        voter_id: &str,
        commitment: Commitment,
    ) -> Result<(), VotingError> {
        if !self.registered.contains(voter_id) {
            return Err(VotingError::UnregisteredVoter(voter_id.to_string()));
        }
        if self.ballots.contains_key(voter_id) {
            return Err(VotingError::DoubleCommit(voter_id.to_string()));
        }
        self.ballots.insert(
            voter_id.to_string(),
            Ballot { commitment, reveal: None },
        );
        self.commit_order.push((voter_id.to_string(), commitment));
        Ok(())
    }

    pub fn reveal(
        &mut self,
        voter_id: &str,
        reveal: Reveal,
    ) -> Result<(), VotingError> {
        let ballot = self
            .ballots
            .get_mut(voter_id)
            .ok_or_else(|| VotingError::NoCommitment(voter_id.to_string()))?;
        if ballot.reveal.is_some() {
            return Err(VotingError::AlreadyRevealed(voter_id.to_string()));
        }
        let recomputed = Commitment::new(&reveal.candidate, &reveal.nonce);
        if recomputed != ballot.commitment {
            return Err(VotingError::InvalidReveal(voter_id.to_string()));
        }
        ballot.reveal = Some(reveal);
        Ok(())
    }

    /// Tally all *revealed* ballots and return the verifiable Merkle root
    /// over the committed-ballot set.
    pub fn tally(&self) -> Result<TallyResult, VotingError> {
        let mut counts: BTreeMap<String, u64> = BTreeMap::new();
        let mut revealed = 0usize;
        for ballot in self.ballots.values() {
            if let Some(r) = &ballot.reveal {
                *counts.entry(r.candidate.clone()).or_insert(0) += 1;
                revealed += 1;
            }
        }
        let leaves: Vec<Hash> = self.commit_order.iter().map(|(_, c)| c.0).collect();
        let root = merkle_root(&leaves).unwrap_or([0u8; 32]);
        Ok(TallyResult {
            counts,
            commitment_root: root,
            total_committed: self.ballots.len(),
            total_revealed: revealed,
        })
    }

    pub fn registered_count(&self) -> usize { self.registered.len() }
    pub fn committed_count(&self) -> usize { self.ballots.len() }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn nonce(byte: u8) -> Vec<u8> { vec![byte; 16] }

    #[test]
    fn commit_then_reveal_then_tally() {
        let mut bb = BallotBox::new();
        bb.register("alice");
        bb.register("bob");

        let c_alice = Commitment::new("yes", &nonce(1));
        let c_bob = Commitment::new("no", &nonce(2));

        bb.commit("alice", c_alice).unwrap();
        bb.commit("bob", c_bob).unwrap();

        bb.reveal("alice", Reveal { candidate: "yes".into(), nonce: nonce(1) }).unwrap();
        bb.reveal("bob", Reveal { candidate: "no".into(), nonce: nonce(2) }).unwrap();

        let result = bb.tally().unwrap();
        assert_eq!(result.counts.get("yes").copied(), Some(1));
        assert_eq!(result.counts.get("no").copied(), Some(1));
        assert_eq!(result.total_revealed, 2);
        assert_eq!(result.total_committed, 2);
        assert_ne!(result.commitment_root, [0u8; 32]);
    }

    #[test]
    fn double_commit_rejected() {
        let mut bb = BallotBox::new();
        bb.register("alice");
        let c = Commitment::new("yes", &nonce(1));
        bb.commit("alice", c).unwrap();
        let again = bb.commit("alice", c);
        assert_eq!(again, Err(VotingError::DoubleCommit("alice".into())));
    }

    #[test]
    fn unregistered_voter_rejected() {
        let mut bb = BallotBox::new();
        let res = bb.commit("eve", Commitment::new("yes", &nonce(1)));
        assert_eq!(res, Err(VotingError::UnregisteredVoter("eve".into())));
    }

    #[test]
    fn wrong_reveal_rejected_and_ballot_remains_unrevealed() {
        let mut bb = BallotBox::new();
        bb.register("alice");
        bb.commit("alice", Commitment::new("yes", &nonce(1))).unwrap();
        let bad = bb.reveal("alice", Reveal { candidate: "no".into(), nonce: nonce(1) });
        assert_eq!(bad, Err(VotingError::InvalidReveal("alice".into())));
        // The ballot must NOT be marked revealed after a failed attempt;
        // the voter can still reveal correctly.
        bb.reveal("alice", Reveal { candidate: "yes".into(), nonce: nonce(1) }).unwrap();
    }

    #[test]
    fn tally_excludes_unrevealed_ballots_but_still_anchors_commitments() {
        let mut bb = BallotBox::new();
        bb.register("alice");
        bb.register("bob");
        bb.commit("alice", Commitment::new("yes", &nonce(1))).unwrap();
        bb.commit("bob", Commitment::new("no", &nonce(2))).unwrap();
        bb.reveal("alice", Reveal { candidate: "yes".into(), nonce: nonce(1) }).unwrap();

        let result = bb.tally().unwrap();
        assert_eq!(result.total_revealed, 1);
        assert_eq!(result.total_committed, 2);
        assert_eq!(result.counts.get("yes").copied(), Some(1));
        assert!(!result.counts.contains_key("no"));
    }
}
