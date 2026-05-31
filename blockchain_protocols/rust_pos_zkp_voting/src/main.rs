//! Demo: register voters with Ed25519 keys, submit signed votes, mine a
//! block via stake-weighted PoS leader selection, tally, verify chain.

use ed25519_dalek::SigningKey;
use rand_core::OsRng;
use rust_pos_zkp_voting::Blockchain;

fn make_voter(bc: &mut Blockchain, id: &str, secret: &[u8]) -> SigningKey {
    let sk = SigningKey::generate(&mut OsRng);
    bc.register_voter(id, sk.verifying_key(), secret);
    sk
}

fn main() {
    let mut bc = Blockchain::with_seed(123);
    bc.register_validator("validator-A", 100);
    bc.register_validator("validator-B", 50);

    let alice = make_voter(&mut bc, "alice", b"alice-secret-nonce");
    let bob   = make_voter(&mut bc, "bob",   b"bob-secret-nonce");

    let v1 = Blockchain::sign_vote(&alice, "alice", "Yes", 1, b"alice-secret-nonce");
    let v2 = Blockchain::sign_vote(&bob,   "bob",   "No",  1, b"bob-secret-nonce");
    bc.submit_vote(v1).expect("signed vote");
    bc.submit_vote(v2).expect("signed vote");

    let idx = bc.mine_block().expect("mine");
    println!("Mined block #{idx} (miner = {}).", bc.chain()[idx as usize].miner);

    let tally = bc.tally();
    println!("Tally:");
    for (c, n) in &tally { println!("  {c}: {n}"); }

    bc.verify_integrity().expect("chain integrity");
    println!("Chain integrity check: OK");
}
