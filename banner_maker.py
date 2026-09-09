import os
from PIL import Image, ImageDraw, ImageFont
from config import TARGET_WIDTH, TARGET_HEIGHT, DEFAULT_FONT_PATH, TEMP_DIR

def create_top_ranking_header(
    line1_text: str = "역대급 해외 바이럴",
    line2_text: str = "웃긴 모먼트 TOP 5",
    sub_text: str = "(다들 몇 번이 제일 웃김? ㅋㅋㅋ)",
    font_path: str = DEFAULT_FONT_PATH,
    output_path: str = None
) -> str:
    """
    유튜브 쇼츠 인기 채널(역대급 랭킹 포맷) 스타일의 상단 고정 헤더 배너를 생성합니다.
    - 1줄: 핑크/퍼플 포인트 컬러 초굵은 볼드 텍스트
    - 2줄: 화이트 초굵은 볼드 텍스트
    - 3줄: 괄호 인터랙션 유도 서브 텍스트
    """
    if output_path is None:
        output_path = str(TEMP_DIR / "ranking_overlay.png")

    # 1080x1920 전체 투명 캔버스
    img = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. 상단 블랙 헤더 영역 (높이 480px)
    HEADER_HEIGHT = 480
    draw.rectangle([(0, 0), (TARGET_WIDTH, HEADER_HEIGHT)], fill=(0, 0, 0, 255))

    # 폰트 로드 (검은고딕)
    try:
        font_large = ImageFont.truetype(font_path, 88)
        font_medium = ImageFont.truetype(font_path, 98)
        font_sub = ImageFont.truetype(font_path, 48)
    except Exception:
        font_large = font_medium = font_sub = ImageFont.load_default()

    # --- 1줄 (핑크 포인트 컬러: #FF66B2) ---
    bbox1 = draw.textbbox((0, 0), line1_text, font=font_large)
    w1 = bbox1[2] - bbox1[0]
    x1 = (TARGET_WIDTH - w1) // 2
    y1 = 80
    draw.text((x1, y1), line1_text, font=font_large, fill=(255, 102, 178, 255))

    # --- 2줄 (화이트 초굵은 컬러) ---
    bbox2 = draw.textbbox((0, 0), line2_text, font=font_medium)
    w2 = bbox2[2] - bbox2[0]
    x2 = (TARGET_WIDTH - w2) // 2
    y2 = 205
    draw.text((x2, y2), line2_text, font=font_medium, fill=(255, 255, 255, 255))

    # --- 3줄 (서브 텍스트 / 괄호 질문) ---
    if sub_text:
        bbox3 = draw.textbbox((0, 0), sub_text, font=font_sub)
        w3 = bbox3[2] - bbox3[0]
        x3 = (TARGET_WIDTH - w3) // 2
        y3 = 345
        draw.text((x3, y3), sub_text, font=font_sub, fill=(255, 255, 255, 240))

    img.save(output_path, "PNG")
    return output_path

def create_bottom_caption(
    caption_text: str,
    base_img_path: str,
    font_path: str = DEFAULT_FONT_PATH,
    y_pos: int = 1420
) -> str:
    """
    영상 중하단에 블랙 반투명 박스 자막을 추가합니다.
    """
    img = Image.open(base_img_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, 48)
    except Exception:
        font = ImageFont.load_default()

    if caption_text:
        bbox = draw.textbbox((0, 0), caption_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        pad_x = 30
        pad_y = 18
        box_x1 = max(40, (TARGET_WIDTH - text_w) // 2 - pad_x)
        box_x2 = min(TARGET_WIDTH - 40, (TARGET_WIDTH + text_w) // 2 + pad_x)
        box_y1 = y_pos - pad_y
        box_y2 = y_pos + text_h + pad_y

        # 블랙 박스
        draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], fill=(0, 0, 0, 230))
        
        text_x = (TARGET_WIDTH - text_w) // 2
        draw.text((text_x, y_pos), caption_text, font=font, fill=(255, 255, 255, 255))

    img.save(base_img_path, "PNG")
    return base_img_path

if __name__ == "__main__":
    out = create_top_ranking_header()
    create_bottom_caption("야@무지게 물어버리네;; ㅋㅋㅋ", out)
    print("쇼츠 랭킹 스타일 오버레이 생성 완료:", out)
