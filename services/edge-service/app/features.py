import numpy as np
import math
from app.schemas import TransactionRequest

class FeatureExtractor:
    def __init__(self):
        self.channel_map = {'UPI': 0, 'IMPS': 1, 'NEFT': 2, 'RTGS': 3, 'ATM': 4, 'POS': 5, 'INTERNET_BANKING': 6}

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return 0.0
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def extract(self, req: TransactionRequest) -> np.ndarray:
        amount = req.amount
        log_amount = math.log1p(amount)
        hour_of_day = req.timestamp.hour
        day_of_week = req.timestamp.weekday()
        is_weekend = 1 if day_of_week in (5, 6) else 0
        channel_encoded = self.channel_map.get(req.channel, -1)
        
        # Mocks or provided metrics
        sender_velocity_1h = req.sender_velocity_1h if req.sender_velocity_1h is not None else 1
        sender_velocity_24h = req.sender_velocity_24h if req.sender_velocity_24h is not None else 1
        receiver_velocity_1h = req.receiver_velocity_1h if req.receiver_velocity_1h is not None else 1
        amount_vs_avg_ratio = req.amount_vs_avg_ratio if req.amount_vs_avg_ratio is not None else 1.0
        is_new_account = req.is_new_account if req.is_new_account is not None else 0
        device_change_flag = req.device_change_flag if req.device_change_flag is not None else 0
        
        geo_distance_km = self.haversine_distance(
            req.sender_geo_latitude, req.sender_geo_longitude, 
            req.receiver_geo_latitude, req.receiver_geo_longitude
        )
        
        is_international = 1 if (req.sender_geo_state and req.receiver_geo_state and req.sender_geo_state != req.receiver_geo_state) else 0
        
        # structuring_flag (amount near 10L, e.g., 9.9L)
        structuring_flag = 1 if (950000 < amount < 1000000) else 0
        
        # round_amount_flag
        round_amount_flag = 1 if (amount % 1000 == 0) else 0
        
        beneficiary_risk_score = req.beneficiary_risk_score if req.beneficiary_risk_score is not None else 0.5
        account_age_days = req.account_age_days if req.account_age_days is not None else 100
        
        features = [
            amount, log_amount, hour_of_day, day_of_week, is_weekend,
            channel_encoded, sender_velocity_1h, sender_velocity_24h,
            receiver_velocity_1h, amount_vs_avg_ratio, is_new_account,
            device_change_flag, geo_distance_km, is_international,
            structuring_flag, round_amount_flag, beneficiary_risk_score,
            account_age_days
        ]
        
        return np.array([features], dtype=np.float32)
