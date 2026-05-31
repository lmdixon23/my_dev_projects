//! Demo: three voters, one delegation, quadratic cost, tallied results.

use rust_quadratic_voting::VotingSystem;

fn main() {
    let mut vs = VotingSystem::new();
    vs.register_voter("voter1", 9);
    vs.register_voter("voter2", 16);
    vs.register_voter("voter3", 25);

    // voter1 delegates to voter2.
    vs.delegate("voter1", "voter2").expect("delegate");
    println!("After delegation: voter2 holds {} credits.", vs.credits("voter2").unwrap());

    vs.submit_vote("voter2", "Alice", 5).expect("vote"); // 25 credits
    vs.submit_vote("voter3", "Bob",   4).expect("vote"); // 16 credits

    let result = vs.tally();
    println!("Tally:");
    for (candidate, count) in &result.counts {
        println!("  {candidate}: {count}");
    }
    println!("Total votes cast: {}", result.total_votes_cast);
}
