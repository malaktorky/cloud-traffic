import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import BotoCoreError, ClientError

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


class CloudStorage:
    def __init__(self):
        self.bucket_name = S3_BUCKET_NAME
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )

    def upload_file(self, local_path: str, s3_key: str) -> str | None:
        """
        Upload a local file to S3 and return its S3 URI.
        """
        try:
            self.s3.upload_file(local_path, self.bucket_name, s3_key)
            return f"s3://{self.bucket_name}/{s3_key}"
        except (BotoCoreError, ClientError, FileNotFoundError) as e:
            print(f"[S3 Upload Error] {e}")
            return None

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3 to local path.
        """
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3.download_file(self.bucket_name, s3_key, local_path)
            return True
        except (BotoCoreError, ClientError) as e:
            print(f"[S3 Download Error] {e}")
            return False