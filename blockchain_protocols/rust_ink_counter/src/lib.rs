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
            self.value += 1;
        }

        #[ink(message)]
        pub fn decrement(&mut self) {
            self.value -= 1;
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        #[ink::test]
        fn it_works() {
            let mut contract = RustInkCounter::new(0);
            assert_eq!(contract.get(), 0);
            contract.increment();
            assert_eq!(contract.get(), 1);
            contract.decrement();
            assert_eq!(contract.get(), 0);
        }
    }
}