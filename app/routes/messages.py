from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, session, url_for, jsonify, current_app, abort,
    send_from_directory
)
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from app.models.db import db, Message, Attachment

bp = Blueprint('messages', __name__, url_prefix='/messages')

# アップロードされたファイルを保存するディレクトリを作成（board.pyと共通化すべき関数）
def ensure_upload_dir():
    upload_dir = os.path.join(current_app.instance_path, 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir

# ファイルアップロード関数（board.pyと共通化すべき関数）
def save_file(file):
    if file:
        upload_dir = ensure_upload_dir()
        filename = secure_filename(file.filename)
        # ユニークなファイル名を生成
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Attachmentモデルに保存
        attachment = Attachment(
            filename=filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size=os.path.getsize(file_path)
        )
        return attachment
    return None

# メッセージページ
@bp.route('/')
def index():
    """メッセージホームページを表示"""
    return render_template('messages/index.html')

# 特定ユーザーとのメッセージページ
@bp.route('/<string:user>')
def chat(user):
    """特定ユーザーとのチャットページを表示"""
    return render_template('messages/chat.html', receiver=user)

# ユーザーとのメッセージ履歴取得API
@bp.route('/api/conversations/<string:user>')
def get_conversation(user):
    """特定ユーザーとのメッセージ履歴を取得するAPI"""
    # セッションから自分の名前を取得（認証機能がないため、仮の実装）
    sender = session.get('username', request.args.get('sender', ''))
    
    if not sender:
        return jsonify({
            'error': '送信者名を指定してください',
            'status': 'error'
        }), 400
    
    # 自分から相手へのメッセージを取得
    sent_messages = Message.query.filter_by(
        sender=sender,
        receiver=user
    ).all()
    
    # 相手から自分へのメッセージを取得
    received_messages = Message.query.filter_by(
        sender=user,
        receiver=sender
    ).all()
    
    # メッセージを時間順にソート
    all_messages = sorted(
        sent_messages + received_messages,
        key=lambda x: x.created_at
    )
    
    # 未読メッセージを既読に更新
    for msg in received_messages:
        if not msg.is_read:
            msg.is_read = True
    
    db.session.commit()
    
    return jsonify({
        'messages': [msg.to_dict() for msg in all_messages],
        'status': 'success'
    })

# 会話相手一覧取得API
@bp.route('/api/contacts')
def get_contacts():
    """メッセージのやり取りがある相手一覧を取得するAPI"""
    # セッションから自分の名前を取得（認証機能がないため、仮の実装）
    sender = session.get('username', request.args.get('sender', ''))
    
    if not sender:
        return jsonify({
            'error': '送信者名を指定してください',
            'status': 'error'
        }), 400
    
    # 自分が送信したメッセージの相手を取得
    sent_to = db.session.query(Message.receiver.distinct()).filter_by(sender=sender).all()
    sent_to = [user[0] for user in sent_to]
    
    # 自分が受信したメッセージの送信者を取得
    received_from = db.session.query(Message.sender.distinct()).filter_by(receiver=sender).all()
    received_from = [user[0] for user in received_from]
    
    # 重複を排除して一覧を作成
    contacts = sorted(list(set(sent_to + received_from)))
    
    # 各連絡先の最新メッセージと未読件数を取得
    contact_details = []
    for contact in contacts:
        # 最新メッセージを取得
        latest_message = Message.query.filter(
            ((Message.sender == sender) & (Message.receiver == contact)) |
            ((Message.sender == contact) & (Message.receiver == sender))
        ).order_by(Message.created_at.desc()).first()
        
        # 未読件数を取得
        unread_count = Message.query.filter_by(
            sender=contact,
            receiver=sender,
            is_read=False
        ).count()
        
        contact_details.append({
            'username': contact,
            'latest_message': latest_message.to_dict() if latest_message else None,
            'unread_count': unread_count
        })
    
    # 最新メッセージの日時でソート
    contact_details = sorted(
        contact_details,
        key=lambda x: x['latest_message']['created_at'] if x['latest_message'] else '1970-01-01',
        reverse=True
    )
    
    return jsonify({
        'contacts': contact_details,
        'status': 'success'
    })

# メッセージ送信API
@bp.route('/api/messages', methods=['POST'])
def send_message():
    """メッセージを送信するAPI"""
    if not request.form.get('content') or not request.form.get('sender') or not request.form.get('receiver'):
        return jsonify({
            'error': '内容、送信者、受信者は必須です',
            'status': 'error'
        }), 400
    
    # メッセージを作成
    message = Message(
        content=request.form.get('content'),
        sender=request.form.get('sender'),
        receiver=request.form.get('receiver')
    )
    db.session.add(message)
    db.session.flush()  # IDを生成するためにflush
    
    # ファイルがある場合は保存
    files = request.files.getlist('files')
    for file in files:
        if file and file.filename:
            attachment = save_file(file)
            if attachment:
                attachment.message_id = message.id
                db.session.add(attachment)
    
    db.session.commit()
    
    # Socket.IOイベントを発火させる（後で実装）
    # socketio.emit('new_message', message.to_dict())
    # socketio.emit(f'new_message_{message.receiver}', message.to_dict())
    
    return jsonify({
        'message': message.to_dict(),
        'status': 'success'
    }), 201

# メッセージ既読化API
@bp.route('/api/messages/read/<string:user>', methods=['POST'])
def mark_as_read(user):
    """特定ユーザーからのメッセージを既読にするAPI"""
    # セッションから自分の名前を取得（認証機能がないため、仮の実装）
    receiver = session.get('username', request.form.get('receiver', ''))
    
    if not receiver:
        return jsonify({
            'error': '受信者名を指定してください',
            'status': 'error'
        }), 400
    
    # 未読メッセージを既読に更新
    unread_messages = Message.query.filter_by(
        sender=user,
        receiver=receiver,
        is_read=False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    return jsonify({
        'message': f'{len(unread_messages)}件のメッセージを既読にしました',
        'status': 'success'
    })

# 添付ファイルダウンロードAPI（board.pyと重複するため、共通化を検討）
@bp.route('/api/attachments/<int:attachment_id>')
def download_attachment(attachment_id):
    """添付ファイルをダウンロードするAPI"""
    attachment = Attachment.query.get_or_404(attachment_id)
    
    if not os.path.exists(attachment.file_path):
        return jsonify({
            'error': 'ファイルが見つかりません',
            'status': 'error'
        }), 404
    
    # ファイルを送信
    return send_from_directory(
        os.path.dirname(attachment.file_path),
        os.path.basename(attachment.file_path),
        as_attachment=True,
        download_name=attachment.filename
    )
