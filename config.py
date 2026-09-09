import os
from pathlib import Path

# 기본 작업 디렉토리 설정
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"

TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 릴스 비디오 규격 (9:16)
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
FPS = 30

# 폰트 경로 (프로젝트 내장 무료 나눔고딕 볼드 우선 사용)
BUNDLE_FONT_PATH = BASE_DIR / "fonts" / "NanumGothic-Bold.ttf"
if BUNDLE_FONT_PATH.exists():
    DEFAULT_FONT_PATH = str(BUNDLE_FONT_PATH)
elif os.path.exists(r"C:\Windows\Fonts\malgunbd.ttf"):
    DEFAULT_FONT_PATH = r"C:\Windows\Fonts\malgunbd.ttf"
else:
    DEFAULT_FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"
