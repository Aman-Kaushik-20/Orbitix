# GCP CREDENTIALS
import os
from dotenv import load_dotenv

# Load environment variables from a .env file.
# This will search for a .env file and load it.
load_dotenv('backend/.env')

BUCKET_NAME = os.environ["BUCKET_NAME"]

STAGING_API = f"https://storage.googleapis.com/{BUCKET_NAME}/"

CDN_API = os.environ["CDN_API"]


private_key_from_env = os.environ["GCP_PRIVATE_KEY"]
formatted_private_key = private_key_from_env.replace("\\n", "\n")

GCP_CREDENTIALS = {
    "type": os.environ["GCP_TYPE"],
    "project_id": os.environ["GCP_PROJECT_ID"],
    "private_key_id": os.environ["GCP_PRIVATE_KEY_ID"],
    "private_key": formatted_private_key,  # Use the corrected key
    "client_email": os.environ["GCP_CLIENT_EMAIL"],
    "client_id": os.environ["GCP_CLIENT_ID"],
    "auth_uri": os.environ["GCP_AUTH_URI"],
    "token_uri": os.environ["GCP_TOKEN_URI"],
    "auth_provider_x509_cert_url": os.environ["GCP_AUTH_PROVIDER_X509_CERT_URL"],
    "client_x509_cert_url": os.environ["GCP_CLIENT_X509_CERT_URL"],
    "universe_domain": os.environ["GCP_UNIVERSE_DOMAIN"],
}
