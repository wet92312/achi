from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# 填入你的 Token 與 Secret
CHANNEL_ACCESS_TOKEN = 'g49CdDG9Ww3jZ7+E0VpI4eqfJ6dEsTNHk4haEkuXPKGtKzUzosUq51V48qoi5pXZFZyXnXn6zTlVYGTsWteX4Lg6/ri75Up3J2zkYfGEj16SCJpQjHNotR1i7D7w2dFAuC/TxvkNFtk95MHcI8hxYgdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = '42832156485a47b6b5d392221bd7c672'

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 關鍵字判斷邏輯
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text.strip()
    reply_text = None
    
    # 關鍵字比對
    if user_message == "你好":
        reply_text = "你好我是阿財！很高興為您服務。"
    elif "營業時間" in user_message:
        reply_text = "我們的營業時間為週一至週五 09:00 - 18:00。"
    elif user_message == "位置":
        reply_text = "我們部位於台北市信義區..."
    else:
        reply_text = f"收到您的訊息：「{user_message}」。目前尚未設定此關鍵字回應。"

    # 沒講到關鍵字就不處理、不發送任何回覆
    if not reply_text:
        return

    # 有命中關鍵字才執行傳送訊息
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    app.run(port=5000)
