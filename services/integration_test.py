import asyncio
import httpx
import json
import time

EDGE_URL = "http://localhost:8001/score"

async def run_traffic():
    print("Starting integration traffic test...")
    async with httpx.AsyncClient() as client:
        # A normal transaction
        req1 = {
            "transaction_id": f"txn_{int(time.time()*1000)}",
            "timestamp": time.time(),
            "sender_account_id": "ACC_NORMAL_01",
            "receiver_account_id": "ACC_MERCH_01",
            "amount": 25.50,
            "channel": "MOBILE",
            "sender_bank": "BofA",
            "receiver_bank": "Chase",
            "sender_geo_city": "New York",
            "sender_geo_state": "NY",
            "sender_geo_latitude": 40.7,
            "sender_geo_longitude": -74.0,
            "receiver_geo_city": "New York",
            "receiver_geo_state": "NY",
            "receiver_geo_latitude": 40.7,
            "receiver_geo_longitude": -74.0,
            "sender_account_type": "CHECKING",
            "receiver_account_type": "SAVINGS",
            "is_fraud": False
        }
        
        # A huge transaction (spikes rule engine)
        req2 = {
            "transaction_id": f"txn_{int(time.time()*1000)+1}",
            "timestamp": time.time() + 1,
            "sender_account_id": "ACC_WHALE_01",
            "receiver_account_id": "ACC_FOREIGN_02",
            "amount": 600000.00,
            "channel": "WIRE",
            "sender_bank": "Citi",
            "receiver_bank": "HSBC",
            "sender_geo_city": "Los Angeles",
            "sender_geo_state": "CA",
            "sender_geo_latitude": 34.0,
            "sender_geo_longitude": -118.2,
            "receiver_geo_city": "London",
            "receiver_geo_state": "UK",
            "receiver_geo_latitude": 51.5,
            "receiver_geo_longitude": -0.1,
            "sender_account_type": "SAVINGS",
            "receiver_account_type": "SAVINGS",
            "is_fraud": True
        }

        # A velocity spike (same sender many times)
        velocity_reqs = []
        for i in range(15): # >10 triggers 1h velocity rule
            velocity_reqs.append({
                "transaction_id": f"txn_vel_{int(time.time()*1000)+i}",
                "timestamp": time.time() + i,
                "sender_account_id": "ACC_SPAM_01",
                "receiver_account_id": f"ACC_MULE_{i}",
                "amount": 100.0,
                "channel": "WEB",
                "sender_bank": "Wells",
                "receiver_bank": "Unknown",
                "sender_geo_city": "Chicago",
                "sender_geo_state": "IL",
                "sender_geo_latitude": 41.8,
                "sender_geo_longitude": -87.6,
                "receiver_geo_city": "Miami",
                "receiver_geo_state": "FL",
                "receiver_geo_latitude": 25.7,
                "receiver_geo_longitude": -80.1,
                "sender_account_type": "CHECKING",
                "receiver_account_type": "CHECKING",
                "is_fraud": True
            })

        print("Sending normal transaction...")
        res = await client.post(EDGE_URL, json=req1)
        print("Response:", res.json())
        time.sleep(0.5)
        
        print("Sending whale transaction...")
        res = await client.post(EDGE_URL, json=req2)
        print("Response:", res.json())
        time.sleep(0.5)
        
        print("Sending velocity attack (15 txns)...")
        for vr in velocity_reqs:
            res = await client.post(EDGE_URL, json=vr)
            print(f"Velocity txn {vr['transaction_id']} response: {res.status_code}")
            
        print("Done. Check Dashboard UI for Risk Score websocket updates!")

if __name__ == "__main__":
    asyncio.run(run_traffic())