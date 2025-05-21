import os
from dotenv import load_dotenv

# .envファイルがあれば読み込む
load_dotenv()

# 基本設定
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
TESTING = os.environ.get('FLASK_TESTING', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')

# Perplexity API設定
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY', '')
PERPLEXITY_API_URL = os.environ.get('PERPLEXITY_API_URL', 'https://api.perplexity.ai')
PERPLEXITY_MODEL = os.environ.get('PERPLEXITY_MODEL', 'sonar-pro')
PERPLEXITY_MAX_TOKENS = int(os.environ.get('PERPLEXITY_MAX_TOKENS', '1024'))
PERPLEXITY_TEMPERATURE = float(os.environ.get('PERPLEXITY_TEMPERATURE', '0.7'))
PERPLEXITY_TIMEOUT = int(os.environ.get('PERPLEXITY_TIMEOUT', '25'))  # 25秒タイムアウト

# セッション設定
SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = os.environ.get('SESSION_FILE_DIR', './flask_session')
SESSION_PERMANENT = False
PERMANENT_SESSION_LIFETIME = 1800  # 30分

# セキュリティ設定
CSRF_ENABLED = True
WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', SECRET_KEY)

# コンテンツセキュリティポリシー
CSP = "default-src 'self' https://api.perplexity.ai; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"

# 入力制限
MAX_CONTENT_LENGTH = 2 * 1024  # 最大2KB
