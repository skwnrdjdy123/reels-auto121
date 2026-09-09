import os
import sys
import time
import requests
import json
from pathlib import Path
from config import BASE_DIR, OUTPUT_DIR
from pipeline import create_reels_pipeline

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN and os.path.exists(BASE_DIR / "telegram_token.txt"):
    BOT_TOKEN = (BASE_DIR / "telegram_token.txt").read_text().strip()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID_FILE = BASE_DIR / "admin_chat_id.txt"

def get_saved_chat_id():
    if CHAT_ID_FILE.exists():
        return CHAT_ID_FILE.read_text().strip()
    return None

def save_chat_id(chat_id):
    CHAT_ID_FILE.write_text(str(chat_id))

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    return requests.post(f"{API_URL}/sendMessage", json=payload).json()

def send_video(chat_id, video_path, caption="", reply_markup=None):
    data = {"chat_id": chat_id, "caption": caption}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    with open(video_path, "rb") as video_file:
        files = {"video": video_file}
        return requests.post(f"{API_URL}/sendVideo", data=data, files=files).json()

def run_bot():
    print("==========================================")
    print("🤖 릴스 매니저 텔레그램 봇 가동 시작!")
    print(f"🔗 봇 링크: https://t.me/Rellllllsssssss_bot")
    print("텔레그램 앱에서 위 봇에 들어가 /start 를 눌러주세요!")
    print("==========================================")

    last_update_id = 0

    while True:
        try:
            res = requests.get(
                f"{API_URL}/getUpdates",
                params={"offset": last_update_id + 1, "timeout": 20},
                timeout=25
            ).json()

            if not res.get("ok"):
                time.sleep(2)
                continue

            for update in res.get("result", []):
                last_update_id = update["update_id"]

                # 1. 인라인 버튼 클릭 처리 (Callback Query)
                if "callback_query" in update:
                    cb = update["callback_query"]
                    cb_id = cb["id"]
                    data = cb["data"]
                    c_chat_id = cb["message"]["chat"]["id"]

                    if data.startswith("approve_"):
                        video_name = data.replace("approve_", "")
                        send_message(
                            c_chat_id,
                            f"🎉 [승인 완료] 인스타그램 릴스 업로드가 승인되었습니다!\n(다음 단계에서 인스타 계정 연동 시 즉시 발행됩니다)\n파일: {video_name}"
                        )
                    elif data.startswith("reject_"):
                        send_message(c_chat_id, "🗑️ [반려 완료] 해당 영상은 발행이 취소되었습니다.")

                    # 콜백 알림 응답
                    requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": cb_id})
                    continue

                # 2. 일반 텍스트 메시지 수신 처리
                if "message" in update and "text" in update["message"]:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg["text"].strip()
                    user_name = msg["from"].get("first_name", "사용자")

                    # 관리자 Chat ID 저장
                    save_chat_id(chat_id)

                    if text.startswith("/start"):
                        welcome_text = (
                            f"반갑습니다, {user_name}님! 👋\n\n"
                            "🎬 **AI 해외 릴스 자동화 매니저**에 연결되었습니다!\n\n"
                            "💡 **사용 방법:**\n"
                            "1. 유튜브 쇼츠/릴스/틱톡 영상 링크를 이곳으로 보내주세요.\n"
                            "2. AI가 자동으로 9:16 릴스(배경 블러 + 한글 후킹 자막)로 편집하여 보내드립니다.\n"
                            "3. 영상을 보고 아래 [ ✅ 업로드 승인 ] 버튼만 누르면 끝!"
                        )
                        send_message(chat_id, welcome_text)
                        continue

                    # URL 감지 시 릴스 제작 실행
                    if text.startswith("http://") or text.startswith("https://"):
                        send_message(chat_id, "⏳ 영상을 분석하고 9:16 릴스로 제작 중입니다...\n잠시만 기다려 주세요! (약 15~20초 소요)")
                        try:
                            # 릴스 파이프라인 실행
                            reels_path = create_reels_pipeline(
                                video_url=text,
                                top_title="외국에서 난리 난 바이럴 영상 ㅋㅋㅋ",
                                bottom_text="끝까지 보면 소름 돋음 🤣"
                            )
                            filename = Path(reels_path).name

                            # 승인/반려 인라인 버튼
                            inline_keyboard = {
                                "inline_keyboard": [
                                    [
                                        {"text": "✅ 인스타 업로드 승인", "callback_data": f"approve_{filename}"},
                                        {"text": "❌ 반려/취소", "callback_data": f"reject_{filename}"}
                                    ]
                                ]
                            }

                            send_video(
                                chat_id=chat_id,
                                video_path=reels_path,
                                caption="✨ **릴스 제작이 완료되었습니다!**\n영상을 확인하고 아래 버튼을 눌러 승인해 주세요.",
                                reply_markup=inline_keyboard
                            )
                        except Exception as e:
                            send_message(chat_id, f"⚠️ 영상 제작 중 오류가 발생했습니다:\n{str(e)}")
                    else:
                        send_message(chat_id, "🔗 변환하고 싶은 영상(유튜브 쇼츠, 릴스 등)의 링크를 보내주세요!")

        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    run_bot()
