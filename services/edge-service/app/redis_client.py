import os
import json
import redis.asyncio as redis

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

async def get_and_update_velocity(account_id: str, amount: float) -> dict:
    """
    Updates the transaction count and sums for an account in Redis.
    Returns the computed velocity features.
    """
    key_1h = f"vel:1h:{account_id}"
    key_24h = f"vel:24h:{account_id}"
    key_sum = f"sum:24h:{account_id}"

    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.incr(key_1h)
        pipe.expire(key_1h, 3600)  # 1 hour
        
        pipe.incr(key_24h)
        pipe.expire(key_24h, 86400) # 24 hours
        
        pipe.incrbyfloat(key_sum, amount)
        pipe.expire(key_sum, 86400)
        
        results = await pipe.execute()
    
    count_1h = results[0]
    count_24h = results[2]
    total_amount_24h = float(results[4])
    
    avg_txn_amount = (total_amount_24h - amount) / max(1, count_24h - 1) if count_24h > 1 else amount
    amount_vs_avg_ratio = amount / avg_txn_amount if avg_txn_amount > 0 else 1.0

    return {
        "sender_velocity_1h": int(count_1h),
        "sender_velocity_24h": int(count_24h),
        "amount_vs_avg_ratio": float(amount_vs_avg_ratio)
    }