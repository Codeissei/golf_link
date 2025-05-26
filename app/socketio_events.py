from flask_socketio import SocketIO, emit, join_room, leave_room

socketio = SocketIO()

def init_socketio(app):
    """SocketIOを初期化"""
    socketio.init_app(app, cors_allowed_origins="*")
    return socketio

# SocketIO イベントハンドラ
@socketio.on('connect')
def handle_connect():
    """クライアント接続時の処理"""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """クライアント切断時の処理"""
    print('Client disconnected')

@socketio.on('join')
def handle_join(data):
    """特定のルームに参加"""
    username = data.get('username')
    if username:
        join_room(username)
        print(f'User {username} joined their room')

@socketio.on('leave')
def handle_leave(data):
    """特定のルームから退出"""
    username = data.get('username')
    if username:
        leave_room(username)
        print(f'User {username} left their room')

# 掲示板関連のイベント送信関数
def emit_new_post(post_data):
    """新しい投稿があったことを通知"""
    socketio.emit('new_post', post_data)

def emit_new_comment(comment_data):
    """新しいコメントがあったことを通知"""
    socketio.emit('new_comment', comment_data)

def emit_delete_post(post_id):
    """投稿が削除されたことを通知"""
    socketio.emit('delete_post', {'post_id': post_id})

# メッセージ関連のイベント送信関数
def emit_new_message(message_data):
    """新しいメッセージがあったことを通知"""
    socketio.emit('new_message', message_data)
    # 受信者のルームにも通知
    socketio.emit('new_message', message_data, room=message_data['receiver'])

def emit_read_messages(data):
    """メッセージが既読になったことを通知"""
    socketio.emit('read_messages', data)
    # 送信者のルームにも通知
    socketio.emit('read_messages', data, room=data['sender'])
