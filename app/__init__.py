from flask import Flask
from flask_session import Session
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import jinja2

def create_app(test_config=None):
    """アプリケーションファクトリ関数"""
    app = Flask(__name__, instance_relative_config=True)
    
    # 環境変数から設定を読み込み
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        PERPLEXITY_API_KEY=os.environ.get('PERPLEXITY_API_KEY', ''),
        SESSION_TYPE='filesystem',
        SESSION_PERMANENT=False,
        PERMANENT_SESSION_LIFETIME=1800,  # 30分
        MAX_CONTENT_LENGTH=2 * 1024,  # 最大2KB
    )
    
    # 設定ファイルの読み込み
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    
    # セッションの初期化
    Session(app)
    
    # カスタムフィルターの追加
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        """改行を<br>タグに変換するフィルター"""
        if s is None:
            return ""
        return jinja2.utils.markupsafe.Markup(s.replace('\n', '<br>'))
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(s):
        """ISO8601形式の日時を日本語形式に変換するフィルター"""
        if s is None:
            return ""
        try:
            dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
            return dt.strftime('%Y/%m/%d %H:%M')
        except:
            return ""
    
    # ロギングの設定
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/golf_ai_strategist.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Golf AI Strategist startup')
    
    # ルートの登録
    from app.routes import main
    app.register_blueprint(main.bp)
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    return app
