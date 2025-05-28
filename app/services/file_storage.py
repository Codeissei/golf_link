"""
ファイルストレージの管理を行うモジュール
環境設定に応じてローカルまたはGoogle Driveにファイルを保存
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from app.models.db import Attachment, db
from app.services.google_drive import get_drive_service

def save_file(uploaded_file, subfolder='uploads'):
    """
    アップロードされたファイルを保存し、Attachmentモデルを作成
    
    Args:
        uploaded_file: FileStorage - アップロードされたファイルオブジェクト
        subfolder: str - 保存先サブフォルダ
        
    Returns:
        Attachment: 保存されたファイルのAttachmentモデル（まだDB未保存）
    """
    if not uploaded_file:
        return None
    
    # ファイル名の安全化と一意性の確保
    original_filename = secure_filename(uploaded_file.filename)
    file_ext = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    
    # ファイルサイズとタイプの取得
    file_size = 0
    uploaded_file.seek(0, os.SEEK_END)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)  # ファイルポインタを先頭に戻す
    file_type = uploaded_file.content_type
    
    # 保存先の決定（Google DriveかLocal Storage）
    use_google_drive = current_app.config.get('USE_GOOGLE_DRIVE', False)
    
    # 新しいAttachmentモデルの作成
    attachment = Attachment(
        filename=original_filename,
        file_type=file_type,
        file_size=file_size
    )
    
    if use_google_drive:
        # Google Driveへのアップロード
        drive_service = get_drive_service()
        if not drive_service:
            return None
        
        # 一時ファイルとして保存
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        uploaded_file.save(temp_path)
        
        try:
            # Google Driveにアップロード
            file_metadata = drive_service.upload_file(
                file_path=temp_path,
                file_name=original_filename,
                subfolder=subfolder
            )
            
            if file_metadata:
                # アップロード成功
                attachment.storage_type = 'google_drive'
                attachment.drive_file_id = file_metadata.get('id')
                attachment.drive_view_url = file_metadata.get('webViewLink')
                
                # 一時ファイルを削除
                os.remove(temp_path)
            else:
                # Google Driveへのアップロードに失敗した場合、ローカルに保存
                attachment.storage_type = 'local'
                attachment.file_path = temp_path
        except Exception as e:
            current_app.logger.error(f"Google Driveへのアップロード失敗: {str(e)}")
            # エラー時もローカルに保持
            attachment.storage_type = 'local'
            attachment.file_path = temp_path
    else:
        # ローカルストレージに保存
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        
        uploaded_file.save(file_path)
        
        attachment.storage_type = 'local'
        attachment.file_path = file_path
    
    return attachment

def delete_file(attachment):
    """
    ファイルを削除
    
    Args:
        attachment: Attachment - 削除するファイルのAttachmentモデル
        
    Returns:
        bool: 削除に成功したかどうか
    """
    if not attachment:
        return False
    
    try:
        if attachment.storage_type == 'google_drive' and attachment.drive_file_id:
            # Google Driveからファイルを削除
            drive_service = get_drive_service()
            if drive_service:
                return drive_service.delete_file(attachment.drive_file_id)
        elif attachment.storage_type == 'local' and attachment.file_path:
            # ローカルファイルを削除
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
                return True
        
        return False
    except Exception as e:
        current_app.logger.error(f"ファイル削除エラー: {str(e)}")
        return False

def get_attachment_url(attachment):
    """
    添付ファイルのアクセスURLを取得
    
    Args:
        attachment: Attachment - ファイルのAttachmentモデル
        
    Returns:
        str: ファイルへのアクセスURL
    """
    if not attachment:
        return None
    
    return attachment.access_url
