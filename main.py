from fastapi import FastAPI
from starlette.responses import StreamingResponse
from promptpay import qrcode
import io
from PIL import Image, ImageDraw, ImageFont

app = FastAPI(
    title="PromptPay QR Code Generator API",
    description="API สำหรับสร้างรูปภาพ QR Code ของ PromptPay แบบไดนามิก",
    version="1.3.0",
)

@app.get(
    "/{id_or_phone_number}",
    tags=["PromptPay QR Code Generator"],
    summary="สร้าง QR Code แบบไม่มีจำนวนเงิน",
    description="สร้างรูปภาพ QR Code สำหรับ PromptPay จากเบอร์โทรศัพท์หรือเลขบัตรประชาชน/เลขผู้เสียภาษี",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "ส่งคืนรูปภาพ QR Code ที่สร้างสำเร็จ",
        }
    },
)
def generate_qr_code_without_amount(id_or_phone_number: str):
    payload = qrcode.generate_payload(id_or_phone_number)
    img = qrcode.to_image(payload).resize((1300, 1300), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    border_width = 10
    draw.rectangle(
        [0, 0, img.width, img.height],
        outline="#003d6a",
        width=border_width
    )
    buffer = io.BytesIO()
    img.save(buffer, "PNG", quality=100)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")

@app.get(
    "/{id_or_phone_number}/{amount}",
    tags=["PromptPay QR Code Generator"],
    summary="สร้าง QR Code แบบมีจำนวนเงิน (พร้อมข้อความบนภาพ)",
    description="สร้างรูปภาพ QR Code สำหรับ PromptPay พร้อมจำนวนเงินที่ระบุ โดยจะแสดงจำนวนเงินซ้อนทับอยู่บนภาพ QR Code ด้วย",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "ส่งคืนรูปภาพ QR Code ที่สร้างสำเร็จพร้อมข้อความจำนวนเงิน",
        }
    },
)
def generate_qr_code_with_amount(id_or_phone_number: str, amount: float):
    payload = qrcode.generate_payload(id_or_phone_number, amount)
    img = qrcode.to_image(payload).resize((1300, 1300), Image.LANCZOS).convert("RGB")
    draw = ImageDraw.Draw(img)
    border_width = 10
    draw.rectangle(
        [0, 0, img.width, img.height],
        outline="#003d6a",
        width=border_width
    )
    font_size_ratio = 20
    font_name = "IBMPlexSansThai-Regular.ttf"
    currency_text = "บาท"
    text = f"{amount:,.2f} {currency_text}"
    font_size = int(img.height / font_size_ratio)
    
    try:
        font = ImageFont.truetype(font_name, size=font_size)
    except IOError:
        print(f"Warning: '{font_name}' not found. Using default font.")
        font = ImageFont.load_default()
    
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    center_x = img.width / 2
    center_y = img.height / 2
    bg_padding = 10
    bg_left = center_x - (text_width / 2) - bg_padding
    bg_top = center_y - (text_height / 2) - bg_padding
    bg_right = center_x + (text_width / 2) + bg_padding
    bg_bottom = center_y + (text_height / 2) + bg_padding
    background_box = [(bg_left, bg_top), (bg_right, bg_bottom)]
    draw.rectangle(background_box, fill="white", outline="black", width=2)
    
    try:
        draw.text(
            (center_x, center_y + 2),
            text,
            font=font,
            fill="black",
            anchor="mm"
        )
    except TypeError:
        print("Warning: Pillow version might be too old for 'anchor' support. Text may not be perfectly centered.")
        position = ((img.width - text_width) / 2, (img.height - text_height) / 2)
        draw.text(position, text, font=font, fill="black")
    
    buffer = io.BytesIO()
    img.save(buffer, "PNG", quality=100)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")
