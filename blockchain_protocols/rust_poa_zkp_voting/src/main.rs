//! Demo: register authorities (each with an Ed25519 key), register voters,
//! submit signed votes, then mine a block via round-robin PoA leader
//! selection — sealed with the scheduled authority's signature — tally, and
//! verify the chain.

use std::collections::HashMap;

use ed25519_dalek::SigningKey;
use rand_core::OsRng;
use rust_poa_zkp_voting::Blockchain;

fn make_voter(bc: &mut Blockchain, id: &str, secret: &[u8]) -> SigningKey {
    let sk = SigningKey::generate(&mut OsRng);
    bc.register_voter(id, sk.verifying_key(), secret);
    sk
}

fn main() {
    let mut bc = Blockchain::new();

    // Authorized block producers, each with a keypair. Keep the signing keys
    // so the demo can seal a block with whichever authority's turn it is.
    let mut authority_keys: HashMap<String, SigningKey> = HashMap::new();
    for id in ["authority-A", "authority-B"] {
        let sk = SigningKey::generate(&mut OsRng);
        bc.register_authority(id, sk.verifying_key());
        authority_keys.insert(id.to_string(), sk);
    }

    let alice = make_voter(&mut bc, "alice", b"alice-secret-nonce");
    let bob = make_voter(&mut bc, "bob", b"bob-secret-nonce");

    let v1 = Blockchain::sign_vote(&alice, "alice", "Yes", 1, b"alice-secret-nonce");
    let v2 = Blockchain::sign_vote(&bob, "bob", "No", 1, b"bob-secret-nonce");
    bc.submit_vote(v1).expect("signed vote");
    bc.submit_vote(v2).expect("signed vote");

    // Round-robin: ask whose turn it is, then seal with that authority's key.
    let proposer = bc.current_proposer().expect("an authority is scheduled");
    let key = authority_keys.get(&proposer).expect("scheduled authority key");
    let idx = bc.mine_block(key).expect("mine");
    println!(
        "Mined block #{idx} (round-robin proposer = {}).",
        bc.chain()[idx as usize].proposer
    );

    let tally = bc.tally();
    println!("Tally:");
    for (c, n) in &tally {
        println!("  {c}: {n}");
    }

    bc.verify_integrity().expect("chain integrity");
    println!("Chain integrity check: OK (proposer schedule + signatures verified)");
}
