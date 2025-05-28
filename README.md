# Golf AI Strategist - チーム連絡ツール

このアプリケーションは、Golf AI Strategist の拡張機能として、チーム内のコミュニケーションを円滑にするための連絡ツール機能を提供します。

## 機能概要

### 1. AI戦略アドバイス（既存）
- ゴルフホール条件を入力し、AI から攻略プランを受け取る
- Perplexity API を使用した高度な戦略アドバイス

### 2. 連絡板（新機能）
- チームメンバー全員が見られる掲示板
- 投稿とコメント機能
- ファイル添付機能
- リアルタイム通知

### 3. メッセージ機能（新機能）
- メンバー間の1対1メッセージング
- メッセージ履歴管理
- 既読/未読表示
- ファイル添付機能
- リアルタイム通知

## 技術仕様

### 使用技術
- **フレームワーク**: Flask 3.x (Blueprint パターン)
- **データベース**: SQLite (Flask-SQLAlchemy)
- **セッション管理**: Flask-Session
- **リアルタイム通信**: Flask-SocketIO
- **フロントエンド**: HTML, CSS, JavaScript (Vanilla JS)

### データ永続化（データベース）
このアプリケーションは SQLite データベースを使用して、以下の情報を永続的に保存します：

1. **連絡板（Board）**
   - 投稿（Posts）: 投稿者名、内容、作成日時
   - コメント（Comments）: 投稿者名、内容、作成日時、所属投稿ID
   - 添付ファイル（Attachments）: ファイル名、保存パス、MIMEタイプ、所属オブジェクト情報

2. **メッセージ（Messages）**
   - メッセージ: 送信者名、受信者名、内容、作成日時、既読状態
   - 添付ファイル: ファイル名、保存パス、MIMEタイプ、所属メッセージID

### データベースモデル
```
Post
- id: Integer (主キー)
- author: String (投稿者名)
- content: Text (投稿内容)
- created_at: DateTime (作成日時)
- comments: Relationship (Comment - 1対多)
- attachments: Relationship (Attachment - 1対多)

Comment
- id: Integer (主キー) 
- post_id: Integer (外部キー - Post)
- author: String (投稿者名)
- content: Text (コメント内容)
- created_at: DateTime (作成日時)
- attachments: Relationship (Attachment - 1対多)

Message
- id: Integer (主キー)
- sender: String (送信者名)
- receiver: String (受信者名)
- content: Text (メッセージ内容)
- created_at: DateTime (作成日時)
- is_read: Boolean (既読状態)
- attachments: Relationship (Attachment - 1対多)

Attachment
- id: Integer (主キー)
- filename: String (ファイル名)
- path: String (保存パス)
- mime_type: String (MIMEタイプ)
- object_type: String (所属オブジェクトタイプ)
- object_id: Integer (所属オブジェクトID)
```

## ユーザー認証
このアプリケーションでは、シンプルな名前ベースの識別を使用しています：
- ブラウザのローカルストレージに名前を保存
- サーバーサイドではセッション管理による状態維持

## インストールと実行方法

### 必要条件
- Python 3.10.16 以上
- pip (Pythonパッケージマネージャー)

### ローカルでのセットアップ手順
1. リポジトリをクローン
```
git clone <リポジトリURL>
cd golf-ai-strategist
```

2. 仮想環境を作成して有効化
```
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

3. 必要なパッケージをインストール
```
pip install -r requirements.txt
```

4. 環境変数を設定
```
# .env ファイルを作成
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=<ランダムな文字列>
PERPLEXITY_API_KEY=<Perplexity APIキー>
```

5. データベースを初期化
```
flask db init
flask db migrate
flask db upgrade
```

6. アプリケーションを実行
```
python run.py
```

7. ブラウザで以下のURLにアクセス
```
http://localhost:5000/
```

## デプロイ方法

このアプリケーションはRenderクラウドプラットフォームへのデプロイに対応しています。テスト環境と本番環境の両方の設定が含まれています。

### Renderへのデプロイ手順

1. [Render](https://render.com/) でアカウントを作成（まだ持っていない場合）

2. Renderダッシュボードから "New +" ボタンをクリックし、"Blueprint" を選択

3. リポジトリURLを入力し連携

4. デプロイが開始され、自動的に `render.yaml` ファイルに基づいてセットアップされます

5. デプロイ完了後、表示されるURLからアプリケーションにアクセスできます

### 環境変数の設定

Renderダッシュボードから以下の環境変数を設定：

- `PERPLEXITY_API_KEY`: Perplexity APIのアクセスキー
- `SECRET_KEY`: セキュリティ用の秘密キー（Renderが自動生成）
- `PRODUCTION`: 本番環境モード（"true"で有効）
- `PERPLEXITY_MODEL`: 使用するPerplexityのモデル（デフォルト: "sonar-pro"）

### テスト環境と本番環境の違い

#### テスト環境
- **データベース**: SQLiteを使用（データは永続化されません）
- **UI**: 画面上部に警告バナーが表示されます
- **設定方法**: 環境変数`PRODUCTION`を設定しない、または"false"に設定

#### 本番環境
- **データベース**: PostgreSQLを使用（データは永続化されます）
- **UI**: 警告バナーは表示されません
- **設定方法**: 環境変数`PRODUCTION`を"true"に設定

### 本番環境の準備

本番環境では以下の機能が利用可能です：

1. **PostgreSQLデータベース**
   - `render.yaml`に含まれるPostgreSQLサービスが自動的に作成されます
   - データは再起動・デプロイ間でも保持されます

2. **永続的なデータストレージ**
   - 投稿、コメント、メッセージ履歴などが永続化されます
   - ユーザー情報も保持されます

### 注意事項

- **ファイル添付**: Renderの無料プランでは、アップロードされたファイルはデプロイ間で保持されません。本番環境でファイル添付機能を完全に対応させるには、クラウドストレージ（AWS S3など）の使用を検討してください。
- **スリープモード**: Renderの無料プランでは、15分間アクセスがないとアプリケーションはスリープ状態になります。初回アクセス時は起動に時間がかかる場合があります。

## 使用方法

### AI戦略アドバイス
1. ホーム画面からゴルフホール条件を入力
2. 「送信」ボタンをクリック
3. AIが生成した攻略プランを確認

### 連絡板
1. ナビゲーションメニューから「連絡板」をクリック
2. 初回利用時は名前を入力
3. 投稿フォームから内容を入力し、必要に応じてファイルを添付
4. 「投稿する」ボタンをクリック
5. 他のメンバーの投稿にコメントを追加可能

### メッセージ
1. ナビゲーションメニューから「メッセージ」をクリック
2. 初回利用時は名前を入力
3. 「新規メッセージ」から送信先の名前を入力
4. メッセージを入力し、必要に応じてファイルを添付
5. 「送信」ボタンをクリック
