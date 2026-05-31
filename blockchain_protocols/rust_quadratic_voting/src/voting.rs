use std::collections::{BTreeMap, HashMap, HashSet};

use crate::error::QvError;

#[derive(Debug, Clone)]
struct Voter {
    credits: u64,
    delegate: Option<String>, // None = casts own votes
    received_from: Vec<String>, // who delegated TO this voter
}

#[derive(Debug, Default)]
pub struct VotingSystem {
    voters: HashMap<String, Voter>,
    tally: BTreeMap<String, u64>,
}

#[derive(Debug)]
pub struct TallyResult {
    pub counts: BTreeMap<String, u64>,
    pub total_votes_cast: u64,
}

impl VotingSystem {
    pub fn new() -> Self { Self::default() }

    pub fn register_voter(&mut self, id: impl Into<String>, credits: u64) {
        self.voters.insert(
            id.into(),
            Voter { credits, delegate: None, received_from: Vec::new() },
        );
    }

    /// Delegate `from`'s remaining credits to `to`. Both voters must be
    /// registered, the delegator must not have already delegated, and the
    /// resulting delegation chain must be acyclic.
    pub fn delegate(&mut self, from: &str, to: &str) -> Result<(), QvError> {
        if !self.voters.contains_key(from) { return Err(QvError::unregistered(from)); }
        if !self.voters.contains_key(to)   { return Err(QvError::unregistered(to)); }
        if self.voters[from].delegate.is_some() {
            return Err(QvError::AlreadyDelegated(from.to_string()));
        }
        // Cycle check: walk `to`'s delegation chain; if we ever land on `from`, reject.
        let mut visited: HashSet<&str> = HashSet::new();
        let mut cursor = to;
        while let Some(next) = self.voters[cursor].delegate.as_deref() {
            if next == from {
                return Err(QvError::DelegationCycle {
                    from: from.to_string(),
                    to: to.to_string(),
                });
            }
            if !visited.insert(next) { break; } // safety against pre-existing cycle
            cursor = next;
        }
        // Move credits and record the delegation.
        let credits = self.voters.get_mut(from).unwrap().credits;
        self.voters.get_mut(from).unwrap().credits = 0;
        self.voters.get_mut(from).unwrap().delegate = Some(to.to_string());
        let to_voter = self.voters.get_mut(to).unwrap();
        to_voter.credits = to_voter.credits.saturating_add(credits);
        to_voter.received_from.push(from.to_string());
        Ok(())
    }

    /// Partial delegation: move exactly `k` of `from`'s credits to `to`,
    /// leaving `from` able to keep voting with whatever remains. Unlike
    /// [`delegate`](Self::delegate) (all-or-nothing), this does **not** mark
    /// `from` as having delegated, so the delegator retains direct voting
    /// rights over the credits they kept. `k == 0` and `from == to` are
    /// harmless no-ops. A voter who has already fully delegated (and thus
    /// has zero credits) is rejected.
    pub fn delegate_n(&mut self, from: &str, to: &str, k: u64) -> Result<(), QvError> {
        if !self.voters.contains_key(from) { return Err(QvError::unregistered(from)); }
        if !self.voters.contains_key(to)   { return Err(QvError::unregistered(to)); }
        if k == 0 || from == to { return Ok(()); }
        if self.voters[from].delegate.is_some() {
            return Err(QvError::AlreadyDelegated(from.to_string()));
        }
        let have = self.voters[from].credits;
        if have < k {
            return Err(QvError::InsufficientCredits {
                voter: from.to_string(),
                have,
                need: k,
            });
        }
        self.voters.get_mut(from).unwrap().credits -= k;
        let to_voter = self.voters.get_mut(to).unwrap();
        to_voter.credits = to_voter.credits.saturating_add(k);
        if !to_voter.received_from.iter().any(|r| r == from) {
            to_voter.received_from.push(from.to_string());
        }
        Ok(())
    }

    /// Cast `n_votes` for `candidate`. Cost is `n_votes^2` credits (QV).
    /// A voter who has delegated cannot cast directly.
    pub fn submit_vote(
        &mut self,
        voter_id: &str,
        candidate: &str,
        n_votes: u64,
    ) -> Result<(), QvError> {
        if n_votes == 0 { return Err(QvError::ZeroVotes); }
        let voter = self
            .voters
            .get_mut(voter_id)
            .ok_or_else(|| QvError::unregistered(voter_id))?;
        if voter.delegate.is_some() {
            return Err(QvError::HasDelegated(voter_id.to_string()));
        }
        let need = n_votes.saturating_mul(n_votes);
        if voter.credits < need {
            return Err(QvError::InsufficientCredits {
                voter: voter_id.to_string(),
                have: voter.credits,
                need,
            });
        }
        voter.credits -= need;
        *self.tally.entry(candidate.to_string()).or_insert(0) += n_votes;
        Ok(())
    }

    pub fn tally(&self) -> TallyResult {
        let total = self.tally.values().sum();
        TallyResult { counts: self.tally.clone(), total_votes_cast: total }
    }

    pub fn credits(&self, voter_id: &str) -> Option<u64> {
        self.voters.get(voter_id).map(|v| v.credits)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quadratic_cost_basic() {
        let mut vs = VotingSystem::new();
        vs.register_voter("a", 16);
        vs.submit_vote("a", "X", 4).unwrap(); // 16 credits
        assert_eq!(vs.credits("a"), Some(0));
        assert_eq!(vs.tally().counts.get("X").copied(), Some(4));
    }

    #[test]
    fn insufficient_credits_rejected() {
        let mut vs = VotingSystem::new();
        vs.register_voter("a", 8);
        let err = vs.submit_vote("a", "X", 3).unwrap_err();
        assert!(matches!(err, QvError::InsufficientCredits { .. }));
        // Credits unchanged after a rejected vote.
        assert_eq!(vs.credits("a"), Some(8));
    }

    #[test]
    fn delegate_transfers_credits_and_delegator_cannot_cast() {
        let mut vs = VotingSystem::new();
        vs.register_voter("a", 9);
        vs.register_voter("b", 16);
        vs.delegate("a", "b").unwrap();
        assert_eq!(vs.credits("a"), Some(0));
        assert_eq!(vs.credits("b"), Some(25));
        assert!(matches!(vs.submit_vote("a", "X", 1), Err(QvError::HasDelegated(_))));
        // b can now cast a 5-vote ballot using the pooled 25 credits.
        vs.submit_vote("b", "X", 5).unwrap();
        assert_eq!(vs.tally().counts.get("X").copied(), Some(5));
    }

    #[test]
    fn partial_delegation_moves_k_and_delegator_keeps_rights() {
        let mut vs = VotingSystem::new();
        vs.register_voter("a", 25);
        vs.register_voter("b", 0);
        vs.delegate_n("a", "b", 9).unwrap();
        assert_eq!(vs.credits("a"), Some(16)); // 25 - 9
        assert_eq!(vs.credits("b"), Some(9));
        // a keeps direct voting rights over the remaining 16 (4^2 = 16).
        vs.submit_vote("a", "X", 4).unwrap();
        assert_eq!(vs.credits("a"), Some(0));
        // b votes with the 9 received (3^2 = 9).
        vs.submit_vote("b", "X", 3).unwrap();
        assert_eq!(vs.tally().counts.get("X").copied(), Some(7));
    }

    #[test]
    fn partial_delegation_insufficient_rejected() {
        let mut vs = VotingSystem::new();
        vs.register_voter("a", 5);
        vs.register_voter("b", 0);
        let err = vs.delegate_n("a", "b", 9).unwrap_err();
        assert!(matches!(err, QvError::InsufficientCredits { .. }));
        assert_eq!(vs.credits("a"), Some(5)); // unchanged after rejection
    }

    #[test]
    fn partial_delegation_zero_and_self_are_noops() {
        let mut vs = VotingSystem::new();
        vs.register_voter("a", 10);
        vs.register_voter("b", 0);
        vs.delegate_n("a", "b", 0).unwrap(); // k == 0
        vs.delegate_n("a", "a", 5).unwrap(); // from == to
        assert_eq!(vs.credits("a"), Some(10));
        assert_eq!(vs.credits("b"), Some(0));
    }

    #[test]
    fn delegation_cycle_rejected() {
        let mut vs = VotingSystem::new();
        vs.register_voter("a", 4);
        vs.register_voter("b", 4);
        vs.register_voter("c", 4);
        vs.delegate("a", "b").unwrap();
        vs.delegate("b", "c").unwrap();
        let err = vs.delegate("c", "a").unwrap_err();
        assert!(matches!(err, QvError::DelegationCycle { .. }));
    }

    #[test]
    fn double_delegation_rejected() {
        let mut vs = VotingSystem::new();
        vs.register_voter("a", 4);
        vs.register_voter("b", 4);
        vs.register_voter("c", 4);
        vs.delegate("a", "b").unwrap();
        assert!(matches!(vs.delegate("a", "c"), Err(QvError::AlreadyDelegated(_))));
    }

    #[test]
    fn many_voters_for_same_candidate_accumulate() {
        let mut vs = VotingSystem::new();
        for v in ["a", "b", "c"] { vs.register_voter(v, 4); }
        vs.submit_vote("a", "X", 2).unwrap(); // 4
        vs.submit_vote("b", "X", 2).unwrap();
        vs.submit_vote("c", "X", 2).unwrap();
        assert_eq!(vs.tally().counts.get("X").copied(), Some(6));
        assert_eq!(vs.tally().total_votes_cast, 6);
    }
}
