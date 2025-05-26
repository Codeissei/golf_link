from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, session, url_for, jsonify, current_app, abort,
    send_from_directory
)
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from app.models.db import db, Post, Comment, Attachment

# ブループリントの設定
bp = Blueprint('board', __name__, url_prefix='/board')

# アップロードされたファイルを保存するディレクトリを作成
def ensure_upload_dir():
    upload_dir = os.path.join(current_app.instance_path, 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir

# ファイルアップロード関数
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

# 掲示板トップページ
@bp.route('/')
def index():
    """掲示板トップページを表示"""
    return render_template('board/index.html')

# 投稿一覧取得API
@bp.route('/api/posts')
def get_posts():
    """投稿一覧を取得するAPI"""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify({
        'posts': [post.to_dict() for post in posts],
        'status': 'success'
    })

# 投稿詳細取得API
@bp.route('/api/posts/<int:post_id>')
def get_post(post_id):
    """特定の投稿を取得するAPI"""
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'post': post.to_dict(),
        'status': 'success'
    })

# 新規投稿API
@bp.route('/api/posts', methods=['POST'])
def create_post():
    """新規投稿を作成するAPI"""
    if not request.form.get('content') or not request.form.get('author'):
        return jsonify({
            'error': '内容と投稿者名は必須です',
            'status': 'error'
        }), 400
    
    # 投稿を作成
    post = Post(
        content=request.form.get('content'),
        author=request.form.get('author')
    )
    db.session.add(post)
    db.session.flush()  # IDを生成するためにflush
    
    # ファイルがある場合は保存
    files = request.files.getlist('files')
    for file in files:
        if file and file.filename:
            attachment = save_file(file)
            if attachment:
                attachment.post_id = post.id
                db.session.add(attachment)
    
    db.session.commit()
    
    # Socket.IOイベントを発火させる
    from app.socketio_events import emit_new_post
    emit_new_post(post.to_dict())
    
    return jsonify({
        'post': post.to_dict(),
        'status': 'success'
    }), 201

# 投稿へのコメント追加API
@bp.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """投稿にコメントを追加するAPI"""
    post = Post.query.get_or_404(post_id)
    
    if not request.form.get('content') or not request.form.get('author'):
        return jsonify({
            'error': '内容と投稿者名は必須です',
            'status': 'error'
        }), 400
    
    # コメントを作成
    comment = Comment(
        content=request.form.get('content'),
        author=request.form.get('author'),
        post_id=post.id
    )
    db.session.add(comment)
    db.session.flush()  # IDを生成するためにflush
    
    # ファイルがある場合は保存
    files = request.files.getlist('files')
    for file in files:
        if file and file.filename:
            attachment = save_file(file)
            if attachment:
                attachment.comment_id = comment.id
                db.session.add(attachment)
    
    db.session.commit()
    
    # Socket.IOイベントを発火させる
    from app.socketio_events import emit_new_comment
    emit_new_comment({'post_id': post.id, 'comment': comment.to_dict()})
    
    return jsonify({
        'comment': comment.to_dict(),
        'status': 'success'
    }), 201

# 投稿削除API (DELETE)
@bp.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    # デバッグ用にリクエスト情報を出力
    current_app.logger.info(f"投稿削除API呼び出し (DELETE): ID={post_id}")
    """投稿を削除するAPI"""
    post = Post.query.get_or_404(post_id)
    
    # 添付ファイルの物理ファイルを削除
    for attachment in post.attachments:
        try:
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
        except Exception as e:
            current_app.logger.error(f"ファイル削除エラー: {str(e)}")
    
    # コメントの添付ファイルも削除
    for comment in post.comments:
        for attachment in comment.attachments:
            try:
                if os.path.exists(attachment.file_path):
                    os.remove(attachment.file_path)
            except Exception as e:
                current_app.logger.error(f"ファイル削除エラー: {str(e)}")
    
    # 投稿を削除（カスケード削除によりコメントと添付ファイルも削除される）
    db.session.delete(post)
    db.session.commit()
    
    # Socket.IOイベントを発火させる
    from app.socketio_events import emit_delete_post
    emit_delete_post(post_id)
    
    return jsonify({
        'message': '投稿を削除しました',
        'status': 'success'
    })

# 投稿削除API (POST - 代替方法)
@bp.route('/api/posts/<int:post_id>/delete', methods=['POST'])
def delete_post_alt(post_id):
    # デバッグ用にリクエスト情報を出力
    current_app.logger.info(f"投稿削除API呼び出し (POST): ID={post_id}")
    
    post = Post.query.get_or_404(post_id)
    
    # 添付ファイルの物理ファイルを削除
    for attachment in post.attachments:
        try:
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
        except Exception as e:
            current_app.logger.error(f"ファイル削除エラー: {str(e)}")
    
    # コメントの添付ファイルも削除
    for comment in post.comments:
        for attachment in comment.attachments:
            try:
                if os.path.exists(attachment.file_path):
                    os.remove(attachment.file_path)
            except Exception as e:
                current_app.logger.error(f"ファイル削除エラー: {str(e)}")
    
    # 投稿を削除（カスケード削除によりコメントと添付ファイルも削除される）
    db.session.delete(post)
    db.session.commit()
    
    # Socket.IOイベントを発火させる
    from app.socketio_events import emit_delete_post
    emit_delete_post(post_id)
    
    return jsonify({
        'message': '投稿を削除しました',
        'status': 'success'
    })

# 添付ファイルダウンロードAPI
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
