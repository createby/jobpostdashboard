from reportlab.lib.pagesizes import A3
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import qrcode
import io
import os

# 폰트 등록
FONT_PATH = "/Users/diff/Library/Fonts/PretendardVariable.ttf"
pdfmetrics.registerFont(TTFont("Pretendard", FONT_PATH))

W, H = A3  # 841.89 x 1190.55 pt

def hex_color(h):
    return colors.HexColor(h)

def make_qr_image(text):
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(text or "https://")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def wrap_text(c, text, font, size, max_width):
    c.setFont(font, size)
    lines = []
    current = ""
    for char in str(text):
        if c.stringWidth(current + char, font, size) <= max_width:
            current += char
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines

def draw_section_header(c, x, y, w, h, text, bg_color):
    c.setFillColor(bg_color)
    c.roundRect(x, y - h, w * 0.22, h, 3, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Pretendard", 13)
    c.drawString(x + 8, y - h + h/2 - 5, text)

def draw_cell(c, x, y, w, h, text, font, size, color, bg, align="left", padding=6):
    c.setFillColor(bg)
    c.rect(x, y - h, w, h, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont(font, size)
    if align == "center":
        c.drawCentredString(x + w/2, y - h + h/2 - size/2 + 1, str(text))
    else:
        c.drawString(x + padding, y - h + h/2 - size/2 + 1, str(text))

def generate_company_pdf(data, output_path):
    accent = hex_color(data.get("배경색", "#4CAF50"))
    accent_light = hex_color(data.get("배경색연한", "#E8F5E9"))
    c_white = colors.white
    c_dark = hex_color("#222222")
    c_gray = hex_color("#F5F5F5")
    c_border = hex_color("#DDDDDD")
    c_label = hex_color("#555555")

    c = canvas.Canvas(output_path, pagesize=A3)
    margin = 18 * mm
    content_w = W - 2 * margin

    # ── 상단 헤더 ──────────────────────────────
    header_h = 28 * mm
    y = H - 12 * mm

    # QR코드 영역
    qr_size = header_h
    qr_text = data.get("qr_url", data.get("기업명", ""))
    qr_buf = make_qr_image(qr_text)
    c.drawImage(qr_buf, margin, y - qr_size, qr_size, qr_size, preserveAspectRatio=True)

    # 부스번호 박스
    booth_x = margin + qr_size + 4 * mm
    booth_w = 28 * mm
    c.setFillColor(accent)
    c.roundRect(booth_x, y - header_h, booth_w, header_h, 4, fill=1, stroke=0)
    c.setFillColor(c_white)
    c.setFont("Pretendard", 22)
    c.drawCentredString(booth_x + booth_w/2, y - header_h/2 - 8, data.get("부스번호", ""))

    # 기업명
    name_x = booth_x + booth_w + 6 * mm
    c.setFillColor(c_dark)
    c.setFont("Pretendard", 28)
    c.drawString(name_x, y - header_h/2 - 10, data.get("기업명", ""))

    # 면접/상담 태그
    tag_text = data.get("태그", "면접,상담")
    if tag_text:
        tag_w = 22 * mm
        tag_h = 8 * mm
        c.setFillColor(accent)
        c.roundRect(W - margin - tag_w, y - tag_h, tag_w, tag_h, 3, fill=1, stroke=0)
        c.setFillColor(c_white)
        c.setFont("Pretendard", 9)
        c.drawCentredString(W - margin - tag_w/2, y - tag_h + tag_h/2 - 4, tag_text)

    y -= header_h + 5 * mm

    # ── 기업정보 섹션 ──────────────────────────
    sec_h = 9 * mm
    draw_section_header(c, margin, y, content_w, sec_h, "기업정보", accent)
    y -= sec_h + 1 * mm

    row_h = 9 * mm
    half = content_w / 2
    label_w = 22 * mm

    # 구분선
    c.setStrokeColor(c_border)
    c.setLineWidth(0.5)

    for row_data in [
        [("업종", data.get("업종","")), ("사업내용", data.get("사업내용",""))],
        [("회사주소", data.get("회사주소",""))],
    ]:
        if len(row_data) == 2:
            for i, (lbl, val) in enumerate(row_data):
                rx = margin + i * half
                draw_cell(c, rx, y, label_w, row_h, lbl, "Pretendard", 9, c_label, c_gray)
                draw_cell(c, rx + label_w, y, half - label_w, row_h, val, "Pretendard", 9, c_dark, c_white)
                c.rect(rx, y - row_h, half, row_h, fill=0, stroke=1)
        else:
            lbl, val = row_data[0]
            draw_cell(c, margin, y, label_w, row_h, lbl, "Pretendard", 9, c_label, c_gray)
            draw_cell(c, margin + label_w, y, content_w - label_w, row_h, val, "Pretendard", 9, c_dark, c_white)
            c.rect(margin, y - row_h, content_w, row_h, fill=0, stroke=1)
        y -= row_h

    y -= 4 * mm

    # ── 기업 소개 섹션 ──────────────────────────
    draw_section_header(c, margin, y, content_w, sec_h, "기업 소개", accent)
    y -= sec_h + 1 * mm

    intro_lines = wrap_text(c, data.get("기업소개", ""), "Pretendard", 10, content_w - 10)
    line_h = 5.5 * mm
    intro_h = max(len(intro_lines) * line_h + 6 * mm, 20 * mm)

    c.setFillColor(c_white)
    c.setStrokeColor(c_border)
    c.rect(margin, y - intro_h, content_w, intro_h, fill=1, stroke=1)
    c.setFillColor(c_dark)
    c.setFont("Pretendard", 10)
    ty = y - 5 * mm
    for line in intro_lines:
        c.drawString(margin + 5, ty, line)
        ty -= line_h

    y -= intro_h + 5 * mm

    # ── 여기서부터 남은 높이 계산 ──────────────
    remaining_y = y  # 채용계획 시작점
    bottom_margin = 12 * mm
    available_h = remaining_y - bottom_margin  # 채용계획~복리후생이 채울 총 높이

    # 각 섹션 비율 (채용계획 헤더+테이블 / 상세정보 6개 필드)
    hire_rows = data.get("채용계획", [])
    detail_fields = [
        ("담당업무 및 세부요건\n(직무내용)", data.get("담당업무", "")),
        ("급여조건",    data.get("급여조건", "")),
        ("자격요건 우대사항", data.get("자격요건", "")),
        ("근무지역",    data.get("근무지역", "")),
        ("근무시간",    data.get("근무시간", "")),
        ("복리후생",    data.get("복리후생", "")),
    ]

    # 섹션 수: 채용계획(1) + 상세정보 헤더(1) + 필드(6) = 8 블록
    # 채용계획 테이블: 헤더행 + 데이터행
    hire_block_count = 1 + len(hire_rows)  # 테이블 헤더 + 데이터행
    total_blocks = hire_block_count + 1 + len(detail_fields)  # +1 = 채용계획 섹션헤더
    # 섹션 헤더 2개 높이 고정
    fixed_h = sec_h * 2 + 2 * mm * 2
    flex_h = available_h - fixed_h
    unit_h = flex_h / (hire_block_count + len(detail_fields))

    # ── 채용계획 섹션 ──────────────────────────
    draw_section_header(c, margin, y, content_w, sec_h, "채용계획", accent)
    y -= sec_h + 1 * mm

    th_h = unit_h * 0.9
    cols = ["모집직무", "경력구분", "고용형태", "학력", "모집인원"]
    col_ratios = [0.35, 0.15, 0.15, 0.20, 0.15]
    col_widths = [content_w * r for r in col_ratios]

    # 테이블 헤더
    cx = margin
    for col, cw in zip(cols, col_widths):
        draw_cell(c, cx, y, cw, th_h, col, "Pretendard", 10, c_white, accent, "center")
        c.setStrokeColor(c_white)
        c.rect(cx, y - th_h, cw, th_h, fill=0, stroke=1)
        cx += cw
    y -= th_h

    # 데이터 행
    data_row_h = unit_h
    for row in hire_rows:
        cx = margin
        for i, (val, cw) in enumerate(zip(row, col_widths)):
            bg = accent_light if i == 0 else c_white
            draw_cell(c, cx, y, cw, data_row_h, val, "Pretendard", 10, c_dark, bg, "center")
            c.setStrokeColor(c_border)
            c.rect(cx, y - data_row_h, cw, data_row_h, fill=0, stroke=1)
            cx += cw
        y -= data_row_h

    y -= 4 * mm

    # ── 상세정보 섹션 ──────────────────────────
    draw_section_header(c, margin, y, content_w, sec_h, "상세 정보", accent)
    y -= sec_h + 1 * mm

    field_label_w = 30 * mm
    field_h = (y - bottom_margin) / len(detail_fields)

    for label, value in detail_fields:
        # 라벨 셀
        c.setFillColor(c_gray)
        c.rect(margin, y - field_h, field_label_w, field_h, fill=1, stroke=0)
        c.setFillColor(c_white)
        c.rect(margin + field_label_w, y - field_h, content_w - field_label_w, field_h, fill=1, stroke=0)
        c.setStrokeColor(c_border)
        c.rect(margin, y - field_h, content_w, field_h, fill=0, stroke=1)

        # 라벨 텍스트 (줄바꿈 처리)
        c.setFillColor(c_label)
        c.setFont("Pretendard", 9)
        label_lines = label.split("\n")
        lbl_start = y - field_h/2 + (len(label_lines) * 5)/2
        for ll in label_lines:
            c.drawCentredString(margin + field_label_w/2, lbl_start - 5, ll)
            lbl_start -= 5.5

        # 값 텍스트
        val_lines = wrap_text(c, value, "Pretendard", 9, content_w - field_label_w - 10)
        c.setFillColor(c_dark)
        c.setFont("Pretendard", 9)
        max_lines = int(field_h / (4.5 * mm))
        vty = y - 5 * mm
        for vl in val_lines[:max_lines]:
            c.drawString(margin + field_label_w + 6, vty, vl)
            vty -= 4.5 * mm

        y -= field_h

    c.save()
    print(f"생성 완료: {output_path}")


# ── 샘플 실행 ──
if __name__ == "__main__":
    sample_data = {
        "번호": "1",
        "부스번호": "A01",
        "ZONE": "대·중견기업ZONE",
        "기업명": "Adecco Korea",
        "업종": "서비스업",
        "사업내용": "HR컨설팅, 헤드헌팅, 스태핑",
        "회사주소": "서울시 송파구 백제고분로 69",
        "태그": "면접,상담",
        "배경색": "#4CAF50",
        "배경색연한": "#E8F5E9",
        "qr_url": "https://adecco.co.kr",
        "기업소개": (
            "Adecco Group은 스위스 취리히에 본사를 두고 전세계 60개국가에서 HR Solution을 제공하고 있는 포춘 글로벌 500대기업입니다. "
            "Adecco Korea는 서울(본사), 용인, 부산, 대전, 원주에 사무실을 운영하여 헤드헌팅, 스태핑, 아웃소싱 서비스를 450개이상의 기업에 제공하고 있으며 "
            "전체 직원은 2,600명이상입니다. "
            "Adecco Korea의 헤드헌팅은 Engineering, IT & Tech, Consumer & Retail, Finance, Healthcare & Life Science, Corporate 팀으로 구성되어 "
            "연 평균 500건 이상의 헤드헌팅(Executive, Senior & Junior level)과 채용대행(RPO)을 성공시키고 있습니다."
        ),
        "채용계획": [
            ["HR Consultant & Recruiter", "경력(1년이상)", "정규직", "대학교(4년) 졸업", "3명"],
        ],
        "담당업무": (
            "고객사 채용 관리(인재채용, 면접일정 조율), 고객사/근무자 계약관리(신규입사, 연장, 퇴사자), "
            "근무자 근태관리(경비, 타임 시트 취합), 고객사 청구 관련 제반 작업, 노무 이슈 핸들링, "
            "기타 사무행정관리 업무, 신규 거래처 발굴, 파견 및 도급 컨설팅, 고객사 현장관리(KPI, SLA) 및 개인 목표관리(매출/GP)"
        ),
        "자격요건": (
            "HR산업에 대한 관심과 이해가 있으신 분 / 동종업계 경력자(1년 이상) / "
            "노무관련 지식 및 채용유관 경험이 있으신 분 / FSM, 판매판촉 업무 관련 경험 / "
            "물류센터 핸들링 또는 물류센터 운영 관리자 업무 경험 / 비지니스 영어 활용 가능자"
        ),
        "급여조건": "회사 내규",
        "근무지역": "서울",
        "근무시간": "주 5일(월~금) 8시간 (8~10시 출근, 17~19시 퇴근)",
        "복리후생": (
            "연차휴가, 명절 선물, 생일 선물, 생일 휴가, 유급 병가, 휴대폰 지원금, 탄력 근무제(8~10시), "
            "재택근무(주1회), 패밀리 데이(매월 마지막 금요일), 조기 퇴근(명절 전일, 크리스마스, 신정), "
            "분기별 인센티브(해당자), PS, 성과 우수사원 포상, APAC 시상(A+) 해외여행"
        ),
    }
    os.makedirs("output", exist_ok=True)
    generate_company_pdf(sample_data, f"output/{sample_data['부스번호']}_{sample_data['기업명']}.pdf")
