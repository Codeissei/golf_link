# Golf AI Strategist - 本番環境デプロイ手順書

このガイドでは、Golf AI Strategistアプリケーションを本番環境向けにRenderにデプロイする手順を説明します。このガイドではPostgreSQLデータベースとGoogle Driveストレージを使用して、データとファイルを永続化する設定を含んでいます。

## 事前準備

### 1. 必要なもの
- GitHubアカウント
- Renderアカウント
- Perplexity API Key

### 2. 確認済みファイル
以下のファイルが既にプロジェクトに含まれていることを確認しました：
- `requirements.txt` - 依存パッケージ一覧
- `Procfile` - アプリケーション起動コマンド
- `render.yaml` - Renderサービス定義
- `.gitignore` - 不要ファイルの除外設定

## デプロイ手順

### 1. GitHubリポジトリの作成

1. GitHubにログインし、新しいリポジトリを作成
   - リポジトリ名: `golf-ai-strategist`（任意）
   - 公開／非公開設定: どちらでも可能
   - READMEの追加: チェックなし

2. ローカルリポジトリの初期化とプッシュ
   ```bash
   # リポジトリの初期化
   git init
   
   # 全てのファイルをステージング
   git add .
   
   # コミット
   git commit -m "Initial commit"
   
   # リモートリポジトリの追加（URLは実際のリポジトリURLに置き換え）
   git remote add origin https://github.com/yourusername/golf-ai-strategist.git
   
   # プッシュ
   git push -u origin main
   ```

### 2. Renderでのデプロイ

1. [Render](https://render.com/)にアクセスしてアカウントを作成またはログイン

2. ダッシュボードの「New +」ボタンをクリック

3. **Blueprint**を選択
   - GitHubアカウントと連携（初回のみ）
   - リポジトリを検索して選択

4. サービス設定の確認
   - `render.yaml`の内容に基づいて自動設定されます
   - サービス名: `golf-ai-strategist`
   - 環境: `Python`
   - リージョン: お好みで選択（東京があれば最適）

5. **「Apply」**ボタンをクリックしてデプロイを開始

### 3. 環境変数の設定

1. デプロイが始まったら、サービスのダッシュボードに移動

2. **Environment**タブを選択

3. 以下の環境変数が設定されていることを確認（`render.yaml`で自動設定）
   - `FLASK_APP`: run.py
   - `SECRET_KEY`: 自動生成

4. Perplexity API Keyを追加
   - **「Add Environment Variable」**をクリック
   - Key: `PERPLEXITY_API_KEY`
   - Value: あなたのPerplexity APIキーを入力

5. **「Save Changes」**をクリックして保存

### 4. デプロイの確認

1. **「Logs」**タブでデプロイログを確認
   - ビルドとスタートアップのログを確認
   - エラーがあれば対処

2. デプロイが完了したら、表示されるURLをクリックしてアプリケーションにアクセス
   - 例: `https://golf-ai-strategist.onrender.com`

## 注意事項とデータの制限

### SQLiteデータベースの一時性

Renderの無料プランでは、ファイルシステムは永続的ではありません：

- アプリケーションが再起動するたびに、SQLiteデータベースが初期化されます
- 以下のタイミングで再起動が発生します：
  - コードの更新によるデプロイ時
  - 15分間アクセスがなかった場合（自動スリープから復帰時）
  - Renderのメンテナンス時

### データとファイルの永続化設定

このアプリケーションは、以下の2種類のデータを永続化するように設計されています：

#### 1. データベース永続化 - PostgreSQL

- `render.yaml`で自動的にPostgreSQLサービスが作成される
- データベースURL環境変数（`DATABASE_URL`）が自動的に設定される
- アプリケーションはこのURLを検出してPostgreSQLを使用する

#### 2. ファイル永続化 - Google Drive

ファイル添付機能を使用するには、Google Drive APIの設定が必要です：

1. **Google Cloud Platformでプロジェクト作成**
   - [Google Cloud Console](https://console.cloud.google.com/)にアクセス
   - 新しいプロジェクトを作成（例：「Golf AI Strategist」）

2. **Google Drive APIを有効化**
   - 「APIとサービス」→「ライブラリ」を選択
   - 「Google Drive API」を検索して有効化

3. **サービスアカウントを作成**
   - 「APIとサービス」→「認証情報」を選択
   - 「認証情報を作成」→「サービスアカウント」を選択
   - サービスアカウント名を入力（例：「golf-ai-storage」）
   - 「作成して続行」をクリック
   - 役割として「Editor」を選択
   - 「完了」をクリック

4. **サービスアカウントキーを作成**
   - 作成したサービスアカウントをクリック
   - 「キー」タブ→「鍵を追加」→「新しい鍵を作成」
   - JSONタイプを選択し、「作成」をクリック
   - JSONキーファイルがダウンロードされる

5. **環境変数の設定**
   - Renderダッシュボードで以下の変数を設定：
     - `USE_GOOGLE_DRIVE`: "true"
     - `GOOGLE_DRIVE_CREDENTIALS`: ダウンロードしたJSONキーの内容を文字列として入力（{}で囲まれた部分すべて）
     - `GOOGLE_DRIVE_FOLDER_ID`: （オプション）特定のフォルダを利用したい場合に設定

これにより、アップロードされたファイルは自動的にGoogle Driveに保存され、アプリケーション再起動後も利用可能になります。

## トラブルシューティング

### 一般的な問題と解決策

1. **デプロイに失敗する場合**
   - ログを確認して具体的なエラーを特定
   - `requirements.txt`に全ての依存関係が含まれているか確認

2. **アプリケーションが起動しない**
   - `Procfile`の構文を確認
   - アプリケーション構造とインポートパスを確認

3. **静的ファイル（CSS/JS）が読み込めない**
   - 開発モード（DEBUG）をオフにする
   - Flask設定で静的ファイルの提供方法を確認

4. **SocketIOの接続エラー**
   - クライアントとサーバーのSocketIOバージョン互換性を確認
   - CORS設定を確認

## サポートとリソース

- [Render ドキュメント](https://render.com/docs)
- [Flask ドキュメント](https://flask.palletsprojects.com/)
- [Flask-SocketIO ドキュメント](https://flask-socketio.readthedocs.io/)
- [Perplexity API ドキュメント](https://docs.perplexity.ai/)
