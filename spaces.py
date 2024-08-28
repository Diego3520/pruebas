import os
import boto3
from botocore.client import Config

# Configura tus credenciales
access_key = os.getenv('DO_SPACES_ACCESS_KEY')
secret_key = os.getenv('DO_SPACES_SECRET_KEY')
space_name = os.getenv('DO_SPACES_NAME')
endpoint_url = os.getenv('DO_SPACES_ENDPOINT_URL')

# Crea una sesión usando tus credenciales
session = boto3.session.Session()
client = session.client('s3',
                        region_name='nyc3',
                        endpoint_url=endpoint_url,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        config=Config(signature_version='s3v4'))