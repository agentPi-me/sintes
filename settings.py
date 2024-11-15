import os
from typing import Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables")

CLIENT_SECRETS_FILE = os.getenv('CLIENT_SECRETS_FILE', 'client_secret.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://mamishka79.github.io/home-page-sintes/')

UserTimezones = Dict[int, str]
UserCredentials = Dict[int, Credentials]
AuthFlows = Dict[int, Flow]

user_timezones: UserTimezones = {}
user_credentials: UserCredentials = {}
auth_flows: AuthFlows = {}

def validate_config() -> None:
    """Validate all required configuration parameters."""
    if not os.path.exists(CLIENT_SECRETS_FILE):
        raise FileNotFoundError(f"Client secrets file not found: {CLIENT_SECRETS_FILE}")
    
    if not REDIRECT_URI:
        raise ValueError("REDIRECT_URI is not configured")

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def get_telegram_token(cls) -> str:
        return TELEGRAM_TOKEN
    
    @classmethod
    def get_client_secrets_file(cls) -> str:
        return CLIENT_SECRETS_FILE
    
    @classmethod
    def get_scopes(cls) -> list:
        return SCOPES
    
    @classmethod
    def get_redirect_uri(cls) -> str:
        return REDIRECT_URI

validate_config()