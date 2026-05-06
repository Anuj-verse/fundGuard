import pandas as pd
import numpy as np
import xgboost as xgb
import math
from datetime import datetime
import json
from pathlib import Path

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return 0.0

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def extract_features(df):
    """
    Extracts 18 features from the dataset.
    """
    print("Extracting features...")
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
    
    # 1. amount
    # already exists
    
    # 2. log_amount
    df['log_amount'] = np.log1p(df['amount'])
    
    # 3. hour_of_day
    df['hour_of_day'] = df['timestamp'].dt.hour
    
    # 4. day_of_week
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # 5. is_weekend
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # 6. channel_encoded
    channel_map = {'UPI': 0, 'IMPS': 1, 'NEFT': 2, 'RTGS': 3, 'ATM': 4, 'POS': 5, 'INTERNET_BANKING': 6}
    df['channel_encoded'] = df['channel'].map(channel_map).fillna(-1).astype(int)
    
    # Group by logic for velocities
    # 7. sender_velocity_1h
    df['sender_velocity_1h'] = np.random.randint(1, 10, size=len(df))
    
    # 8. sender_velocity_24h
    df['sender_velocity_24h'] = np.random.randint(1, 20, size=len(df))
    
    # 9. receiver_velocity_1h
    df['receiver_velocity_1h'] = np.random.randint(1, 5, size=len(df))
    
    # 10. amount_vs_avg_ratio
    # Mocked by comparing to global avg for simplicity or just a random static value
    global_avg = df['amount'].mean()
    df['amount_vs_avg_ratio'] = df['amount'] / (global_avg + 1e-5)
    
    # 11. is_new_account
    # Mock
    df['is_new_account'] = 0
    
    # 12. device_change_flag
    df['device_change_flag'] = 0
    
    # 13. geo_distance_km
    df['geo_distance_km'] = df.apply(lambda row: haversine_distance(row['sender_geo_latitude'], row['sender_geo_longitude'], row['receiver_geo_latitude'], row['receiver_geo_longitude']), axis=1)
    
    # 14. is_international
    df['is_international'] = (df['sender_geo_state'] != df['receiver_geo_state']).astype(int) # simplistic heuristic
    
    # 15. structuring_flag (amount near 10L, e.g., 9.9L)
    df['structuring_flag'] = ((df['amount'] > 950000) & (df['amount'] < 1000000)).astype(int)
    
    # 16. round_amount_flag
    df['round_amount_flag'] = (df['amount'] % 1000 == 0).astype(int)
    
    # 17. beneficiary_risk_score
    df['beneficiary_risk_score'] = np.random.uniform(0, 1, size=len(df))
    
    # 18. account_age_days
    df['account_age_days'] = np.random.randint(10, 1000, size=len(df))
    
    # Convert bools to ints
    if 'is_fraud' in df.columns:
        df['is_fraud'] = df['is_fraud'].astype(int)
    else:
        df['is_fraud'] = 0

    feature_cols = [
        'amount', 'log_amount', 'hour_of_day', 'day_of_week', 'is_weekend', 
        'channel_encoded', 'sender_velocity_1h', 'sender_velocity_24h', 
        'receiver_velocity_1h', 'amount_vs_avg_ratio', 'is_new_account', 
        'device_change_flag', 'geo_distance_km', 'is_international', 
        'structuring_flag', 'round_amount_flag', 'beneficiary_risk_score', 
        'account_age_days'
    ]
    
    return df[feature_cols].fillna(0), df['is_fraud']

def main():
    data_path = Path("/home/anuj-gope/fundguard/fundguard/data/generator/data/output/transactions.csv")
    if not data_path.exists():
        print(f"Data file {data_path} not found. Ensure synthetic data generator has run.")
        return
        
    print(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    X, y = extract_features(df)
    
    print(f"Training XGBoost on {len(X)} rows...")
    model = xgb.XGBClassifier(
        n_estimators=100, 
        max_depth=6, 
        learning_rate=0.1,
        objective='binary:logistic',
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X, y)
    
    # Save the model
    out_dir = Path("models")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "xgboost_model.json"
    model.save_model(out_path)
    print(f"Model saved to {out_path}")

if __name__ == "__main__":
    main()
