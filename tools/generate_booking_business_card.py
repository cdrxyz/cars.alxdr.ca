#!/usr/bin/env python3
"""Generate the booking QR business card sheet."""

from pathlib import Path

import qrcode
from PIL import Image, ImageEnhance
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "design/business-cards/business-card-light-vehicle-booking-qr.pdf"
LOGO_PATH = ROOT / "design/logo/icon.png"
VEHICLE_PATH = ROOT / "design/business-cards/wagoneer-cutout.png"

BOOKING_URL = "https://cars.alxdr.ca/#contact"

INCH = 72
PAGE_W, PAGE_H = letter
CARD_W = 3.5 * INCH
CARD_H = 2 * INCH
LEFT_MARGIN = 0.75 * INCH
TOP_MARGIN = 0.5 * INCH

GOLD = (200, 164, 86)
DARK = (17, 17, 17)
MUTED = (82, 82, 82)
HAIRLINE = (224, 218, 204)

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_HEADING = "Helvetica-Bold"


def register_fonts():
    global FONT_REGULAR, FONT_BOLD, FONT_HEADING

    regular_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    ]
    bold_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
    ]
    heading_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"),
        Path("/Library/Fonts/Arial Narrow Bold.ttf"),
    ]

    regular = next((path for path in regular_candidates if path.exists()), None)
    bold = next((path for path in bold_candidates if path.exists()), None)
    heading = next((path for path in heading_candidates if path.exists()), None)
    if not regular or not bold:
        return

    pdfmetrics.registerFont(TTFont("CardRegular", str(regular)))
    pdfmetrics.registerFont(TTFont("CardBold", str(bold)))
    FONT_REGULAR = "CardRegular"
    FONT_BOLD = "CardBold"
    if heading:
        pdfmetrics.registerFont(TTFont("CardHeading", str(heading)))
        FONT_HEADING = "CardHeading"


def rgb(color):
    return tuple(channel / 255 for channel in color)


def make_qr() -> ImageReader:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=14,
        border=2,
    )
    qr.add_data(BOOKING_URL)
    qr.make(fit=True)
    image = qr.make_image(fill_color=DARK, back_color="white").convert("RGB")
    return ImageReader(image)


def make_watermark() -> ImageReader:
    image = Image.open(LOGO_PATH).convert("RGBA")
    image = ImageEnhance.Brightness(image).enhance(1.25)
    alpha = image.getchannel("A").point(lambda value: int(value * 0.08))
    image.putalpha(alpha)
    return ImageReader(image)


def load_image(path: Path) -> ImageReader:
    return ImageReader(Image.open(path).convert("RGBA"))


def draw_text(card, x, y, text, font=None, size=6, color=DARK):
    font = font or FONT_REGULAR
    card.setFillColorRGB(*rgb(color))
    card.setFont(font, size)
    card.drawString(x, y, text)


def draw_centered_text(card, x, y, width, text, font=None, size=6, color=DARK):
    font = font or FONT_REGULAR
    card.setFillColorRGB(*rgb(color))
    card.setFont(font, size)
    text_width = card.stringWidth(text, font, size)
    card.drawString(x + (width - text_width) / 2, y, text)


def draw_card(card, x, y, logo, watermark, vehicle, qr_image):
    card.saveState()
    card.translate(x, y)

    clip = card.beginPath()
    clip.rect(0, 0, CARD_W, CARD_H)
    card.clipPath(clip, stroke=0, fill=0)

    card.setFillColorRGB(1, 1, 1)
    card.rect(0, 0, CARD_W, CARD_H, stroke=0, fill=1)

    card.setStrokeColorRGB(*rgb(HAIRLINE))
    card.setLineWidth(0.45)
    card.rect(0.5, 0.5, CARD_W - 1, CARD_H - 1, stroke=1, fill=0)

    card.drawImage(watermark, -23, 23, width=116, height=116, mask="auto")

    card.drawImage(logo, 13, 99, width=34, height=34, mask="auto")
    draw_text(card, 51, 115, "ALEXANDER", FONT_HEADING, 26, DARK)
    draw_text(card, 53, 104, "CAR SERVICE", FONT_BOLD, 9, GOLD)
    draw_text(card, 53, 93, "Private passenger transportation", FONT_REGULAR, 6.8, MUTED)

    card.drawImage(vehicle, 108, 1, width=140, height=81, mask="auto")

    qr_size = 49
    qr_x = CARD_W - qr_size - 14
    qr_y = CARD_H - qr_size - 12
    card.setStrokeColorRGB(*rgb(GOLD))
    card.setLineWidth(0.6)
    card.roundRect(qr_x - 3, qr_y - 3, qr_size + 6, qr_size + 6, 3, stroke=1, fill=0)
    card.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
    card.setFillColorRGB(1, 1, 1)
    card.roundRect(qr_x - 3, qr_y - 13, qr_size + 6, 9, 2, stroke=0, fill=1)
    draw_centered_text(card, qr_x - 2, qr_y - 10, qr_size + 4, "SCAN TO BOOK", FONT_BOLD, 5.6, DARK)

    draw_text(card, 14, 75, "Nabil Alexander", FONT_BOLD, 12.2, DARK)
    draw_text(card, 14, 63, "Owner & Chauffeur", FONT_REGULAR, 7.2, GOLD)

    card.setStrokeColorRGB(*rgb(GOLD))
    card.setLineWidth(0.6)
    card.line(14, 56, 105, 56)

    draw_text(card, 14, 45, "(519) 577-8582", FONT_REGULAR, 7.2, DARK)
    draw_text(card, 14, 34, "cars@alxdr.ca", FONT_REGULAR, 7.2, DARK)
    draw_text(card, 14, 23, "cars.alxdr.ca", FONT_REGULAR, 7.2, DARK)
    draw_text(card, 14, 12, "Waterloo, Ontario", FONT_REGULAR, 7.2, DARK)

    card.restoreState()


def build_pdf():
    register_fonts()

    logo = load_image(LOGO_PATH)
    watermark = make_watermark()
    vehicle = load_image(VEHICLE_PATH)
    qr_image = make_qr()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUTPUT), pagesize=letter)
    pdf.setTitle("Alexander Car Service Booking Business Card")
    pdf.setAuthor("Alexander Car Service")

    for row in range(5):
        y = PAGE_H - TOP_MARGIN - CARD_H - (row * CARD_H)
        for col in range(2):
            x = LEFT_MARGIN + (col * CARD_W)
            draw_card(pdf, x, y, logo, watermark, vehicle, qr_image)

    pdf.showPage()
    pdf.save()


if __name__ == "__main__":
    build_pdf()
