import os
from PIL import Image, ImageDraw, ImageFont
from config import TARGET_WIDTH, TARGET_HEIGHT, DEFAULT_FONT_PATH, TEMP_DIR

def create_text_overlay(
    top_title: str,
    bottom_text: str = "",
    font_path: str = DEFAULT_FONT_PATH,
    output_path: str = None
) -> str:
    """
    1080x1920 투명 캔버스에 릴스 상단 후킹 타이틀 및 하단 서브 텍스트를 감각적으로 렌더링합니다.
    """
    if output_path is None:
        output_path = str(TEMP_DIR / "overlay.png")

    # 투명 캔버스 생성 (RGBA)
    img = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 폰트 로드
    title_font_size = 56
    sub_font_size = 38
    try:
        title_font = ImageFont.truetype(font_path, title_font_size)
        sub_font = ImageFont.truetype(font_path, sub_font_size)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    # --- 상단 타이틀 렌더링 ---
    if top_title:
        # 긴 제목 줄바꿈 처리
        lines = []
        words = top_title.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=title_font)
            line_width = bbox[2] - bbox[0]
            if line_width <= (TARGET_WIDTH - 160): # 양옆 마진 80px
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # 박스 크기 계산
        line_height = title_font_size + 16
        total_text_height = len(lines) * line_height
        box_padding_x = 40
        box_padding_y = 30
        
        # 시작 Y좌표 (상단 180px 위치)
        start_y = 180
        box_top = start_y - box_padding_y
        box_bottom = start_y + total_text_height + box_padding_y

        # 각 줄의 최대 너비
        max_w = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            w = bbox[2] - bbox[0]
            if w > max_w:
                max_w = w

        box_left = max(40, (TARGET_WIDTH - max_w) // 2 - box_padding_x)
        box_right = min(TARGET_WIDTH - 40, (TARGET_WIDTH + max_w) // 2 + box_padding_x)

        # 상단 타이틀 배경 박스 (반투명 블랙 둥근 사각형)
        draw.rounded_rectangle(
            [(box_left, box_top), (box_right, box_bottom)],
            radius=20,
            fill=(0, 0, 0, 200),
            outline=(255, 230, 0, 255), # 포인트 옐로우 테두리
            width=4
        )

        # 텍스트 그리기 (중앙 정렬)
        curr_y = start_y
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            line_w = bbox[2] - bbox[0]
            text_x = (TARGET_WIDTH - line_w) // 2
            
            # 텍스트 아웃라인/그림자 효과
            for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                draw.text((text_x + ox, curr_y + oy), line, font=title_font, fill=(0, 0, 0, 255))
            draw.text((text_x, curr_y), line, font=title_font, fill=(255, 255, 255, 255))
            curr_y += line_height

    # --- 하단 서브 텍스트 렌더링 ---
    if bottom_text:
        bbox = draw.textbbox((0, 0), bottom_text, font=sub_font)
        sub_w = bbox[2] - bbox[0]
        sub_h = bbox[3] - bbox[1]
        sub_y = 1680 # 하단 안전 영역 위쪽

        sub_box_left = max(60, (TARGET_WIDTH - sub_w) // 2 - 25)
        sub_box_right = min(TARGET_WIDTH - 60, (TARGET_WIDTH + sub_w) // 2 + 25)
        sub_box_top = sub_y - 15
        sub_box_bottom = sub_y + sub_h + 15

        draw.rounded_rectangle(
            [(sub_box_left, sub_box_top), (sub_box_right, sub_box_bottom)],
            radius=15,
            fill=(0, 0, 0, 180)
        )
        sub_x = (TARGET_WIDTH - sub_w) // 2
        draw.text((sub_x, sub_y), bottom_text, font=sub_font, fill=(255, 230, 0, 255)) # 옐로우 강조 텍스트

    img.save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    out = create_text_overlay(
        top_title="외국에서 난리 난 강아지 반응 ㅋㅋㅋ",
        bottom_text="끝까지 보면 소름 돋음 🤣"
    )
    print("오버레이 생성 완료:", out)
