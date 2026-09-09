import os
from PIL import Image, ImageDraw, ImageFont
from config import TARGET_WIDTH, TARGET_HEIGHT, DEFAULT_FONT_PATH, TEMP_DIR

def create_top_ranking_header(
    line1_text: str = "역대급 해외 바이럴",
    line2_text: str = "웃긴 모먼트 랭킹 TOP6",
    sub_text: str = "(다들 몇 번이 제일 웃김? ㅋㅋㅋ)",
    font_path: str = DEFAULT_FONT_PATH,
    output_path: str = None
) -> str:
    """
    유튜브 쇼츠 / 틱톡 대세 랭킹 채널 스타일의 상단 고정 헤더 배너:
    - 두꺼운 고딕 폰트(BlackHanSans)
    - 흰색 굵은 글씨 + 두꺼운 검은색 외곽선 테두리 (시인성 극대화)
    - 상단 인스타 Safe Zone (높이 380px) 블랙 바
    """
    if output_path is None:
        output_path = str(TEMP_DIR / "ranking_overlay.png")

    img = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. 상단 블랙 헤더 영역 (높이 360px)
    HEADER_HEIGHT = 360
    draw.rectangle([(0, 0), (TARGET_WIDTH, HEADER_HEIGHT)], fill=(0, 0, 0, 255))

    # 폰트 로드 (검은고딕)
    try:
        font_title = ImageFont.truetype(font_path, 80)
        font_sub = ImageFont.truetype(font_path, 40)
    except Exception:
        font_title = font_sub = ImageFont.load_default()

    # 상단 메인 타이틀 구성
    full_title = f"{line1_text} {line2_text}".strip()
    # 글자가 너무 길면 2줄로 나누어 배치
    if len(full_title) > 18 or (line1_text and line2_text and len(line2_text) >= 6):
        # 1줄
        bbox1 = draw.textbbox((0, 0), line1_text, font=font_title)
        w1 = bbox1[2] - bbox1[0]
        x1 = (TARGET_WIDTH - w1) // 2
        y1 = 65
        draw.text((x1, y1), line1_text, font=font_title, fill=(255, 255, 255, 255),
                  stroke_width=7, stroke_fill=(0, 0, 0, 255))

        # 2줄 (포인트 컬러 살짝 주거나 화이트 볼드)
        bbox2 = draw.textbbox((0, 0), line2_text, font=font_title)
        w2 = bbox2[2] - bbox2[0]
        x2 = (TARGET_WIDTH - w2) // 2
        y2 = 165
        # 랭킹이나 TOP 키워드는 옐로우 하이라이트로 시선 강탈
        t2_color = (255, 235, 59, 255) if "TOP" in line2_text.upper() or "랭킹" in line2_text else (255, 255, 255, 255)
        draw.text((x2, y2), line2_text, font=font_title, fill=t2_color,
                  stroke_width=7, stroke_fill=(0, 0, 0, 255))

        # 서브 텍스트
        if sub_text:
            bbox3 = draw.textbbox((0, 0), sub_text, font=font_sub)
            w3 = bbox3[2] - bbox3[0]
            x3 = (TARGET_WIDTH - w3) // 2
            y3 = 275
            draw.text((x3, y3), sub_text, font=font_sub, fill=(230, 230, 230, 240),
                      stroke_width=3, stroke_fill=(0, 0, 0, 255))
    else:
        # 1줄 집중 타이틀
        bbox = draw.textbbox((0, 0), full_title, font=font_title)
        w = bbox[2] - bbox[0]
        x = (TARGET_WIDTH - w) // 2
        y = 120
        draw.text((x, y), full_title, font=font_title, fill=(255, 255, 255, 255),
                  stroke_width=8, stroke_fill=(0, 0, 0, 255))

        if sub_text:
            bbox3 = draw.textbbox((0, 0), sub_text, font=font_sub)
            w3 = bbox3[2] - bbox3[0]
            x3 = (TARGET_WIDTH - w3) // 2
            y3 = 240
            draw.text((x3, y3), sub_text, font=font_sub, fill=(230, 230, 230, 240),
                      stroke_width=3, stroke_fill=(0, 0, 0, 255))

    img.save(output_path, "PNG")
    return output_path

def create_caption_overlay(
    caption_text: str,
    output_path: str,
    font_path: str = DEFAULT_FONT_PATH,
    y_pos: int = 1080
) -> str:
    """
    유튜브 쇼츠 대세 예능 밈 스타일 중앙 집중 자막 오버레이:
    - 위치: 화면 중앙부 (Y: 1080 부근) - 시선이 바로 꽂히는 위치!
    - 폰트: 70px 대형 볼드 고딕
    - 텍스트: 흰색/옐로우 굵은 글씨 + 8px 검은색 두꺼운 외곽선 테두리
    - 배경: 둥근 블랙 섀도 박스 (시인성 100% 보장)
    """
    img = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, 70)
    except Exception:
        font = ImageFont.load_default()

    if caption_text:
        bbox = draw.textbbox((0, 0), caption_text, font=font, stroke_width=8)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        pad_x = 42
        pad_y = 20
        box_x1 = max(30, (TARGET_WIDTH - text_w) // 2 - pad_x)
        box_x2 = min(TARGET_WIDTH - 30, (TARGET_WIDTH + text_w) // 2 + pad_x)
        box_y1 = y_pos - pad_y
        box_y2 = y_pos + text_h + pad_y

        # 세련된 라운드 블랙 섀도 박스
        draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=20, fill=(0, 0, 0, 225))
        
        # 텍스트 컬러 (펀치라인/감탄사/웃음 포인트는 쨍한 옐로우 #FFE600)
        is_punchline = any(w in caption_text for w in ["대참사", "ㅋㅋㅋ", "퍽", "뇌정지", "실화", "멈춰", "어이", "눈치", "저기서", "??", "!!"])
        text_color = (255, 230, 0, 255) if is_punchline else (255, 255, 255, 255)

        text_x = (TARGET_WIDTH - text_w) // 2
        draw.text(
            (text_x, y_pos),
            caption_text,
            font=font,
            fill=text_color,
            stroke_width=8,
            stroke_fill=(0, 0, 0, 255)
        )

    img.save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    out = create_top_ranking_header("역대급 정확한 에임", "랭킹 TOP6", "(끝까지 보면 이유 나옴 ㅋㅋㅋ)")
    create_caption_overlay("저기서 저걸 던진다고?? ㅋㅋㅋ", str(TEMP_DIR / "sample_center_cap.png"))
    print("디자인 업데이트 완료!")
