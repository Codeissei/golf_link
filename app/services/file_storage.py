"""
ファイルストレージの管理を行うモジュール
環境設定に応じてローカルまたはGoogle Driveにファイルを保存
"""
import os
import uuid
import tempfile
from werkzeug.utils import secure_filename
from flask import current_app
from app.models.db import Attachment, db
from app.services.google_drive import get_drive_service
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

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
    
    try:
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
        
        logger.info(f"ファイル保存開始: {original_filename}, サイズ: {file_size}, タイプ: {file_type}")
        
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
                logger.error("Google Driveサービスが利用できません")
                return None
            
            # 一時ファイルとして保存
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                uploaded_file.save(temp_path)
            
            try:
                # Google Driveにアップロード
                logger.info(f"Google Driveにアップロード開始: {original_filename}")
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
                    logger.info(f"Google Driveへのアップロード成功: {file_metadata.get('id')}")
                    
                    # 一時ファイルを削除
                    try:
                        os.remove(temp_path)
                    except Exception as e:
                        logger.warning(f"一時ファイル削除エラー: {str(e)}")
                else:
                    # Google Driveへのアップロードに失敗した場合、ローカルに保存
                    logger.warning("Google Driveへのアップロード失敗、ローカルに保存します")
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, unique_filename)
                    
                    # 一時ファイルを移動
                    os.rename(temp_path, file_path)
                    
                    attachment.storage_type = 'local'
                    attachment.file_path = file_path
            except Exception as e:
                logger.error(f"Google Driveへのアップロード失敗: {str(e)}")
                # エラー時もローカルに保持
                try:
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, unique_filename)
                    
                    # 一時ファイルを移動
                    os.rename(temp_path, file_path)
                    
                    attachment.storage_type = 'local'
                    attachment.file_path = file_path
                except Exception as move_error:
                    logger.error(f"ローカルへの保存も失敗: {str(move_error)}")
                    return None
        else:
            # ローカルストレージに保存
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            
            try:
                uploaded_file.save(file_path)
                logger.info(f"ローカルストレージに保存: {file_path}")
                
                attachment.storage_type = 'local'
                attachment.file_path = file_path
            except Exception as e:
                logger.error(f"ローカルストレージへの保存失敗: {str(e)}")
                return None
        
        return attachment
    except Exception as e:
        logger.error(f"ファイル保存中の予期せぬエラー: {str(e)}")
        return None

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
                result = drive_service.delete_file(attachment.drive_file_id)
                logger.info(f"Google Driveからファイル削除: ID={attachment.drive_file_id}, 結果={result}")
                return result
        elif attachment.storage_type == 'local' and attachment.file_path:
            # ローカルファイルを削除
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
                logger.info(f"ローカルファイル削除: {attachment.file_path}")
                return True
        
        return False
    except Exception as e:
        logger.error(f"ファイル削除エラー: {str(e)}")
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
