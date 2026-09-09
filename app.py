import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage  # 1. 新增匯入 ImageMessage
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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # .strip() 去除前後空格，.lower() 將英文一律轉為小寫
    user_message = event.message.text.strip().lower()
    reply_messages = []

    # 範例 1：純文字回應
    if user_message == "你好":
        reply_messages.append(TextMessage(text="你好我是阿財！很高興為您服務。"))

    # 範例 4：純文字 + 超連結網址
    elif user_message == "lcw":
        reply_messages.append(
            TextMessage(text="歡迎造訪我們的LCW官方網站：\nhttps://aweidesign.why3s.tw/lcwmade/index.html")
        )

    # 範例 2：單獨回應圖片
    elif user_message == "菜單":
        menu_img_url = "https://example.com/menu.jpg"  # 替換為你的公開圖片網址
        reply_messages.append(
            ImageMessage(
                original_content_url=menu_img_url,  # 點開看的原圖
                preview_image_url=menu_img_url       # 聊天室顯示的縮圖
            )
        )

    # 範例 3：同時回應「文字 + 圖片」
    elif user_message == "優惠":
        promo_img_url = "https://example.com/promo.jpg"
        reply_messages.append(TextMessage(text="這是我們本月最新的優惠活動："))
        reply_messages.append(
            ImageMessage(
                original_content_url=promo_img_url,
                preview_image_url=promo_img_url
            )
        )

    # 沒命中任何關鍵字，直接 return 不回覆
    if not reply_messages:
        return

    # 發送訊息
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=reply_messages
            )
        )

if __name__ == "__main__":
    app.run(port=5000)
