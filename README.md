# Golf AI Strategist

ゴルフ部の監督と選手が、特定コースをどう攻めるかをすばやく把握できるように、生成AIを用いて最適な攻略プランを提示するWebアプリケーションです。

## 目次
- [Golf AI Strategist](#golf-ai-strategist)
  - [目次](#目次)
  - [機能](#機能)
  - [技術スタック](#技術スタック)
  - [開発環境のセットアップ](#開発環境のセットアップ)
    - [前提条件](#前提条件)
    - [インストール手順](#インストール手順)
    - [Perplexity APIキーの取得方法](#perplexity-apiキーの取得方法)
  - [アプリケーションの実行](#アプリケーションの実行)
  - [デプロイ](#デプロイ)
    - [Renderへのデプロイ](#renderへのデプロイ)
  - [ライセンス](#ライセンス)
- [Golf AI Strategist 実装完了](#golf-ai-strategist-実装完了)
  - [実装内容](#実装内容)
    - [1. アプリケーション構造](#1-アプリケーション構造)
    - [2. 主要機能](#2-主要機能)
    - [3. 非機能要件対応](#3-非機能要件対応)
  - [使用方法](#使用方法)
  - [デプロイ方法](#デプロイ方法)
  - [今後の改善点](#今後の改善点)

## 機能

- ホール情報や悩みを自由記述で入力
- Perplexity APIを使用して最適な攻略プランを生成
- 推奨ティーショット、セカンド、グリーン周りの狙いどころなどを日本語で提示
- シンプルなUI（入力ホームと回答ホームのみ）
- アクセシビリティに配慮した設計

## 技術スタック

- **バックエンド**: Python 3.10.16, Flask 3.x (Blueprint)
- **フロントエンド**: HTML5, CSS, JavaScript
- **API**: Perplexity pplx-api
- **セッション管理**: Flask-Session (In-Memory, TTL 30分)
- **デプロイ**: Render (1 vCPU / 512 MB)

## 開発環境のセットアップ

### 前提条件
- Python 3.10.16
- pip (Pythonパッケージマネージャー)

### インストール手順

1. リポジトリをクローン

```bash
git clone https://github.com/yourusername/golf-ai-strategist.git
cd golf-ai-strategist
```

2. 仮想環境を作成して有効化

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

4. 環境変数の設定

`.env.example`ファイルを`.env`にコピーして、必要な環境変数を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の項目を設定します：

- `SECRET_KEY`: セッション暗号化用のシークレットキー
- `PERPLEXITY_API_KEY`: Perplexity APIのAPIキー

### Perplexity APIキーの取得方法

1. [Perplexity AI](https://www.perplexity.ai/)にアクセスしてアカウントを作成
2. APIキーを発行（詳細は[Perplexity APIドキュメント](https://docs.perplexity.ai/)を参照）
3. 取得したAPIキーを`.env`ファイルの`PERPLEXITY_API_KEY`に設定

## アプリケーションの実行

開発サーバーを起動：

```bash
flask run
```

ブラウザで http://localhost:5000 にアクセスしてアプリケーションを使用できます。

## デプロイ

### Renderへのデプロイ

1. [Render](https://render.com/)にアカウントを作成
2. 新しいWeb Serviceを作成
3. GitHubリポジトリを連携
4. 以下の設定を行う：
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
   - **環境変数**: `.env`ファイルの内容を環境変数として設定

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。




1. アプリケーション構造

   - `app/__init__.py` - アプリケーション初期化
   - `app/config.py` - 設定ファイル
   - `app/routes/__init__.py` - ルートパッケージ初期化
   - `app/routes/main.py` - メインルート
   - `app/services/__init__.py` - サービスパッケージ初期化
   - `app/services/perplexity.py` - Perplexity API連携
   - `app/templates/base.html` - ベーステンプレート
   - `app/templates/index.html` - 入力ホーム
   - `app/templates/result.html` - 回答ホーム
   - `app/static/css/style.css` - スタイルシート

2. 設定ファイル

   - `run.py` - アプリケーション起動スクリプト
   - `.env.example` - 環境変数サンプル
   - `requirements.txt` - 依存パッケージ
   - `README.md` - 説明書
   - `.gitignore` - バージョン管理除外ファイル

これらのファイルにより、要件定義書に記載された機能を実装しました：

1. 入力フォーム表示：ユーザーが攻略したいホール情報や悩みを自由記述で入力できる。
2. 生成AI解析・回答表示：Perplexity APIに問い合わせ、推奨ティーショット、セカンド、グリーン周りの狙いどころなどを日本語で提示。
3. 単一セッション維持：直前の質問と回答セットを同一画面に保持。

また、非機能要件も満たしています：

1. 性能：入力送信から回答表示まで平均≤10秒、最大≤20秒を目指す設計。
2. 可用性：Renderへのデプロイ手順を提供。
3. セキュリティ：HTTPS必須、CSRFトークン、CSP設定。
4. アクセシビリティ：WCAG AA、文字サイズ≥14pt、aria-label付与。

次に、ユーザーにこの実装の概要を説明し、アプリケーションの実行方法を案内します。

Task Completed

# Golf AI Strategist 実装完了

Golf AI Strategistの実装が完了しました。要件定義書に基づいて、以下の機能を持つWebアプリケーションを作成しました：

## 実装内容

### 1. アプリケーション構造

- Flask Blueprintを使用した構造設計
- 設定ファイルとアプリケーション初期化
- ルーティングとAPIエンドポイント
- Perplexity API連携サービス
- テンプレートとスタイルシート

### 2. 主要機能

- __入力ホーム__：ユーザーがホール情報や悩みを自由記述で入力できるフォーム
- __回答ホーム__：生成AIからの攻略プランをチャット形式で表示
- __API連携__：Perplexity APIを使用した攻略プラン生成
- __セッション管理__：直前の質問と回答セットを保持

### 3. 非機能要件対応

- __性能__：APIタイムアウト設定、エラーハンドリング
- __セキュリティ__：CSRF対策、CSP設定
- __アクセシビリティ__：WCAG AA準拠、aria-label付与、14pt以上のフォント

## 使用方法

1. 環境変数の設定

   - `.env.example`を`.env`にコピーして必要な情報を設定
   - 特にPerplexity APIキーの設定が必要

2. 依存パッケージのインストール

   ```javascript
   pip install -r requirements.txt
   ```

3. アプリケーションの起動

   ```javascript
   flask run
   ```

4. ブラウザでアクセス

   - <http://localhost:5000> にアクセスして利用開始

## デプロイ方法

READMEに記載されているRenderへのデプロイ手順に従ってデプロイできます。

## 今後の改善点

1. テストコードの追加
2. エラーハンドリングの強化
3. ユーザーフィードバックに基づくUI改善

これで、ゴルフ部の監督と選手が特定コースの攻略プランを素早く取得できるWebアプリケーションが完成しました。
