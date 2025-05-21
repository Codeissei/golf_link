from flask import (
    Blueprint, flash, g, redirect, render_template, 
    request, session, url_for, jsonify, current_app
)
from werkzeug.exceptions import BadRequest, RequestTimeout
import uuid
import time
from datetime import datetime, timezone, timedelta
import json

from app.services.perplexity import query_perplexity

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """入力ホームを表示"""
    return render_template('index.html')

@bp.route('/result')
def result():
    """回答ホームを表示"""
    # セッションからQ&Aを取得
    qa = session.get('qa', [])
    return render_template('result.html', qa=qa)

@bp.route('/api/ask', methods=['POST'])
def ask():
    """Perplexity APIに質問を送信し、回答を取得"""
    start_time = time.time()
    req_id = str(uuid.uuid4())
    
    try:
        # リクエストからテキストを取得
        if not request.is_json:
            raise BadRequest("JSONリクエストが必要です")
        
        data = request.get_json()
        user_input = data.get('question', '').strip()
        
        # 入力バリデーション
        if not user_input:
            return jsonify({
                'error': '質問を入力してください',
                'status': 'error'
            }), 400
        
        if len(user_input) > 1000:
            return jsonify({
                'error': '質問は1000文字以内にしてください',
                'status': 'error'
            }), 400
        
        # Perplexity APIに問い合わせ
        response = query_perplexity(user_input)
        
        # レスポンスを処理
        answer = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        usage = response.get('usage', {})
        
        # タイムスタンプを生成（日本時間 = UTC+9）
        jst = timezone(timedelta(hours=9))
        timestamp = datetime.now(jst).isoformat()
        
        # セッションにQ&Aを保存
        qa_item = {
            'q': user_input,
            'a': answer,
            'ts': timestamp
        }
        
        # セッションを更新
        session['qa'] = [qa_item]  # 最大1件のみ保存
        
        # レスポンスタイム計算
        response_time = time.time() - start_time
        
        # ログ出力
        current_app.logger.info(
            f"REQ_ID:{req_id} LATENCY:{response_time:.2f}s "
            f"TOKENS:{usage.get('total_tokens', 0)} "
            f"(P:{usage.get('prompt_tokens', 0)}, C:{usage.get('completion_tokens', 0)})"
        )
        
        return jsonify({
            'answer': answer,
            'status': 'success',
            'response_time': f"{response_time:.2f}"
        })
        
    except RequestTimeout:
        current_app.logger.error(f"ERROR pplx_timeout REQ_ID:{req_id}")
        return jsonify({
            'error': '混雑しています。後で試してください',
            'status': 'error'
        }), 503
        
    except Exception as e:
        error_type = type(e).__name__
        current_app.logger.error(f"ERROR pplx_status:{error_type} REQ_ID:{req_id} MSG:{str(e)}")
        return jsonify({
            'error': '混雑しています。後で試してください',
            'status': 'error'
        }), 503
