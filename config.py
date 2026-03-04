
#basically this is the file that is used to load all the environment variables into CONSTANTS that can be reused
import os
from dotenv import load_dotenv

load_dotenv()

# MinIO
#os.getenv(get_from_the_env_file , if_not_in_env_default)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET_RAW = os.getenv("MINIO_BUCKET_RAW", "raw")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_STREAM_NAME = os.getenv("REDIS_STREAM_NAME", "mindful:raw:new")

