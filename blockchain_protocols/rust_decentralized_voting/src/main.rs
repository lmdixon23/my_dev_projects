use std::collections::HashMap;

#[derive(Debug, Clone)]
struct Vote {
    voter_id: String,
    candidate: String,
}

#[derive(Debug)]
struct Voter {
    id: String,
    has_voted: bool,
}

impl Voter {
    fn new(id: String) -> Self {
        Voter {
            id,
            has_voted: false,
        }
    }

    fn get_id(&self) -> &String {
        &self.id
    }
}

impl Vote {
    fn new(voter_id: String, candidate: String) -> Self {
        Vote { voter_id, candidate }
    }

    fn get_voter_id(&self) -> &String {
        &self.voter_id
    }
}

struct VotingSystem {
    voters: HashMap<String, Voter>,
    votes: Vec<Vote>,
}

impl VotingSystem {
    fn new() -> Self {
        VotingSystem {
            voters: HashMap::new(),
            votes: Vec::new(),
        }
    }

    fn register_voter(&mut self, voter_id: String) {
        let voter = Voter::new(voter_id.clone());
        self.voters.insert(voter_id, voter);
    }

    fn submit_vote(&mut self, voter_id: String, candidate: String) -> Result<(), &'static str> {
        if let Some(voter) = self.voters.get_mut(&voter_id) {
            if voter.has_voted {
                return Err("Voter has already voted.");
            } else {
                voter.has_voted = true;
                let vote = Vote::new(voter_id.clone(), candidate.clone());
                
                // Log the voter ID and candidate
                println!("Voter ID: {} has voted for {}", voter.get_id(), candidate);

                self.votes.push(vote);
                Ok(())
            }
        } else {
            Err("Voter not registered.")
        }
    }

    fn tally_votes(&self) -> HashMap<String, usize> {
        let mut results = HashMap::new();
        for vote in &self.votes {
            // Log the voter ID for each vote during tallying
            println!("Counting vote from Voter ID: {}", vote.get_voter_id());

            let counter = results.entry(vote.candidate.clone()).or_insert(0);
            *counter += 1;
        }
        results
    }
}

fn main() {
    let mut voting_system = VotingSystem::new();

    // Register voters
    voting_system.register_voter("voter1".to_string());
    voting_system.register_voter("voter2".to_string());
    voting_system.register_voter("voter3".to_string());

    // Submit votes
    match voting_system.submit_vote("voter1".to_string(), "Alice".to_string()) {
        Ok(_) => println!("Vote submitted successfully."),
        Err(e) => println!("Error submitting vote: {}", e),
    }

    match voting_system.submit_vote("voter2".to_string(), "Bob".to_string()) {
        Ok(_) => println!("Vote submitted successfully."),
        Err(e) => println!("Error submitting vote: {}", e),
    }

    match voting_system.submit_vote("voter1".to_string(), "Charlie".to_string()) {
        Ok(_) => println!("Vote submitted successfully."),
        Err(e) => println!("Error submitting vote: {}", e),
    }

    // Tally votes
    let results = voting_system.tally_votes();
    println!("Voting results: {:?}", results);
}
