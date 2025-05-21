from flask import current_app
from werkzeug.exceptions import RequestTimeout, ServiceUnavailable
from openai import OpenAI

def query_perplexity(user_input):
    """
    Perplexity APIに問い合わせを行う
    
    Args:
        user_input (str): ユーザーからの入力テキスト
        
    Returns:
        dict: APIからのレスポンス
        
    Raises:
        RequestTimeout: リクエストがタイムアウトした場合
        ServiceUnavailable: APIが利用できない場合
    """
    # APIキーを取得
    api_key = current_app.config.get('PERPLEXITY_API_KEY')
    if not api_key:
        current_app.logger.error("Perplexity API キーが設定されていません")
        raise ServiceUnavailable("API設定エラー")
    
    # システムプロンプトを設定
    system_prompt = (
        "You are a professional golf caddie with extensive knowledge of golf course strategy. "
        "Provide specific advice for the hole described by the user. "
        "Include recommendations for tee shot direction, club selection, approach strategy, "
        "and green reading. Consider any weather conditions or player tendencies mentioned. "
        "Keep your response concise but thorough, focusing on practical advice. "
        "Respond in Japanese only."
    )
    
    # メッセージを設定
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    try:
        # OpenAIクライアントを初期化（プロキシ設定を無効化）
        import httpx
        http_client = httpx.Client(proxies=None)
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai",
            http_client=http_client
        )
        
        # チャット完了をリクエスト
        response = client.chat.completions.create(
            model=current_app.config.get('PERPLEXITY_MODEL', 'sonar-pro'),
            messages=messages,
            max_tokens=current_app.config.get('PERPLEXITY_MAX_TOKENS', 1024),
            temperature=current_app.config.get('PERPLEXITY_TEMPERATURE', 0.7),
            stream=False
        )
        
        # レスポンスを辞書形式に変換
        return {
            'choices': [{
                'message': {
                    'content': response.choices[0].message.content
                }
            }],
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"Perplexity API エラー: {str(e)}")
        raise ServiceUnavailable(f"APIエラー: {str(e)}")
