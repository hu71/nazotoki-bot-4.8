import os
import time
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

# Flaskアプリケーションの設定
app = Flask(__name__)

# ==== LINE Bot API設定 ====
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET must be set in environment variables.")

try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
except LineBotApiError as e:
    raise ValueError(f"Invalid LINE_CHANNEL_ACCESS_TOKEN: {str(e)}")

handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ==== 謎の問題データ ====
questions = [
    {
        "story_messages": [
            {"text": "第1問のストーリー第一部", "delay_seconds": 1},
            {"text": "第1問のストーリー第二部", "delay_seconds": 2}
        ],
        "puzzle_message": {"text": "第1問の問題文", "delay_seconds": 1.5},
        "image_url": {"url": "https://drive.google.com/uc?export=view&id=XXXXX1", "delay_seconds": 2},
        "hint_keyword": "hint1",
        "hint_text": "第1問のヒントです",
        "correct_answer": "correct1"
    },
    # (他の質問データは省略、必要に応じて追加)
    {
        "story_messages": [
            {"text": "第5問のストーリー第一部", "delay_seconds": 1}
        ],
        "puzzle_message": {"text": "第5問の問題文", "delay_seconds": 1},
        "image_url": {"url": "https://drive.google.com/uc?export=view&id=XXXXX5", "delay_seconds": 1.5},
        "hint_keyword": "hint5",
        "hint_text": "第5問のヒントです",
        "correct_answer": ["correct5a", "correct5b"],
        "good_end_story": [
            {"text": "Goodエンドのストーリー第一部", "delay_seconds": 1},
            {"text": "Goodエンドのストーリー第二部", "delay_seconds": 1}
        ],
        "bad_end_story": [
            {"text": "Badエンドのストーリー第一部", "delay_seconds": 1},
            {"text": "Badエンドのストーリー第二部", "delay_seconds": 1}
        ]
    },
    {
        "story_messages": [
            {"text": "終章のストーリー第一部", "delay_seconds": 1},
            {"text": "終章のストーリー第二部", "delay_seconds": 1}
        ],
        "puzzle_message": {"text": "終章のおまけ謎", "delay_seconds": 2},
        "image_url": {"url": "https://drive.google.com/uc?export=view&id=XXXXX6", "delay_seconds": 1},
        "hint_keyword": "hint6",
        "hint_text": "終章のヒントです",
        "correct_answer": "correct6"
    }
]

# ==== ユーザーごとの進行状況と回答 ====
user_states = {}  # {user_id: {"current_q": int, "answers": [list of answers]}}

# ==== 関数: メッセージを安全に送信 (レート制限対策付き) ===
def send_message_with_retry(user_id, message, delay_seconds=0):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            line_bot_api.push_message(user_id, message)
            time.sleep(delay_seconds)
            break
        except LineBotApiError as e:
            if getattr(e, 'status_code', None) == 429:
                wait_time = 60  # デフォルトで60秒待つ（Retry-Afterがあれば調整）
                if 'retry_after' in e.error_details:
                    wait_time = int(e.error_details['retry_after'])
                print(f"Rate limit exceeded for {user_id}. Retrying after {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"Failed to send message to {user_id}: {str(e)} - Status code: {getattr(e, 'status_code', 'N/A')}")
                raise

def send_content(user_id, content_type, content_data, next_qnum=None):
    try:
        if content_type == "question":
            q = content_data
            for story_msg in q["story_messages"]:
                send_message_with_retry(user_id, TextSendMessage(text=story_msg["text"]), story_msg["delay_seconds"])
            send_message_with_retry(user_id, TextSendMessage(text=q["puzzle_message"]["text"]), q["puzzle_message"]["delay_seconds"])
            send_message_with_retry(
                user_id,
                ImageSendMessage(original_content_url=q["image_url"]["url"], preview_image_url=q["image_url"]["url"]),
                q["image_url"]["delay_seconds"]
            )
            send_message_with_retry(user_id, TextSendMessage(text="答えとなるテキストを送ってね！"))
        elif content_type == "end_story":
            for story_msg in content_data:
                send_message_with_retry(user_id, TextSendMessage(text=story_msg["text"]), story_msg["delay_seconds"])
            if next_qnum is not None:
                send_question(user_id, next_qnum)
    except LineBotApiError as e:
        print(f"Failed to send content to {user_id}: {str(e)} - Status code: {getattr(e, 'status_code', 'N/A')}")
        raise

def send_question(user_id, qnum):
    if qnum < len(questions):
        send_content(user_id, "question", questions[qnum])
    else:
        line_bot_api.push_message(user_id, TextSendMessage(text="全ての問題が終了しました！"))

# ==== Webhookエンドポイント ====
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    print(f"Received body at {os.getcwd()}: {body}")
    print(f"Signature: {signature}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature error")
        return "Invalid signature", 400
    except Exception as e:
        print(f"Callback error: {str(e)}")
        return "Internal server error", 500
    return "OK", 200

# ==== メッセージ受信時の処理 ====
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if text.lower() == "start":
        user_states[user_id] = {"current_q": 0, "answers": []}
        send_question(user_id, 0)
        return

    if user_id in user_states:
        qnum = user_states[user_id]["current_q"]
        if qnum < len(questions):
            q = questions[qnum]
            if text.lower() == q["hint_keyword"].lower():
                send_message_with_retry(user_id, TextSendMessage(text=q["hint_text"]))
                return
            if isinstance(q["correct_answer"], list):
                if qnum == 4 and text.lower() in q["correct_answer"]:  # 第5問
                    if text.lower() == q["correct_answer"][0]:  # correct5a → Goodエンド
                        send_content(user_id, "end_story", q["good_end_story"], 5)
                    elif text.lower() == q["correct_answer"][1]:  # correct5b → Badエンド
                        send_content(user_id, "end_story", q["bad_end_story"], 5)
                    return
            elif text.lower() == q["correct_answer"].lower():  # 通常の正解
                if qnum < 4:
                    user_states[user_id]["current_q"] += 1
                    send_question(user_id, user_states[user_id]["current_q"])
                elif qnum == 5:  # 終章
                    send_message_with_retry(user_id, TextSendMessage(text="大正解！探偵事務所にお越しください。"))
                    user_states[user_id]["current_q"] += 1
                    send_question(user_id, user_states[user_id]["current_q"])
                    return
            else:  # 不正解
                send_message_with_retry(user_id, TextSendMessage(text=f"残念。不正解です。{q['hint_keyword']}と送ると何かあるかも"))
                return

    send_message_with_retry(user_id, TextSendMessage(text="メッセージを理解できませんでした."))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
