import os
import random
import pandas as pd
import xgboost as xgb
import numpy as np

def generate_synthetic_data(num_samples=5000):
    """
    Generates synthetic training data mirroring the Kaggle UPI Fraud Dataset.
    Features: transaction_amount, hour_of_day, is_new_recipient, 
              amount_vs_30d_avg_ratio, device_changed, location_changed, 
              txn_frequency_last_1h, is_collect_request
    """
    print(f"Generating {num_samples} synthetic samples...")
    
    data = []
    for _ in range(num_samples):
        # Base distributions for normal transactions
        amount = np.random.exponential(scale=2000) + 10  # Most txns are small
        hour = int(np.random.normal(loc=14, scale=4)) % 24 # Most active during day
        is_new = int(random.random() < 0.15) # 15% to new recipients
        avg_ratio = np.random.lognormal(mean=0, sigma=0.5) 
        device_changed = int(random.random() < 0.05)
        location_changed = int(random.random() < 0.1)
        txn_freq = int(np.random.exponential(scale=1))
        is_collect = int(random.random() < 0.05)
        
        # Fraud logic (injecting anomalies)
        # We aim for ~5% fraud rate in synthetic data
        is_fraud = 0
        
        # Scenario 1: Late night large transfers to new recipients
        if hour < 6 or hour > 23:
            if amount > 50000 and is_new:
                is_fraud = int(random.random() < 0.8) # 80% chance it's fraud
                
        # Scenario 2: Device/Location changed + high ratio
        if device_changed and location_changed and avg_ratio > 3.0:
            is_fraud = int(random.random() < 0.9)
            
        # Scenario 3: Collect request spam
        if is_collect and amount > 10000 and is_new:
             is_fraud = int(random.random() < 0.7)
             
        # Scenario 4: Purely random fraud (noise)
        if not is_fraud and random.random() < 0.01:
            is_fraud = 1
            
        data.append([
            amount, hour, is_new, avg_ratio, device_changed, 
            location_changed, txn_freq, is_collect, is_fraud
        ])
        
    cols = [
        "transaction_amount", "hour_of_day", "is_new_recipient", 
        "amount_vs_30d_avg_ratio", "device_changed", "location_changed", 
        "txn_frequency_last_1h", "is_collect_request", "is_fraud"
    ]
    
    return pd.DataFrame(data, columns=cols)

def train_and_save():
    df = generate_synthetic_data(10000)
    
    X = df.drop("is_fraud", axis=1)
    y = df["is_fraud"]
    
    fraud_count = y.sum()
    print(f"Dataset generated. Fraud cases: {fraud_count}/{len(df)} ({fraud_count/len(df)*100:.1f}%)")
    
    # Calculate scale_pos_weight for class imbalance
    scale_pos_weight = (len(y) - fraud_count) / fraud_count if fraud_count > 0 else 1
    
    print("Training XGBoost model...")
    model = xgb.XGBClassifier(
        n_estimators=200, 
        max_depth=6, 
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42
    )
    
    model.fit(X, y)
    
    # Save to project root
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    model_path = os.path.join(root_dir, "upi_behavioral.json")
    
    model.save_model(model_path)
    print(f"Model saved successfully to: {model_path}")

if __name__ == "__main__":
    train_and_save()
