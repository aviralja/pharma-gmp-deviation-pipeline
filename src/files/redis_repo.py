import redis
import json
#! Redis repository for storing and retrieving deviation data
class DeviationRedisRepository:
    def __init__(self, host="localhost", port=6379, db=0, password=None):
        """
        Initialize Redis client for local or cloud Redis.
        
        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number (0-15)
            password: Password for Redis authentication (required for cloud Redis)
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

    def save_deviation(self, deviation_id: str, data: dict):
        key = f"deviation:{deviation_id}"
        self.client.set(key, json.dumps(data))

    def get_deviation(self, deviation_id: str) -> dict | None:
        key = f"deviation:{deviation_id}"
        value = self.client.get(key)
        return json.loads(value) if value else None
    