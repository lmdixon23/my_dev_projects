import pandas as pd
import yaml
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def load_and_preprocess_data(folder_path, label):
    all_data = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            data = pd.read_csv(file_path)
            
            # Drop rows with missing values
            data.dropna(inplace=True)
            
            # Add battery pack type label
            data['pack_type'] = label
            
            # Convert time to a more useful feature
            data['relative time'] = data['relative time'] / 3600  # Convert to hours

            # Example feature engineering: calculate average current
            if 'current load' in data.columns:
                data['avg_current'] = data['current load'].mean()
            
            all_data.append(data)
    
    return pd.concat(all_data, ignore_index=True)

# Load data from each folder with appropriate labels
regular_data = load_and_preprocess_data('data/battery_alt_dataset/regular_alt_batteries', 'regular')
recommissioned_data = load_and_preprocess_data('data/battery_alt_dataset/recommissioned_batteries', 'recommissioned')

# Combine all data
data = pd.concat([regular_data, recommissioned_data], ignore_index=True)

# Handle categorical data (e.g., 'pack_type')
data = pd.get_dummies(data, columns=['pack_type'])

# Feature Engineering
data['failure'] = data['relative time'].apply(lambda x: 1 if x > 1000 else 0)  # Example threshold for failure

# Drop irrelevant columns
data = data.drop(['start time', 'mode'], axis=1, errors='ignore')

# Split data
X = data.drop('failure', axis=1)
y = data['failure']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=config['training']['test_size'], random_state=config['training']['random_state'])

# Normalize data
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Save preprocessed data
pd.DataFrame(X_train).to_csv('data/X_train.csv', index=False)
pd.DataFrame(X_test).to_csv('data/X_test.csv', index=False)
pd.DataFrame(y_train).to_csv('data/y_train.csv', index=False)
pd.DataFrame(y_test).to_csv('data/y_test.csv', index=False)

print("Data preprocessing complete.")