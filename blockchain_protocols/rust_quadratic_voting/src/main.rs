use std::collections::HashMap;

#[derive(Debug, Clone)]
struct Voter {
    credits: u32,
    has_voted: bool,
    delegate: Option<String>, // For Liquid Democracy
}

impl Voter {
    fn new(credits: u32) -> Self {
        Voter {
            credits,
            has_voted: false,
            delegate: None,
        }
    }
}

struct VotingSystem {
    voters: HashMap<String, Voter>,
    votes: HashMap<String, u32>,
    delegations: HashMap<String, String>, // Maps voter ID to their delegate
}

impl VotingSystem {
    fn new() -> Self {
        VotingSystem {
            voters: HashMap::new(),
            votes: HashMap::new(),
            delegations: HashMap::new(),
        }
    }

    fn register_voter(&mut self, voter_id: String, credits: u32) {
        let voter = Voter::new(credits);
        self.voters.insert(voter_id, voter);
    }

    fn delegate_vote(&mut self, from: String, to: String) -> Result<(), &'static str> {
        if self.voters.contains_key(&from) && self.voters.contains_key(&to) {
            self.delegations.insert(from.clone(), to.clone());
            Ok(())
        } else {
            Err("Either delegator or delegatee is not registered.")
        }
    }

    fn submit_vote(&mut self, voter_id: String, candidate: String, num_votes: u32) -> Result<(), &'static str> {
        if let Some(voter) = self.voters.get_mut(&voter_id) {
            if voter.has_voted {
                return Err("Voter has already voted.");
            }

            let cost = num_votes * num_votes; // Quadratic cost
            if voter.credits >= cost {
                voter.credits -= cost;
                voter.has_voted = true;

                let counter = self.votes.entry(candidate.clone()).or_insert(0);
                *counter += num_votes;

                // Handle Liquid Democracy
                if let Some(delegate) = voter.delegate.clone() {
                    let delegate_votes = self.votes.entry(delegate).or_insert(0);
                    *delegate_votes += num_votes;
                }

                Ok(())
            } else {
                Err("Insufficient credits.")
            }
        } else {
            Err("Voter not registered.")
        }
    }

    fn tally_votes(&self) -> HashMap<String, u32> {
        self.votes.clone()
    }
}

fn main() {
    let mut voting_system = VotingSystem::new();

    // Register voters
    voting_system.register_voter("voter1".to_string(), 9); // 9 credits
    voting_system.register_voter("voter2".to_string(), 16); // 16 credits
    voting_system.register_voter("voter3".to_string(), 25); // 25 credits

    // Delegation
    match voting_system.delegate_vote("voter1".to_string(), "voter2".to_string()) {
        Ok(_) => println!("Delegation successful."),
        Err(e) => println!("Error in delegation: {}", e),
    }

    // Submit votes
    match voting_system.submit_vote("voter2".to_string(), "Alice".to_string(), 3) { // 9 credits used (3^2)
        Ok(_) => println!("Vote submitted successfully."),
        Err(e) => println!("Error submitting vote: {}", e),
    }

    match voting_system.submit_vote("voter3".to_string(), "Bob".to_string(), 4) { // 16 credits used (4^2)
        Ok(_) => println!("Vote submitted successfully."),
        Err(e) => println!("Error submitting vote: {}", e),
    }

    // Tally votes
    let results = voting_system.tally_votes();
    println!("Voting results: {:?}", results);
}
