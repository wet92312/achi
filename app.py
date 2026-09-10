import os
import requests
import urllib3
import traceback
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')
CWA_API_KEY = os.environ.get('CWA_API_KEY')

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

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

def get_weather_icon(wx_text):
    if not wx_text:
        return "🌤️"
    if "雷" in wx_text:
        return "🌩️"
    elif "雨" in wx_text:
        return "🌧️"
    elif "陰" in wx_text:
        return "☁️"
    elif "多雲" in wx_text:
        return "⛅"
    elif "晴" in wx_text:
        return "☀️"
    return "🌤️"

def create_apple_weather_flex(target_city, wx, min_t, max_t, pop, ci):
    # 數值防呆與轉字串
    target_city = str(target_city or "未知縣市")
    wx = str(wx or "未知")
    min_t = str(min_t or "0")
    max_t = str(max_t or "0")
    pop = str(pop or "0")
    ci = str(ci or "舒適")

    icon = get_weather_icon(wx)
    
    try:
        pop_num = int(pop)
    except (ValueError, TypeError):
        pop_num = 0

    pop_percent = f"{max(5, min(100, pop_num))}%"

    if pop_num >= 50:
        tip = "☔ 降雨機率偏高，出門記得帶把傘！"
    elif "晴" in wx:
        tip = "🕶️ 晴朗好天氣，適合安排戶外活動！"
    else:
        tip = f"💡 目前體感{ci}，外出建議穿著適當衣物。"

    flex_json = {
        "type": "bubble",
        "styles": {
            "body": {
                "backgroundColor": "#1E293B"
            }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "lg",
            "contents": [
                # 📢 最前面加入：阿財播報員開場白
                {
                    "type": "text",
                    "text": "🎙️ 我是阿財，現在為您播報氣象～",
                    "size": "xs",
                    "color": "#38BDF8",
                    "weight": "bold"
                },
                # 城市名稱
                {
                    "type": "text",
                    "text": target_city,
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FFFFFF",
                    "margin": "xs"
                },
                {
                    "type": "text",
                    "text": "未來 12 小時天氣預報",
                    "size": "xs",
                    "color": "#94A3B8"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "lg",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": f"{max_t}°C",
                                    "size": "3xl",
                                    "weight": "bold",
                                    "color": "#FFFFFF"
                                },
                                {
                                    "type": "text",
                                    "text": f"{wx} · {ci}",
                                    "size": "sm",
                                    "color": "#CBD5E1",
                                    "margin": "sm"
                                }
                            ]
                        },
                        {
                            "type": "text",
                            "text": icon,
                            "size": "3xl",
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"▲ 最高 {max_t}°",
                            "size": "xs",
                            "color": "#F87171",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": f"▼ 最低 {min_t}°",
                            "size": "xs",
                            "color": "#60A5FA",
                            "weight": "bold"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": "#334155"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "☔ 降雨機率",
                                    "size": "xs",
                                    "color": "#94A3B8"
                                },
                                {
                                    "type": "text",
                                    "text": f"{pop}%",
                                    "size": "xs",
                                    "color": "#38BDF8",
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#334155",
                            "height": "8px",
                            "cornerRadius": "4px",
                            "margin": "xs",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": "#38BDF8",
                                    "height": "8px",
                                    "width": pop_percent,
                                    "cornerRadius": "4px",
                                    "contents": []
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "lg",
                    "backgroundColor": "#0F172A",
                    "cornerRadius": "md",
                    "paddingAll": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": tip,
                            "size": "xs",
                            "color": "#38BDF8",
                            "wrap": True
                        }
                    ]
                }
            ]
        }
    }
    
    flex_container = FlexContainer.from_dict(flex_json)
    return FlexMessage(
        alt_text=f"我是阿財~{target_city}天氣預報",
        contents=flex_container
    )

def get_taiwan_weather(city_input):
    if not CWA_API_KEY:
        return TextMessage(text="系統未設定氣象 API 金鑰。")

    target_city = CITY_MAPPING.get(city_input)
    if not target_city:
        return None

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": CWA_API_KEY.strip(),
        "locationName": target_city
    }
    
    try:
        res = requests.get(url, params=params, timeout=8, verify=False)
        if res.status_code != 200:
            return TextMessage(text=f"氣象 API 連線失敗 (HTTP {res.status_code})")

        data = res.json()
        locations = data.get('records', {}).get('location', [])
        if not locations:
            return TextMessage(text="查無該縣市氣象資料。")

        location_data = locations[0]
        
        elements = {}
        for item in location_data.get('weatherElement', []):
            e_name = item.get('elementName')
            time_list = item.get('time', [])
            if time_list and 'parameter' in time_list[0]:
                param_val = time_list[0]['parameter'].get('parameterName')
                elements[e_name] = param_val if param_val is not None else ""

        wx = elements.get('Wx') or '未知'
        pop = elements.get('PoP') or '0'
        min_t = elements.get('MinT') or '0'
        max_t = elements.get('MaxT') or '0'
        ci = elements.get('CI') or '舒適'

        return create_apple_weather_flex(target_city, wx, min_t, max_t, pop, ci)

    except Exception as e:
        print(f"❌ Exception Detail:\n{traceback.format_exc()}")
        return TextMessage(text="無法取得氣象資料，請稍後再試。")

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
    reply_messages = []

    cleaned_msg = user_message.replace("天氣", "").replace("氣象", "").strip()
    weather_flex = get_taiwan_weather(cleaned_msg)
    
    if weather_flex:
        reply_messages.append(weather_flex)
    elif user_message == "hello":
        reply_messages.append(TextMessage(text="你好！請輸入縣市名稱（例如：台北天氣、高雄天氣）即可獲得極簡風氣象卡片喔！"))

    if not reply_messages:
        return

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
