//! Minimal ink! counter contract.
//!
//! Prototype only: a single i32 with `get`, `increment`, `decrement`
//! messages. Demonstrates the basic ink! macro layout for a Substrate
//! smart contract. Not a portfolio piece — see prototypes/README.md.

#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract]
mod rust_ink_counter {
    #[ink(storage)]
    pub struct RustInkCounter {
        value: i32,
    }

    impl RustInkCounter {
        #[ink(constructor)]
        pub fn new(init_value: i32) -> Self {
            Self { value: init_value }
        }

        #[ink(message)]
        pub fn get(&self) -> i32 {
            self.value
        }

        #[ink(message)]
        pub fn increment(&mut self) {
            self.value = self.value.saturating_add(1);
        }

        #[ink(message)]
        pub fn decrement(&mut self) {
            self.value = self.value.saturating_sub(1);
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        #[ink::test]
        fn new_initializes_value() {
            let c = RustInkCounter::new(7);
            assert_eq!(c.get(), 7);
        }

        #[ink::test]
        fn increment_and_decrement_round_trip() {
            let mut c = RustInkCounter::new(0);
            c.increment();
            c.increment();
            c.decrement();
            assert_eq!(c.get(), 1);
        }

        #[ink::test]
        fn saturating_arithmetic_does_not_panic_on_overflow() {
            let mut c = RustInkCounter::new(i32::MAX);
            c.increment();   // saturates instead of panicking
            assert_eq!(c.get(), i32::MAX);

            let mut c = RustInkCounter::new(i32::MIN);
            c.decrement();   // saturates instead of panicking
            assert_eq!(c.get(), i32::MIN);
        }
    }
}
