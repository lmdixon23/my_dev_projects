use std::collections::HashMap;
use std::time::{Duration, SystemTime};
use async_std::task;
use log::{info, warn};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone)]
struct Asset {
    id: String,
    name: String,
    amount: f64,
    wrapped: bool,
}

#[derive(Debug, Clone)]
struct HTLC {
    hash: String,
    timeout: SystemTime,
}

impl HTLC {
    fn new(secret: &str, duration: Duration) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(secret);
        let hash = format!("{:x}", hasher.finalize());

        HTLC {
            hash,
            timeout: SystemTime::now() + duration,
        }
    }

    fn verify_hash(&self, provided_hash: &str) -> bool {
        if SystemTime::now() > self.timeout {
            warn!("HTLC has expired.");
            false
        } else if &self.hash == provided_hash {
            info!("HTLC verification succeeded.");
            true
        } else {
            warn!("HTLC hash mismatch.");
            false
        }
    }
}

#[derive(Debug)]
struct Blockchain {
    name: String,
    assets: HashMap<String, Asset>,
}

impl Blockchain {
    fn new(name: &str) -> Self {
        Blockchain {
            name: name.to_string(),
            assets: HashMap::new(),
        }
    }

    fn add_asset(&mut self, asset: Asset) {
        self.assets.insert(asset.id.clone(), asset);
    }

    fn transfer_asset(&mut self, asset_id: &str, to_chain: &mut Blockchain, htlc: &HTLC) -> Result<(), &'static str> {
        if let Some(asset) = self.assets.get(asset_id) {
            if htlc.verify_hash(&htlc.hash) {
                info!(
                    "Transferring {} {} from {} to {}",
                    asset.amount, asset.name, self.name, to_chain.name
                );
                let mut transferred_asset = asset.clone();
                transferred_asset.wrapped = true;
                to_chain.add_asset(transferred_asset);
                self.assets.remove(asset_id);
                Ok(())
            } else {
                Err("HTLC verification failed.")
            }
        } else {
            Err("Asset not found.")
        }
    }

    fn get_asset(&self, asset_id: &str) -> Option<&Asset> {
        self.assets.get(asset_id)
    }
}

async fn async_transfer(
    from_chain: &mut Blockchain,
    to_chain: &mut Blockchain,
    asset_id: &str,
    htlc: HTLC,
) -> Result<(), &'static str> {
    task::sleep(Duration::from_secs(2)).await; // Simulate network delay
    from_chain.transfer_asset(asset_id, to_chain, &htlc)
}

fn main() {
    env_logger::init();

    let mut ethereum = Blockchain::new("Ethereum");
    let mut polkadot = Blockchain::new("Polkadot");

    let eth_asset = Asset {
        id: "eth-001".to_string(),
        name: "Ethereum".to_string(),
        amount: 10.0,
        wrapped: false,
    };

    ethereum.add_asset(eth_asset);

    let secret = "supersecret";
    let htlc = HTLC::new(secret, Duration::from_secs(60));

    println!("Before Transfer:");
    println!("Ethereum chain: {:?}", ethereum.get_asset("eth-001"));
    println!("Polkadot chain: {:?}", polkadot.get_asset("eth-001"));

    let transfer_result = task::block_on(async_transfer(&mut ethereum, &mut polkadot, "eth-001", htlc.clone()));

    match transfer_result {
        Ok(_) => info!("Transfer successful"),
        Err(e) => warn!("Transfer failed: {}", e),
    }

    println!("\nAfter Transfer:");
    println!("Ethereum chain: {:?}", ethereum.get_asset("eth-001"));
    println!("Polkadot chain: {:?}", polkadot.get_asset("eth-001"));
}