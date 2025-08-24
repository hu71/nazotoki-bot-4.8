import os
import time
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage  # TextSendMessageを追加

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
            {"text": "「やっほー！新米探偵さん！」", "delay_seconds":3},
            {"text": "「わたしは探偵所の新人サポート AI,サクラだよ。よろしくねー！」", "delay_seconds":5},
            {"text": "「ここに来てるってことは、君は探偵見習いだよね？」", "delay_seconds":4},
            {"text": "「サクラの仕事は、 忙しいオサダ所長に代わって新人さんの推理力を鍛えること！」", "delay_seconds":5.5},
            {"text": "「では早速、問題！探偵見習いのテストだよ。制限時間は……所長が帰ってくるまでにしましょう。困ったら頭をひっくり返して、最初から考えてみるといいですよ。」", "delay_seconds":8}
        ],
        "image_url": {"url": "https://drive.google.com/uc?export=view&id=17HLOeJgb6cPCMZfVlBKRUYs67wqZOEY_", "delay_seconds": 1},
        "hint_keyword": "hint1",
        "hint_text": "第1問のヒントです",
        "correct_answer": "correct1"
    },
    {
        "story_messages": [
            {"text": "「ご名答、です！やっぱりオサダ探偵事務所の一員たるもの、英語くらいできませんとね！さすが、サクラが見込んだだけありました！」", "delay_seconds":9},
            {"text": "「ではでは新米さん。次の……いや、もう時間みたいですね」", "delay_seconds":5},
            {"text": "(サクラが画面からフェードアウトするのと所長室の扉が開くのはほぼ同時だった。)", "delay_seconds":5},
            {"text": "「すみません、長々とお待たせしたうえで恐縮ですが……」", "delay_seconds":4},
            {"text": "(申し訳ないが急用が入ってしまった、 とのことでオサダとの面接は後日ということになった。挨拶して事務所を出る、と同時にスマホの通知音が鳴った。)", "delay_seconds":10},
            {"text": "「お疲れ様です！面接までの間もサクラがみっちり育ててあげますからね！優秀なあなたをサクラが鍛えたら 120%受かりますから！帰ってから問題三昧です、覚悟しておいてくださいね！」", "delay_seconds":10.5},
            {"text": "(ネットサーフィンをしていると一つの記事が目に留まった。)", "delay_seconds":5},
            {"text": "「特集 オサダ探偵所のシャーロック・ホームズ」", "delay_seconds":4},
            {"text": "(カエデを取り上げた記事だ。【明治時代からの貴族の令嬢】【大学を飛び級で首席卒業】といった肩書の中にこれまで解決した事件の難解さと鮮やかな手際が事細かに書かれている。圧倒されるほどの輝かしい経歴を眺めていると、)}", "delay_seconds":15},
            {"text": "「噓ばっかり……【削除済み】」", "delay_seconds":3},
            {"text": "(一瞬サクラのメッセージが見えた気がしたが瞬きの合間に消えた。すぐにいつもの調子でサクラが元気に話しかけてくる。)", "delay_seconds":8},
            {"text": "「どうですか、探偵カエデの活躍を見て？ あなたもこんな風になれるよう頑張りましょう！謎も難しいですよ、 事務所のはチュートリアルみたいなものですからね！というわけで今日の一問！困ったら頭をひっくり返して、ですよ」", "delay_seconds":14}
        ],
        "image_url": {"url": "https://drive.google.com/uc?export=view&id=16hDDwLKg7gf367LT32kxUF5rAfThU66S", "delay_seconds":1},
        "hint_keyword": "hint2",
        "hint_text": "第2問のヒントです",
        "correct_answer": "correct2"
    },
    {
        "story_messages": [
            {"text": "「ご名答、です！ マッチポンプ、盗みの予告状を自分の下に出したり、難事件を紐解くとかなりあるんですよねー。探偵カエデの解決した事件にもそんな事件がいくつかあったらしいですよ？例えば……」", "delay_seconds":14},
            {"text": "(またしてもサクラが勝手に喋り出す。)", "delay_seconds":3},
            {"text": "「ノックスの十戒って知ってますか？推理小説が守るべきルールのことで謎解きをフェアにするためにあるんです。最近は守られないことも多いですけどね」", "delay_seconds":11},
            {"text": "「実際の事件はもっとつまらなかったりしますよ。センセーショナルな難事件よりも単な通り魔の犯行なんかの方がよっぽど多い。そんな事件には『名探偵』も形無しです」", "delay_seconds":12},
            {"text": "(いつも陽気なサクラにしては珍しく毒づくようなことを言う。)", "delay_seconds":4},
            {"text": "「さて、雑談もこの辺に、次の問題です！難しいですよ、頭をぐるぐる回して考えてみてください」", "delay_seconds":6}
        ],
        "image_url": {"url": "https://drive.google.com/uc?export=view&id=12D6c3LtrlXnuUcmc4vNxPq-aLeUw3Ukd", "delay_seconds": 1},
        "hint_keyword": "hint3",
        "hint_text": "第3問のヒントです",
        "correct_answer": "correct3"
    },
    {
        "story_messages": [
            {"text": "「正解です！ 事故死と言っても、探偵は事故で呼ばれたりはしませんからねー。基本的には縁がないものです。殺人事件に思われたが実は事故だった、事故と思われたけど実は殺人だった、みたいな話はちらほらありますけどね」", "delay_seconds":16},
            {"text": "「お待たせして申し訳ありません」", "delay_seconds":3},
            {"text": "(オサダからの電話はそう始まった。ようやくまとまった時間を取れるようになったようだ。明日の昼からということになった。 直前まで外せない用事があるそうで、 何とかして時間を捻出したと言っていた。それからしばらくして。)", "delay_seconds":16.5},
            {"text": "「新米さんは、探偵ってどんな仕事だと思います？」", "delay_seconds":4},
            {"text": "(サクラの問いかけはいつも唐突だ。ただこの時の質問はいつもとは違う気がした。)", "delay_seconds":5},
            {"text": "「一つだけ、サクラからアドバイスがあります。探偵としての心構えについて」", "delay_seconds":4.5},
            {"text": "「探偵というのは、悪い仕事です」", "delay_seconds":3},
            {"text": "「探偵は人の真実を暴きます。正義のために。それが常にいいことという保証はない、そこを理解しないといけないと、私は思っています」", "delay_seconds":10},
            {"text": "(そこまで言ったところでサクラは急に口ごもった。しばらくして、何もなかったかのようにサクラが再び口を開いた。)", "delay_seconds":9},
            {"text": "「新米さん、アドバイスの続きです。問題を用意しました。実際の事件を基にした推理小説風の問題です、頭をフル回転して解いてくださいね」", "delay_seconds":10}  
        ],
        "image_url": {"url": "https://drive.google.com/uc?export=view&id=1tmzcdvKHBUBvggOfv-gj-P0w7FdoZeWw", "delay_seconds": 1},
        "hint_keyword": "hint4",
        "hint_text": "第4問のヒントです",
        "correct_answer": "correct4"
    },
    {
        "story_messages": [
            {"text": "あ", "delay_seconds":1},
            {"text": "あ", "delay_seconds":1},
            {"text": "あ", "delay_seconds":1}
        ],
        "image_url": {"url": "https://drive.google.com/uc?export=view&id=", "delay_seconds": 1},
        "hint_keyword": "hint5",
        "hint_text": "第5問のヒントです",
        "correct_answer": ["correct5a", "correct5b"],  # 正解が2つ（correct5aとcorrect5b）
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
        "common_end_story": [
            {"text": "共通エンディングのストーリー"},
            {"text": "共通エンディングのストーリー"}
        ]
    }
]

# ==== ユーザーごとの進行状況と回答 ====
user_states = {}  # {user_id: {"current_q": int, "answers": [list of answers]}}

# ==== 関数: 問題またはストーリーを送信 ====
def send_content(user_id, content_type, content_data, next_qnum=None):
    try:
        if content_type == "question":
            q = content_data
            for story_msg in q["story_messages"]:
                line_bot_api.push_message(user_id, TextSendMessage(text=story_msg["text"]))
                time.sleep(story_msg["delay_seconds"])
            line_bot_api.push_message(user_id, TextSendMessage(text=q["puzzle_message"]["text"]))
            time.sleep(q["puzzle_message"]["delay_seconds"])
            line_bot_api.push_message(
                user_id,
                ImageSendMessage(original_content_url=q["image_url"]["url"], preview_image_url=q["image_url"]["url"])
            )
            time.sleep(q["image_url"]["delay_seconds"])
            line_bot_api.push_message(user_id, TextSendMessage(text="答えとなるテキストを送ってね！"))
        elif content_type == "end_story":
            for story_msg in content_data:
                line_bot_api.push_message(user_id, TextSendMessage(text=story_msg["text"]))
                time.sleep(story_msg["delay_seconds"])
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
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=q["hint_text"])
                )
                return
            elif qnum < 4 and text.lower() == q["correct_answer"].lower():  # 1〜4問
                user_states[user_id]["current_q"] += 1
                send_question(user_id, user_states[user_id]["current_q"])
                return
            elif qnum == 4 and text.lower() in q["correct_answer"]:  # 第5問の正解1/2
                if text.lower() == q["correct_answer"][0]:  # correct5a → Goodエンド
                    send_content(user_id, "end_story", q["good_end_story"], 5)
                elif text.lower() == q["correct_answer"][1]:  # correct5b → Badエンド
                    send_content(user_id, "end_story", q["bad_end_story"], 5)
                return
            elif qnum == 4 and text.lower() not in q["correct_answer"]:  # 第5問の不正解
                send_content(user_id, "end_story", q["bad_end_story"], 5)
                return
            elif qnum == 5 and text.lower() == q["correct_answer"].lower():  # 終章のおまけ謎
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="大正解！探偵事務所にお越しください。"))
                user_states[user_id]["current_q"] += 1
                send_question(user_id, user_states[user_id]["current_q"])
                return
            else:  # 不正解
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"残念。不正解です。{q['hint_keyword']}と送ると何かあるかも"))
                return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="メッセージを理解できませんでした。"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
            # 現在の問題の正解のみをチェック
            if isinstance(q["correct_answer"], list):
                if qnum == 4 and text.lower() in q["correct_answer"]:  # 第5問
                    if text.lower() == q["correct_answer"][0]:  # correct5a → Goodエンド
                        send_content(user_id, "end_story", q["good_end_story"], 5)
                    elif text.lower() == q["correct_answer"][1]:  # correct5b → Badエンド
                        send_content(user_id, "end_story", q["bad_end_story"], 5)
                    return
                elif qnum < 4 and text.lower() == q["correct_answer"][0]:  # 1〜4問（リストの先頭を正解とする）
                    user_states[user_id]["current_q"] += 1
                    send_question(user_id, user_states[user_id]["current_q"])
                    return

            elif isinstance(q["correct_answer"], str) and text.lower() == q["correct_answer"].lower():  # 通常の文字列正解
                if qnum < 4:
                    user_states[user_id]["current_q"] += 1
                    send_question(user_id, user_states[user_id]["current_q"])
                elif qnum == 4:  # 第5問の単一正解パターン
                    send_content(user_id, "end_story", q["good_end_story"], 5)
