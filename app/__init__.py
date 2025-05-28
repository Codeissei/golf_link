from flask import Flask
from flask_session import Session
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import jinja2
from app.models.db import init_db
from app.socketio_events import init_socketio

# Gunicorn用のアプリケーションオブジェクト
application = None

def create_app(test_config=None):
    global application
    """アプリケーションファクトリ関数"""
    app = Flask(__name__, instance_relative_config=True)
    
    # インスタンスフォルダの作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # 環境変数から設定を読み込み
    # 環境変数DATABASE_URLが設定されていればPostgresを使用、なければSQLiteを使用
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres:"):
        # RenderのPostgresQLURLは'postgres://'で始まるが、SQLAlchemyは'postgresql://'を期待する
        database_url = database_url.replace("postgres:", "postgresql:", 1)
    else:
        # デフォルトはSQLite
        database_url = f"sqlite:///{os.path.join(app.instance_path, 'golf_ai_strategist.sqlite')}"
    
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        PERPLEXITY_API_KEY=os.environ.get('PERPLEXITY_API_KEY', ''),
        SESSION_TYPE='filesystem',
        SESSION_PERMANENT=False,
        PERMANENT_SESSION_LIFETIME=1800,  # 30分
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 最大10MB
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
        # 本番環境用の設定
        PRODUCTION=os.environ.get('PRODUCTION', 'False').lower() == 'true',
        # PerplexityのAPIモデル
        PERPLEXITY_MODEL=os.environ.get('PERPLEXITY_MODEL', 'sonar-pro'),
        # Google Drive設定
        USE_GOOGLE_DRIVE=os.environ.get('USE_GOOGLE_DRIVE', 'False').lower() == 'true',
        GOOGLE_DRIVE_CREDENTIALS=os.environ.get('GOOGLE_DRIVE_CREDENTIALS', None),
        GOOGLE_DRIVE_FOLDER_ID=os.environ.get('GOOGLE_DRIVE_FOLDER_ID', None)
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
    from app.routes import main, board, messages
    app.register_blueprint(main.bp)
    app.register_blueprint(board.bp)
    app.register_blueprint(messages.bp)
    
    # データベースの初期化
    init_db(app)
    
    # SocketIOの初期化
    socketio = init_socketio(app)
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    # グローバル変数にアプリケーションを保存（get_wsgi_application関数で使用）
    application = app
    
    return app, socketio

def get_wsgi_application():
    """Gunicorn用のWSGIアプリケーションを返す関数"""
    # create_app()が既に呼ばれていて、applicationが設定されている場合はそれを返す
    if application is not None:
        return application
    
    # まだcreate_app()が呼ばれていない場合は呼び出して、Flaskアプリのみを返す
    app, _ = create_app()
    return app
