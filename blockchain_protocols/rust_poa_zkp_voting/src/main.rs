use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use rand::Rng;
use md5;

#[derive(Debug, Clone)]
struct Vote {
    voter_id: String,
    candidate: String,
    weight: u64,
    timestamp: u64,
    zkp: String, // Zero-Knowledge Proof for eligibility
    signature: String,
}

#[derive(Debug)]
struct Voter {
    id: String,
    public_key: String,
    has_voted: bool,
    delegate: Option<String>,
}

#[derive(Debug, Clone)]
struct Block {
    index: u64,
    timestamp: u64,
    previous_hash: String,
    hash: String,
    votes: Vec<Vote>,
}

#[derive(Debug)]
struct Validator {
    id: String,
    stake: u64,  // Amount of cryptocurrency staked
    is_active: bool,
}

#[derive(Debug)]
struct Blockchain {
    chain: Vec<Block>,
    pending_votes: Vec<Vote>,
    validators: HashMap<String, Validator>, // Validators for PoS
    voters: HashMap<String, Voter>,  // Registered voters
}

impl Voter {
    fn new(id: String, public_key: String) -> Self {
        println!("Creating voter with ID: {} and Public Key: {}", id, public_key);
        Voter {
            id,
            public_key,
            has_voted: false,
            delegate: None,
        }
    }
}

impl Vote {
    fn new(voter_id: String, candidate: String, weight: u64, zkp: String, signature: String) -> Self {
        Vote {
            voter_id,
            candidate,
            weight,
            timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            zkp,
            signature,
        }
    }
}

impl Blockchain {
    fn new() -> Self {
        let mut blockchain = Blockchain {
            chain: Vec::new(),
            pending_votes: Vec::new(),
            validators: HashMap::new(),
            voters: HashMap::new(),
        };

        // Create and add the genesis block
        let genesis_block = blockchain.create_genesis_block();
        blockchain.chain.push(genesis_block);

        blockchain
    }

    fn create_genesis_block(&mut self) -> Block {
        Block {
            index: 0,
            timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            previous_hash: "0".to_string(),
            hash: "genesis_hash".to_string(),
            votes: Vec::new(),
        }
    }

    fn register_voter(&mut self, voter_id: String, public_key: String) {
        let voter = Voter::new(voter_id.clone(), public_key.clone());
        // Directly use the fields in a log statement
        println!("Registered voter with ID: {}, Public Key: {}", voter.id, voter.public_key);
        self.voters.insert(voter_id, voter);
    }

    fn register_validator(&mut self, validator_id: String, stake: u64) {
        let validator = Validator {
            id: validator_id,
            stake,
            is_active: true,
        };
        self.validators.insert(validator.id.clone(), validator);
    }

    fn delegate_vote(&mut self, voter_id: String, delegate_id: String) -> Result<(), &'static str> {
        if let Some(_delegate) = self.voters.get(&delegate_id) {
            if let Some(voter) = self.voters.get_mut(&voter_id) {
                if voter.has_voted {
                    return Err("Voter has already voted.");
                }
                voter.delegate = Some(delegate_id.clone());
                println!("Voter {} has delegated their vote to {}", voter_id, delegate_id);
                Ok(())
            } else {
                Err("Voter is not registered.")
            }
        } else {
            Err("Delegate is not registered.")
        }
    }
    

    fn submit_vote(&mut self, voter_id: String, candidate: String, weight: u64, zkp: String, signature: String) -> Result<(), &'static str> {
        if let Some(voter) = self.voters.get_mut(&voter_id) {
            if voter.has_voted {
                return Err("Voter has already voted.");
            }
            voter.has_voted = true;
    
            let vote = Vote::new(voter_id.clone(), candidate, weight, zkp, signature.clone());
            println!("Vote submitted by Voter ID: {}, Signature: {}, Timestamp: {}", vote.voter_id, vote.signature, vote.timestamp);
    
            if self.validate_zkp(&vote.zkp) {
                self.pending_votes.push(vote);
                Ok(())
            } else {
                Err("Invalid ZKP.")
            }
        } else {
            Err("Voter not registered.")
        }
    }

    fn validate_zkp(&self, _zkp: &String) -> bool {
        true
    }

    fn select_validator(&self) -> Option<&Validator> {
        let active_validators: Vec<&Validator> = self.validators.values().filter(|v| v.is_active).collect();
        let total_stake: u64 = active_validators.iter().map(|v| v.stake).sum();
        let mut rng = rand::thread_rng();
        let selected_stake: u64 = rng.gen_range(0..total_stake);

        let mut cumulative_stake = 0;
        for validator in active_validators {
            cumulative_stake += validator.stake;
            if cumulative_stake >= selected_stake {
                println!("Selected Validator ID: {} with Stake: {}", validator.id, validator.stake);
                return Some(validator);
            }
        }
        None
    }

    fn create_block(&mut self, previous_hash: String) -> Block {
        let block = Block {
            index: self.chain.len() as u64,
            timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            previous_hash,
            hash: String::new(), // To be calculated later
            votes: self.pending_votes.clone(),
        };

        self.pending_votes.clear();
        block
    }

    fn hash_block(&mut self, block: &Block) -> String {
        let block_content = format!(
            "{}{}{}{:?}",
            block.index, block.timestamp, block.previous_hash, block.votes
        );

        format!("{:x}", md5::compute(block_content))
    }

    fn add_block(&mut self, block: Block) {
        let mut new_block = block.clone();
        new_block.hash = self.hash_block(&new_block);
        self.chain.push(new_block);
    }

    fn consensus(&mut self) {
        let selected_validator_id = self.select_validator().map(|validator| validator.id.clone());
        let previous_block_hash = self.chain.last().map(|block| block.hash.clone());

        if let (Some(validator_id), Some(previous_hash)) = (selected_validator_id, previous_block_hash) {
            if !self.pending_votes.is_empty() {
                let new_block = self.create_block(previous_hash);
                self.add_block(new_block);
                println!("Block mined by validator {}", validator_id);
            }
        }
    }

    fn tally_votes(&self) -> HashMap<String, u64> {
        let mut results = HashMap::new();
        for block in &self.chain {
            for vote in &block.votes {
                let counter = results.entry(vote.candidate.clone()).or_insert(0);
                *counter += vote.weight;
            }
        }
        results
    }

    fn deploy_smart_contract(&self) {
        println!("Smart contract deployed to manage voting process.");
    }
}

fn main() {
    let mut blockchain = Blockchain::new();

    // Register voters
    blockchain.register_voter("voter1".to_string(), "public_key_1".to_string());
    blockchain.register_voter("voter2".to_string(), "public_key_2".to_string());
    blockchain.register_voter("voter3".to_string(), "public_key_3".to_string());

    // Register validators with stakes
    blockchain.register_validator("validator1".to_string(), 100);
    blockchain.register_validator("validator2".to_string(), 50);

    // Delegation
    match blockchain.delegate_vote("voter1".to_string(), "voter2".to_string()) {
        Ok(_) => println!("Delegation successful."),
        Err(e) => println!("Error in delegation: {}", e),
    }

    // Submit votes with ZKP
    match blockchain.submit_vote("voter2".to_string(), "Alice".to_string(), 3, "zkp_2".to_string(), "signature_2".to_string()) {
        Ok(_) => println!("Vote submitted successfully."),
        Err(e) => println!("Error submitting vote: {}", e),
    }

    match blockchain.submit_vote("voter3".to_string(), "Bob".to_string(), 4, "zkp_3".to_string(), "signature_3".to_string()) {
        Ok(_) => println!("Vote submitted successfully."),
        Err(e) => println!("Error submitting vote: {}", e),
    }

    // Perform consensus and mine the block
    blockchain.consensus();

    // Tally votes
    let results = blockchain.tally_votes();
    println!("Voting results: {:?}", results);

    // Deploy smart contract (placeholder)
    blockchain.deploy_smart_contract();
}
