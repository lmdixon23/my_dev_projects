//! Minimal Merkle root over an ordered list of 32-byte leaves.
//!
//! Pairs are hashed left||right with SHA-256. Odd levels duplicate the
//! last leaf (Bitcoin-style). Sufficient for "give me one number that
//! summarizes the committed-ballot set"; not designed for inclusion-proof
//! generation.

use sha2::{Digest, Sha256};

pub type Hash = [u8; 32];

pub fn merkle_root(leaves: &[Hash]) -> Option<Hash> {
    if leaves.is_empty() {
        return None;
    }
    let mut layer: Vec<Hash> = leaves.to_vec();
    while layer.len() > 1 {
        let mut next = Vec::with_capacity((layer.len() + 1) / 2);
        for pair in layer.chunks(2) {
            let mut hasher = Sha256::new();
            hasher.update(pair[0]);
            // Duplicate the last element if the layer is odd.
            hasher.update(if pair.len() == 2 { &pair[1] } else { &pair[0] });
            let mut out = [0u8; 32];
            out.copy_from_slice(&hasher.finalize());
            next.push(out);
        }
        layer = next;
    }
    Some(layer[0])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn root_of_one_leaf_is_the_leaf() {
        let h = [1u8; 32];
        assert_eq!(merkle_root(&[h]), Some(h));
    }

    #[test]
    fn order_matters() {
        let a = [1u8; 32];
        let b = [2u8; 32];
        assert_ne!(merkle_root(&[a, b]), merkle_root(&[b, a]));
    }

    #[test]
    fn empty_input_returns_none() {
        assert_eq!(merkle_root(&[]), None);
    }
}
