"""
Google Drive APIを使用してファイルの保存と取得を行うサービス
"""
import os
import io
import logging
from flask import current_app
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

class GoogleDriveService:
    """Google DriveとAPIを通じて連携するサービスクラス"""
    
    def __init__(self):
        """初期化"""
        self.service = None
        self.creds = None
        self.folder_id = None
        self._connect()
    
    def _connect(self):
        """Google Drive APIへの接続を初期化"""
        try:
            # 認証情報を環境変数から取得
            credentials_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
            
            if not credentials_json:
                current_app.logger.warning('Google Drive認証情報が設定されていません')
                return False
            
            # JSON文字列から認証情報を作成
            self.creds = service_account.Credentials.from_service_account_info(
                eval(credentials_json),
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            # DriveAPIクライアントの構築
            self.service = build('drive', 'v3', credentials=self.creds)
            
            # ルートフォルダIDを取得（環境変数から、または新規作成）
            self.folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
            if not self.folder_id:
                self.folder_id = self._create_root_folder()
            
            current_app.logger.info('Google Drive APIに接続しました')
            return True
            
        except Exception as e:
            current_app.logger.error(f"Google Drive APIの初期化に失敗: {str(e)}")
            return False
    
    def _create_root_folder(self):
        """アプリケーション用のルートフォルダを作成"""
        folder_metadata = {
            'name': 'Golf_AI_Strategist_Files',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder.get('id')
        current_app.logger.info(f'Google Driveにルートフォルダを作成: {folder_id}')
        
        return folder_id
    
    def create_subfolder(self, folder_name):
        """サブフォルダを作成"""
        if not self.service or not self.folder_id:
            return None
        
        # サブフォルダがすでに存在するか確認
        existing_folder = self.service.files().list(
            q=f"name='{folder_name}' and '{self.folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        if existing_folder.get('files'):
            # 既存のフォルダを返す
            return existing_folder.get('files')[0].get('id')
        
        # 新しいサブフォルダを作成
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.folder_id]
        }
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
    
    def upload_file(self, file_path, file_name=None, subfolder=None):
        """ファイルをアップロード
        
        Args:
            file_path (str): アップロードするファイルのパス
            file_name (str, optional): 保存時のファイル名（指定がなければ元のファイル名）
            subfolder (str, optional): サブフォルダ名（指定がなければルートフォルダに保存）
            
        Returns:
            dict: ファイルID、公開URL、その他のメタデータ
        """
        if not self.service or not self.folder_id:
            return None
        
        # ファイルが存在するか確認
        if not os.path.exists(file_path):
            current_app.logger.error(f"ファイルが存在しません: {file_path}")
            return None
        
        # ファイル名が指定されていない場合は元のファイル名を使用
        if not file_name:
            file_name = os.path.basename(file_path)
        
        # 保存先のフォルダIDを決定
        parent_id = self.folder_id
        if subfolder:
            subfolder_id = self.create_subfolder(subfolder)
            if subfolder_id:
                parent_id = subfolder_id
        
        # ファイルのメタデータ
        file_metadata = {
            'name': file_name,
            'parents': [parent_id]
        }
        
        # アップロード実行
        try:
            media = MediaFileUpload(file_path)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType,webViewLink'
            ).execute()
            
            # ファイルへのアクセス権を設定（任意、必要に応じて）
            # ここでは例として閲覧権限を設定
            self.service.permissions().create(
                fileId=file.get('id'),
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            return file
            
        except Exception as e:
            current_app.logger.error(f"ファイルのアップロードに失敗: {str(e)}")
            return None
    
    def download_file(self, file_id):
        """ファイルをダウンロード
        
        Args:
            file_id (str): ダウンロードするファイルのID
            
        Returns:
            bytes: ファイルの内容
        """
        if not self.service:
            return None
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            file_content.seek(0)
            return file_content.read()
            
        except Exception as e:
            current_app.logger.error(f"ファイルのダウンロードに失敗: {str(e)}")
            return None
    
    def get_file_metadata(self, file_id):
        """ファイルのメタデータを取得
        
        Args:
            file_id (str): ファイルのID
            
        Returns:
            dict: ファイルのメタデータ
        """
        if not self.service:
            return None
        
        try:
            return self.service.files().get(
                fileId=file_id, 
                fields='id,name,mimeType,webViewLink'
            ).execute()
            
        except Exception as e:
            current_app.logger.error(f"ファイルメタデータの取得に失敗: {str(e)}")
            return None
    
    def delete_file(self, file_id):
        """ファイルを削除
        
        Args:
            file_id (str): 削除するファイルのID
            
        Returns:
            bool: 削除に成功したかどうか
        """
        if not self.service:
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
            
        except Exception as e:
            current_app.logger.error(f"ファイルの削除に失敗: {str(e)}")
            return False


# シングルトンパターンでサービスインスタンスを提供する関数
_drive_service = None

def get_drive_service():
    """Google Driveサービスのシングルトンインスタンスを取得"""
    global _drive_service
    
    # 環境変数でGoogle Drive統合が有効になっているか確認
    use_google_drive = os.environ.get('USE_GOOGLE_DRIVE', 'false').lower() == 'true'
    if not use_google_drive:
        return None
    
    # インスタンスがまだ作成されていなければ作成
    if _drive_service is None:
        _drive_service = GoogleDriveService()
    
    return _drive_service
