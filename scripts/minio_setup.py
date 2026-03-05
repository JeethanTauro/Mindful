import boto3
from botocore.exceptions import ClientError
import config

def create_raw_bucket():
    client = boto3.client(
        "s3",
        endpoint_url=config.MINIO_ENDPOINT,
        aws_access_key_id=config.MINIO_USER,
        aws_secret_access_key=config.MINIO_PASSWORD,
    )

    try:
        client.create_bucket(Bucket=config.MINIO_BUCKET_RAW)
        print(f"Bucket '{config.MINIO_BUCKET_RAW}' created successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
            print(f"Bucket '{config.MINIO_BUCKET_RAW}' already exists")
        else:
            raise

if __name__ == "__main__":
    create_raw_bucket()