import pandas as pd

# Create sample sales data
data = {
    "OrderID": [1001, 1002, 1003, 1004, 1005],
    "OrderDate": ["2023-08-01", "2023-08-02", "2023-08-03", "2023-08-04", "2023-08-05"],
    "CustomerID": [501, 502, 503, 504, 505],
    "ProductID": [101, 102, 103, 104, 105],
    "ProductName": ["Laptop", "Smartphone", "Headphones", "Monitor", "Keyboard"],
    "Quantity": [1, 2, 1, 3, 5],
    "UnitPrice": [1000.00, 800.00, 200.00, 150.00, 50.00],
    "TotalPrice": [1000.00, 1600.00, 200.00, 450.00, 250.00]
}

# Create DataFrame and save as CSV
sales_data = pd.DataFrame(data)
sales_data.to_csv('sales_data.csv', index=False)