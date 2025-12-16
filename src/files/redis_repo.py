import redis
import json
#! Redis repository for storing and retrieving deviation data
class DeviationRedisRepository:
    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )

    def save_deviation(self, deviation_id: str, data: dict):
        key = f"deviation:{deviation_id}"
        self.client.set(key, json.dumps(data))

    def get_deviation(self, deviation_id: str) -> dict | None:
        key = f"deviation:{deviation_id}"
        value = self.client.get(key)
        return json.loads(value) if value else None
    