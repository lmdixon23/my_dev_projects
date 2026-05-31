//! End-to-end test through the public API: register -> commit -> reveal -> tally,
//! plus the anti-tamper property that two observers compute the same root.

use rust_decentralized_voting::{BallotBox, Commitment, Reveal};

fn nonce(byte: u8) -> Vec<u8> { vec![byte; 16] }

#[test]
fn two_observers_agree_on_merkle_root_for_the_same_committed_set() {
    let mut bb1 = BallotBox::new();
    let mut bb2 = BallotBox::new();
    for bb in [&mut bb1, &mut bb2] {
        bb.register("alice");
        bb.register("bob");
        bb.commit("alice", Commitment::new("yes", &nonce(1))).unwrap();
        bb.commit("bob", Commitment::new("no", &nonce(2))).unwrap();
    }
    let r1 = bb1.tally().unwrap();
    let r2 = bb2.tally().unwrap();
    assert_eq!(r1.commitment_root, r2.commitment_root);
}

#[test]
fn full_flow_produces_expected_counts() {
    let mut bb = BallotBox::new();
    for v in ["a", "b", "c", "d", "e"] { bb.register(v); }
    let ballots = [
        ("a", "x", nonce(11)),
        ("b", "x", nonce(12)),
        ("c", "y", nonce(13)),
        ("d", "x", nonce(14)),
        ("e", "z", nonce(15)),
    ];
    for (voter, cand, n) in &ballots {
        bb.commit(voter, Commitment::new(cand, n)).unwrap();
    }
    for (voter, cand, n) in &ballots {
        bb.reveal(voter, Reveal { candidate: (*cand).into(), nonce: n.clone() }).unwrap();
    }
    let result = bb.tally().unwrap();
    assert_eq!(result.counts.get("x").copied(), Some(3));
    assert_eq!(result.counts.get("y").copied(), Some(1));
    assert_eq!(result.counts.get("z").copied(), Some(1));
}
