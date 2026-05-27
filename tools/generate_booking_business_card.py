#!/usr/bin/env python3
"""Generate booking QR business card sheets."""

from pathlib import Path

import qrcode
from PIL import Image, ImageEnhance
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
BUSINESS_CARDS_DIR = ROOT / "design/business-cards"
LOGO_PATH = ROOT / "design/logo/icon.png"
VEHICLE_PATH = BUSINESS_CARDS_DIR / "wagoneer-cutout.png"

BOOKING_URL = "https://cars.alxdr.ca/#contact"
QR_LABEL = "Book Now"

INCH = 72
PAGE_W, PAGE_H = letter
CARD_W = 3.5 * INCH
CARD_H = 2 * INCH
LEFT_MARGIN = 0.75 * INCH
TOP_MARGIN = 0.5 * INCH

GOLD = (200, 164, 86)
DARK = (17, 17, 17)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
MUTED = (82, 82, 82)
LIGHT_MUTED = (210, 210, 210)
HAIRLINE = (224, 218, 204)

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_HEADING = "Helvetica-Bold"


THEMES = {
    "light": {
        "bg": WHITE,
        "text": DARK,
        "muted": MUTED,
        "rule": GOLD,
        "qr_label": DARK,
        "edge": HAIRLINE,
    },
    "dark": {
        "bg": (7, 7, 7),
        "text": WHITE,
        "muted": LIGHT_MUTED,
        "rule": GOLD,
        "qr_label": DARK,
        "edge": (36, 36, 36),
    },
}


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


def load_image(path: Path) -> ImageReader:
    return ImageReader(Image.open(path).convert("RGBA"))


def make_qr() -> ImageReader:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=14,
        border=2,
    )
    qr.add_data(BOOKING_URL)
    qr.make(fit=True)
    image = qr.make_image(fill_color=BLACK, back_color=WHITE).convert("RGB")
    return ImageReader(image)


def make_watermark() -> ImageReader:
    image = Image.open(LOGO_PATH).convert("RGBA")
    image = ImageEnhance.Brightness(image).enhance(1.25)
    alpha = image.getchannel("A").point(lambda value: int(value * 0.08))
    image.putalpha(alpha)
    return ImageReader(image)


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


def clip_to_card(card):
    clip = card.beginPath()
    clip.rect(0, 0, CARD_W, CARD_H)
    card.clipPath(clip, stroke=0, fill=0)


def fill_card(card, theme, bordered=False):
    card.setFillColorRGB(*rgb(theme["bg"]))
    card.rect(0, 0, CARD_W, CARD_H, stroke=0, fill=1)

    card.setStrokeColorRGB(*rgb(theme["edge"]))
    card.setLineWidth(0.45)
    card.rect(0.5, 0.5, CARD_W - 1, CARD_H - 1, stroke=1, fill=0)

    if bordered:
        card.setStrokeColorRGB(*rgb(GOLD))
        card.setLineWidth(0.8)
        card.line(0, CARD_H - 1.2, CARD_W, CARD_H - 1.2)
        card.line(0, 1.2, CARD_W, 1.2)


def draw_qr_block(card, qr_image, x, y, size, label_size=6.2):
    card.setFillColorRGB(1, 1, 1)
    card.roundRect(x - 4, y - 14, size + 8, size + 18, 3, stroke=0, fill=1)
    card.setStrokeColorRGB(*rgb(GOLD))
    card.setLineWidth(0.65)
    card.roundRect(x - 4, y - 4, size + 8, size + 8, 3, stroke=1, fill=0)
    card.drawImage(qr_image, x, y, width=size, height=size)
    draw_centered_text(card, x - 4, y - 11, size + 8, QR_LABEL, FONT_BOLD, label_size, DARK)


def draw_standard_card(card, x, y, theme_name, logo, qr_image):
    theme = THEMES[theme_name]

    card.saveState()
    card.translate(x, y)
    clip_to_card(card)
    fill_card(card, theme, bordered=True)

    card.drawImage(logo, 20, 91, width=38, height=38, mask="auto")
    draw_text(card, 66, 108, "ALEXANDER", FONT_HEADING, 22, theme["text"])
    draw_text(card, 68, 96, "CAR SERVICE", FONT_BOLD, 8.5, GOLD)

    card.setStrokeColorRGB(*rgb(GOLD))
    card.setLineWidth(0.6)
    card.line(20, 86, 170, 86)

    draw_qr_block(card, qr_image, 187, 80, 43, label_size=5.8)

    draw_text(card, 20, 58, "Nabil Alexander", FONT_BOLD, 11, theme["text"])
    draw_text(card, 20, 47, "Owner & Chauffeur", FONT_REGULAR, 7, GOLD)
    draw_text(card, 20, 29, "(519) 577-8582 | cars@alxdr.ca", FONT_REGULAR, 6.6, theme["text"])
    draw_text(card, 20, 18, "Waterloo, Ontario | cars.alxdr.ca", FONT_REGULAR, 6.6, theme["text"])

    card.restoreState()


def draw_vehicle_card(card, x, y, theme_name, logo, vehicle, qr_image):
    theme = THEMES[theme_name]

    card.saveState()
    card.translate(x, y)
    clip_to_card(card)
    fill_card(card, theme)

    card.drawImage(logo, 13, 99, width=34, height=34, mask="auto")
    draw_text(card, 54, 116, "ALEXANDER", FONT_HEADING, 20, theme["text"])
    draw_text(card, 56, 105, "CAR SERVICE", FONT_BOLD, 7.8, GOLD)
    draw_text(card, 56, 95, "Passenger Transportation", FONT_REGULAR, 6.4, theme["muted"])

    card.drawImage(vehicle, 107, 1, width=141, height=82, mask="auto")
    draw_qr_block(card, qr_image, 196, 88, 39, label_size=5.2)

    draw_text(card, 14, 73, "Nabil Alexander", FONT_BOLD, 10.8, theme["text"])
    draw_text(card, 14, 63, "Owner & Chauffeur", FONT_REGULAR, 6.4, GOLD)

    card.setStrokeColorRGB(*rgb(GOLD))
    card.setLineWidth(0.55)
    card.line(14, 56, 104, 56)

    draw_text(card, 14, 45, "(519) 577-8582", FONT_REGULAR, 6.6, theme["text"])
    draw_text(card, 14, 35, "cars@alxdr.ca", FONT_REGULAR, 6.6, theme["text"])
    draw_text(card, 14, 25, "Waterloo, Ontario", FONT_REGULAR, 6.6, theme["text"])
    draw_text(card, 14, 15, "cars.alxdr.ca", FONT_REGULAR, 6.6, theme["text"])

    card.restoreState()


def draw_large_booking_card(card, x, y, logo, watermark, vehicle, qr_image):
    theme = THEMES["light"]

    card.saveState()
    card.translate(x, y)
    clip_to_card(card)
    fill_card(card, theme)

    card.drawImage(watermark, -23, 23, width=116, height=116, mask="auto")

    card.drawImage(logo, 13, 99, width=34, height=34, mask="auto")
    draw_text(card, 51, 115, "ALEXANDER", FONT_HEADING, 26, DARK)
    draw_text(card, 53, 104, "CAR SERVICE", FONT_BOLD, 9, GOLD)
    draw_text(card, 53, 93, "Private passenger transportation", FONT_REGULAR, 6.8, MUTED)

    card.drawImage(vehicle, 108, 1, width=140, height=81, mask="auto")
    draw_qr_block(card, qr_image, CARD_W - 63, CARD_H - 61, 49, label_size=7.2)

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


def draw_sheet(output, draw_one):
    BUSINESS_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output), pagesize=letter)
    pdf.setTitle("Alexander Car Service Booking QR Business Card")
    pdf.setAuthor("Alexander Car Service")

    for row in range(5):
        y = PAGE_H - TOP_MARGIN - CARD_H - (row * CARD_H)
        for col in range(2):
            x = LEFT_MARGIN + (col * CARD_W)
            draw_one(pdf, x, y)

    pdf.showPage()
    pdf.save()


def build_pdf():
    register_fonts()

    logo = load_image(LOGO_PATH)
    watermark = make_watermark()
    vehicle = load_image(VEHICLE_PATH)
    qr_image = make_qr()

    outputs = [
        (
            BUSINESS_CARDS_DIR / "business-card-light-qr.pdf",
            lambda pdf, x, y: draw_standard_card(pdf, x, y, "light", logo, qr_image),
        ),
        (
            BUSINESS_CARDS_DIR / "business-card-dark-qr.pdf",
            lambda pdf, x, y: draw_standard_card(pdf, x, y, "dark", logo, qr_image),
        ),
        (
            BUSINESS_CARDS_DIR / "business-card-light-vehicle-qr.pdf",
            lambda pdf, x, y: draw_vehicle_card(pdf, x, y, "light", logo, vehicle, qr_image),
        ),
        (
            BUSINESS_CARDS_DIR / "business-card-dark-vehicle-qr.pdf",
            lambda pdf, x, y: draw_vehicle_card(pdf, x, y, "dark", logo, vehicle, qr_image),
        ),
        (
            BUSINESS_CARDS_DIR / "business-card-light-vehicle-booking-qr.pdf",
            lambda pdf, x, y: draw_large_booking_card(pdf, x, y, logo, watermark, vehicle, qr_image),
        ),
    ]

    for output, draw_one in outputs:
        draw_sheet(output, draw_one)


if __name__ == "__main__":
    build_pdf()
