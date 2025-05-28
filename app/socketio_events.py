from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

# SocketIOの設定
socketio = SocketIO()

def init_socketio(app):
    """SocketIOを初期化"""
    # エラーハンドリングを強化
    socketio.init_app(
        app, 
        cors_allowed_origins="*",
        ping_timeout=60,  # タイムアウト時間を延長
        ping_interval=25,  # ping間隔を調整
        async_mode='eventlet',  # 明示的にeventletモードを指定
        logger=True,  # ロギングを有効化
        engineio_logger=True  # Engine.IOのロギングも有効化
    )
    return socketio

# SocketIO イベントハンドラ
@socketio.on('connect')
def handle_connect():
    """クライアント接続時の処理"""
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """クライアント切断時の処理"""
    logger.info('Client disconnected')

@socketio.on('error')
def handle_error(error):
    """エラー発生時の処理"""
    logger.error(f'SocketIO error: {error}')

@socketio.on_error()
def error_handler(e):
    """グローバルエラーハンドラ"""
    logger.error(f'SocketIO global error: {str(e)}')

@socketio.on('join')
def handle_join(data):
    """特定のルームに参加"""
    username = data.get('username')
    if username:
        join_room(username)
        logger.info(f'User {username} joined their room')

@socketio.on('leave')
def handle_leave(data):
    """特定のルームから退出"""
    username = data.get('username')
    if username:
        leave_room(username)
        logger.info(f'User {username} left their room')

# 掲示板関連のイベント送信関数
def emit_new_post(post_data):
    """新しい投稿があったことを通知"""
    try:
        socketio.emit('new_post', post_data)
        logger.info(f'Emitted new_post event: post_id={post_data.get("id")}')
    except Exception as e:
        logger.error(f'Error emitting new_post: {str(e)}')

def emit_new_comment(comment_data):
    """新しいコメントがあったことを通知"""
    try:
        socketio.emit('new_comment', comment_data)
        logger.info(f'Emitted new_comment event: post_id={comment_data.get("post_id")}')
    except Exception as e:
        logger.error(f'Error emitting new_comment: {str(e)}')

def emit_delete_post(post_id):
    """投稿が削除されたことを通知"""
    try:
        socketio.emit('delete_post', {'post_id': post_id})
        logger.info(f'Emitted delete_post event: post_id={post_id}')
    except Exception as e:
        logger.error(f'Error emitting delete_post: {str(e)}')

# メッセージ関連のイベント送信関数
def emit_new_message(message_data):
    """新しいメッセージがあったことを通知"""
    try:
        socketio.emit('new_message', message_data)
        # 受信者のルームにも通知
        socketio.emit('new_message', message_data, room=message_data['receiver'])
        logger.info(f'Emitted new_message event to {message_data.get("receiver")}')
    except Exception as e:
        logger.error(f'Error emitting new_message: {str(e)}')

def emit_read_messages(data):
    """メッセージが既読になったことを通知"""
    try:
        socketio.emit('read_messages', data)
        # 送信者のルームにも通知
        socketio.emit('read_messages', data, room=data['sender'])
        logger.info(f'Emitted read_messages event to {data.get("sender")}')
    except Exception as e:
        logger.error(f'Error emitting read_messages: {str(e)}')
