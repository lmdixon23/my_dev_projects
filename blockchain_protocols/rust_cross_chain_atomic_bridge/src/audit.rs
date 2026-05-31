//! Append-only audit log of bridge domain events.

use std::time::SystemTime;

use log::debug;
use uuid::Uuid;

#[derive(Debug, Clone)]
pub enum AuditEvent {
    AssetMinted     { chain: String, asset_id: String, amount: u64 },
    AssetLocked     { chain: String, lock_id: Uuid, asset_id: String, hash: String },
    AssetReleased   { chain: String, lock_id: Uuid, asset_id: String },
    AssetRefunded   { chain: String, lock_id: Uuid, asset_id: String },
    WrappedMinted   { chain: String, asset_id: String, origin: String, amount: u64 },
    WrappedBurned   { chain: String, asset_id: String },
    MessageSent     { from: String, to: String, kind: &'static str },
    MessageReceived { at: String, kind: &'static str },
}

#[derive(Debug, Default)]
pub struct AuditLog {
    events: Vec<(SystemTime, AuditEvent)>,
}

impl AuditLog {
    pub fn record(&mut self, e: AuditEvent) {
        debug!("audit: {:?}", e);
        self.events.push((SystemTime::now(), e));
    }
    pub fn events(&self) -> &[(SystemTime, AuditEvent)] { &self.events }
    pub fn len(&self) -> usize { self.events.len() }
    pub fn is_empty(&self) -> bool { self.events.is_empty() }
}
