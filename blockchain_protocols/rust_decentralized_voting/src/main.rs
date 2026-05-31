//! Demo binary: registers three voters, runs the commit/reveal flow,
//! prints the tally + the Merkle root that anchors the committed-ballot set.

use rand::RngCore;
use rust_decentralized_voting::{BallotBox, Commitment, Reveal};

fn random_nonce() -> Vec<u8> {
    let mut buf = [0u8; 16];
    rand::thread_rng().fill_bytes(&mut buf);
    buf.to_vec()
}

fn main() {
    let mut bb = BallotBox::new();
    bb.register("alice");
    bb.register("bob");
    bb.register("carol");

    // Each voter picks a candidate locally and publishes only the commitment.
    let votes = [
        ("alice", "yes"),
        ("bob",   "no"),
        ("carol", "yes"),
    ];
    let mut secrets = Vec::new();
    for (voter, candidate) in votes {
        let nonce = random_nonce();
        let commitment = Commitment::new(candidate, &nonce);
        bb.commit(voter, commitment).expect("commit");
        secrets.push((voter, candidate.to_string(), nonce));
    }
    println!("Phase 1 (commit): {} ballots committed.", bb.committed_count());

    // Phase 2: each voter reveals.
    for (voter, candidate, nonce) in &secrets {
        bb.reveal(voter, Reveal { candidate: candidate.clone(), nonce: nonce.clone() })
            .expect("reveal");
    }

    let result = bb.tally().expect("tally");
    println!(
        "Phase 2 (reveal+tally): {}/{} revealed.",
        result.total_revealed, result.total_committed
    );
    for (candidate, count) in &result.counts {
        println!("  {candidate}: {count}");
    }
    println!("Commitment Merkle root: 0x{}", hex::encode(result.commitment_root));
}
