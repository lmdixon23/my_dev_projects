use std::collections::HashMap;

#[derive(Debug)]
struct User {
    id: String, // User ID field
    balance: f64,
    collateral: f64,
}

#[derive(Debug)]
struct Loan {
    borrower: String,
    amount: f64,
    interest_rate: f64,
    collateral: f64,
}

struct DefiLendingPlatform {
    users: HashMap<String, User>,
    loans: Vec<Loan>,
}

impl DefiLendingPlatform {
    fn new() -> Self {
        DefiLendingPlatform {
            users: HashMap::new(),
            loans: Vec::new(),
        }
    }

    fn register_user(&mut self, id: String, initial_balance: f64) {
        let user = User {
            id: id.clone(), // Using the id field here
            balance: initial_balance,
            collateral: 0.0,
        };
        self.users.insert(id.clone(), user);
        println!("User {} registered with initial balance: {}", id, initial_balance);
    }

    fn deposit_collateral(&mut self, user_id: &String, amount: f64) -> Result<(), &'static str> {
        if let Some(user) = self.users.get_mut(user_id) {
            user.collateral += amount;
            println!("User {} deposited collateral: {}", user.id, amount); // Logging user ID
            Ok(())
        } else {
            Err("User not found.")
        }
    }

    fn request_loan(&mut self, borrower_id: &String, amount: f64, interest_rate: f64) -> Result<(), &'static str> {
        if let Some(borrower) = self.users.get_mut(borrower_id) {
            let collateral_required = amount * 1.5; // Example: 150% collateral required
            if borrower.collateral >= collateral_required {
                borrower.collateral -= collateral_required;
                let loan = Loan {
                    borrower: borrower_id.clone(),
                    amount,
                    interest_rate,
                    collateral: collateral_required,
                };
                self.loans.push(loan);
                borrower.balance += amount;
                println!("Loan granted to user {}: amount {}, collateral {}", borrower.id, amount, collateral_required); // Logging user ID
                Ok(())
            } else {
                Err("Insufficient collateral.")
            }
        } else {
            Err("Borrower not found.")
        }
    }

    fn repay_loan(&mut self, borrower_id: &String, amount: f64) -> Result<(), &'static str> {
        if let Some(borrower) = self.users.get_mut(borrower_id) {
            let mut loan_repaid = false;
            for loan in &mut self.loans {
                if loan.borrower == *borrower_id && amount >= loan.amount * (1.0 + loan.interest_rate) {
                    borrower.balance -= amount;
                    borrower.collateral += loan.collateral;
                    loan_repaid = true;
                    println!("Loan repaid by user {}: amount {}", borrower.id, amount); // Logging user ID
                    break;
                }
            }

            if loan_repaid {
                self.loans.retain(|loan| loan.borrower != *borrower_id);
                Ok(())
            } else {
                Err("Loan repayment failed.")
            }
        } else {
            Err("Borrower not found.")
        }
    }

    fn check_balance(&self, user_id: &String) -> Result<f64, &'static str> {
        if let Some(user) = self.users.get(user_id) {
            println!("User {} balance checked: {}", user.id, user.balance); // Logging user ID
            Ok(user.balance)
        } else {
            Err("User not found.")
        }
    }

    fn check_collateral(&self, user_id: &String) -> Result<f64, &'static str> {
        if let Some(user) = self.users.get(user_id) {
            println!("User {} collateral checked: {}", user.id, user.collateral); // Logging user ID
            Ok(user.collateral)
        } else {
            Err("User not found.")
        }
    }
}

fn main() {
    let mut platform = DefiLendingPlatform::new();

    platform.register_user("Alice".to_string(), 1000.0);
    platform.register_user("Bob".to_string(), 500.0);

    platform.deposit_collateral(&"Alice".to_string(), 300.0).unwrap();
    platform.request_loan(&"Alice".to_string(), 200.0, 0.05).unwrap();

    println!("Alice's balance after loan: {}", platform.check_balance(&"Alice".to_string()).unwrap());
    println!("Alice's collateral after loan: {}", platform.check_collateral(&"Alice".to_string()).unwrap());

    platform.repay_loan(&"Alice".to_string(), 210.0).unwrap();

    println!("Alice's balance after repayment: {}", platform.check_balance(&"Alice".to_string()).unwrap());
    println!("Alice's collateral after repayment: {}", platform.check_collateral(&"Alice".to_string()).unwrap());
}
