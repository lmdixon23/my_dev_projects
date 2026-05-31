use rust_quadratic_voting::{QvError, VotingSystem};

#[test]
fn chained_delegation_pools_credits() {
    let mut vs = VotingSystem::new();
    vs.register_voter("a", 4);
    vs.register_voter("b", 9);
    vs.register_voter("c", 16);
    // a -> b -> c. After both delegations, c holds 4 + 9 + 16 = 29.
    vs.delegate("a", "b").unwrap();
    vs.delegate("b", "c").unwrap();
    assert_eq!(vs.credits("a"), Some(0));
    assert_eq!(vs.credits("b"), Some(0));
    assert_eq!(vs.credits("c"), Some(29));
    assert!(matches!(vs.submit_vote("a", "X", 1), Err(QvError::HasDelegated(_))));
    assert!(matches!(vs.submit_vote("b", "X", 1), Err(QvError::HasDelegated(_))));
    vs.submit_vote("c", "X", 5).unwrap();
    assert_eq!(vs.tally().counts.get("X").copied(), Some(5));
}

#[test]
fn split_credits_across_two_candidates() {
    let mut vs = VotingSystem::new();
    vs.register_voter("a", 25);
    vs.submit_vote("a", "X", 3).unwrap(); // 9 credits
    vs.submit_vote("a", "Y", 4).unwrap(); // 16 credits
    assert_eq!(vs.credits("a"), Some(0));
    let result = vs.tally();
    assert_eq!(result.counts.get("X").copied(), Some(3));
    assert_eq!(result.counts.get("Y").copied(), Some(4));
}
