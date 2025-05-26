from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Post(db.Model):
    """掲示板投稿モデル"""
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='post', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'comments': [comment.to_dict() for comment in self.comments],
            'attachments': [attachment.to_dict() for attachment in self.attachments],
        }


class Comment(db.Model):
    """投稿へのコメントモデル"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    
    attachments = db.relationship('Attachment', backref='comment', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'post_id': self.post_id,
            'attachments': [attachment.to_dict() for attachment in self.attachments],
        }


class Message(db.Model):
    """DMメッセージモデル"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)
    
    attachments = db.relationship('Attachment', backref='message', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'sender': self.sender,
            'receiver': self.receiver,
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read,
            'attachments': [attachment.to_dict() for attachment in self.attachments],
        }


class Attachment(db.Model):
    """ファイル添付モデル"""
    __tablename__ = 'attachments'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)  # バイト単位
    uploaded_at = db.Column(db.DateTime, default=datetime.now)
    
    # 関連付け（どれか1つだけnullableではない）
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat(),
        }


# データベース初期化関数
def init_db(app):
    """アプリケーションコンテキストでデータベースを初期化"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
