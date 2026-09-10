import os
import requests
import urllib3  # 新增：用於關閉 SSL 警告

# 關閉 urllib3 產生的 SSL 警告訊息（讓 Render Logs 保持乾淨）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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

CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')
CWA_API_KEY = os.environ.get('CWA_API_KEY')  # 氣象署 API Key

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 台灣縣市名稱常用對照表
CITY_MAPPING = {
    "台北": "臺北市", "臺北": "臺北市", "台北市": "臺北市", "臺北市": "臺北市",
    "新北": "新北市", "新北市": "新北市",
    "基隆": "基隆市", "基隆市": "基隆市",
    "桃園": "桃園市", "桃園市": "桃園市",
    "新竹": "新竹市", "新竹市": "新竹市", "新竹縣": "新竹縣",
    "苗栗": "苗栗縣", "苗栗縣": "苗栗縣",
    "台中": "臺中市", "臺中": "臺中市", "台中市": "臺中市", "臺中市": "臺中市",
    "彰化": "彰化縣", "彰化縣": "彰化縣",
    "南投": "南投縣", "南投縣": "南投縣",
    "雲林": "雲林縣", "雲林縣": "雲林縣",
    "嘉義": "嘉義市", "嘉義市": "嘉義市", "嘉義縣": "嘉義縣",
    "台南": "臺南市", "臺南": "臺南市", "台南市": "臺南市", "臺南市": "臺南市",
    "高雄": "高雄市", "高雄市": "高雄市",
    "屏東": "屏東縣", "屏東縣": "屏東縣",
    "宜蘭": "宜蘭縣", "宜蘭縣": "宜蘭縣",
    "花蓮": "花蓮縣", "花蓮縣": "花蓮縣",
    "台東": "臺東縣", "臺東": "臺東縣", "台東縣": "臺東縣", "臺東縣": "臺東縣",
    "澎湖": "澎湖縣", "澎湖縣": "澎湖縣",
    "金門": "金門縣", "金門縣": "金門縣",
    "馬祖": "連江縣", "連江": "連江縣"
}

def get_taiwan_weather(city_input):
    """呼叫中央氣象署 API 取得預報（新增 verify=False 忽略 SSL 驗證）"""
    if not CWA_API_KEY:
        print("❌ 錯誤: 未設定 CWA_API_KEY 環境變數")
        return "系統未設定氣象 API 金鑰。"

    target_city = CITY_MAPPING.get(city_input)
    if not target_city:
        return None

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": CWA_API_KEY.strip(),
        "locationName": target_city
    }
    
    try:
        # 🔥 在此處加入 verify=False 繞過憑證問題
        res = requests.get(url, params=params, timeout=8, verify=False)
        
        if res.status_code != 200:
            print(f"❌ API 請求失敗，狀態碼: {res.status_code}, 回覆: {res.text}")
            return f"氣象 API 連線失敗 (HTTP {res.status_code})"

        data = res.json()
        locations = data.get('records', {}).get('location', [])
        if not locations:
            return "查無該縣市氣象資料。"

        location_data = locations[0]
        elements = {
            item['elementName']: item['time'][0]['parameter']['parameterName'] 
            for item in location_data.get('weatherElement', [])
        }
        
        wx = elements.get('Wx', '未知')
        pop = elements.get('PoP', '0')
        min_t = elements.get('MinT', '')
        max_t = elements.get('MaxT', '')
        ci = elements.get('CI', '')
        
        msg = f"🌤️【{target_city} 未來12小時預報】\n"
        msg += f"• 天氣狀況：{wx}\n"
        msg += f"• 預估氣溫：{min_t}°C ~ {max_t}°C ({ci})\n"
        msg += f"• 降雨機率：{pop}%"
        return msg

    except Exception as e:
        print(f"❌ Exception 錯誤詳細資訊: {e}")
        return "無法取得氣象資料，請稍後再試。"

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
    user_message = event.message.text.strip().lower()
    reply_text = None

    # 1. 判斷是否為天氣查詢（例如輸入：台北天氣、天氣 台北、高雄天氣）
    cleaned_msg = user_message.replace("天氣", "").replace("氣象", "").strip()
    weather_result = get_taiwan_weather(cleaned_msg)
    
    if weather_result:
        reply_text = weather_result
    # 2. 一般關鍵字判斷
    elif user_message == "hello":
        reply_text = "你好！發送縣市名稱（如：台北天氣）可查詢最新氣象喔！"

    # 沒命中關鍵字或無氣象資料時不回覆
    if not reply_text:
        return

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
