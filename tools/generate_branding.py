#!/usr/bin/env python3
"""
Hospitality TV - Automated Branding & Wallpaper Generator
Turns your Airbnb listing photos into native 1080p Apple TV-style
hero shots and glassmorphic photo collages with host branding.
"""

import os
import sys
import math
import argparse

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("Error: Pillow is required. Run: pip install Pillow")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(PROJECT_DIR, "launcher", "assets")
WALL_OUT_DIR = os.path.join(ASSETS_DIR, "wallpapers")
FONT_DIR = os.path.join(ASSETS_DIR, "fonts")

FONT_OVERLINE_PATH = os.path.join(FONT_DIR, "Montserrat-SemiBold.ttf")
FONT_TITLE_PATH    = os.path.join(FONT_DIR, "Montserrat-SemiBold.ttf")
FONT_SUB_PATH      = os.path.join(FONT_DIR, "Montserrat-Medium.ttf")

GOLD_ACCENT = (226, 196, 140)
WHITE       = (255, 255, 255)
SUB_COLOR   = (215, 220, 230)

def crop_cover(img, target_w=1920, target_h=1080):
    bw, bh = img.size
    scale = max(target_w / bw, target_h / bh)
    nw, nh = int(bw * scale), int(bh * scale)
    img_resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - target_w) // 2
    top = (nh - target_h) // 2
    return img_resized.crop((left, top, left + target_w, top + target_h))

def generate_vignette_mask():
    sw, sh = 192, 108
    small_mask = Image.new("L", (sw, sh), 0)
    pix = small_mask.load()
    for y in range(sh):
        py = y * 10
        top_a = 130.0 * max(0.0, 1.0 - py / 360.0)**1.5
        bot_a = 165.0 * max(0.0, (py - 700.0) / 380.0)**1.4
        for x in range(sw):
            px = x * 10
            dist = math.hypot(px, py)
            tl_a = 70.0 * max(0.0, 1.0 - dist / 880.0)
            val = int(min(225, max(top_a + tl_a, bot_a)))
            pix[x, y] = val
    return small_mask.resize((1920, 1080), Image.Resampling.BICUBIC)

VIGNETTE_MASK = generate_vignette_mask()

def add_ui_gradients(img):
    dark_overlay = Image.new("RGBA", (1920, 1080), (8, 10, 14, 255))
    composed = img.convert("RGBA")
    composed.paste(dark_overlay, (0, 0), VIGNETTE_MASK)
    return composed

def prepare_card(img_path, target_w, target_h, radius=18):
    im = Image.open(img_path).convert("RGB")
    iw, ih = im.size
    scale = max(target_w / iw, target_h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - target_w) // 2
    top = (nh - target_h) // 2
    im = im.crop((left, top, left + target_w, top + target_h)).convert("RGBA")
    
    mask = Image.new("L", (target_w, target_h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (target_w, target_h)], radius=radius, fill=255)
    
    bordered = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    bordered.paste(im, (0, 0), mask)
    b_draw = ImageDraw.Draw(bordered)
    b_draw.rounded_rectangle([(0, 0), (target_w-1, target_h-1)], radius=radius, outline=(255, 255, 255, 60), width=2)
    return bordered

def draw_branding_badge(img, overline, title, subtitle, logo_img=None, x1=1110, y1=250, w=740, h=205):
    x2 = x1 + w
    y2 = y1 + h
    card_overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_overlay)
    card_draw.rounded_rectangle([x1, y1, x2, y2], radius=22, fill=(12, 14, 20, 175), outline=(255, 255, 255, 45), width=1)
    
    if logo_img:
        div_x = x1 + 525
        card_draw.line([(div_x, y1 + 26), (div_x, y2 - 26)], fill=(255, 255, 255, 35), width=1)
        lw, lh = logo_img.size
        logo_x = div_x + ((w - 525) - lw) // 2
        logo_y = y1 + (h - lh) // 2
        card_overlay.paste(logo_img, (logo_x, logo_y), logo_img)
    
    composed = Image.alpha_composite(img.convert("RGBA"), card_overlay)
    draw = ImageDraw.Draw(composed)
    
    font_over  = ImageFont.truetype(FONT_OVERLINE_PATH, 14)
    font_title = ImageFont.truetype(FONT_TITLE_PATH, 38)
    
    max_sub_w = 450 if logo_img else (w - 70)
    sub_size = 16
    while sub_size > 11:
        f_test = ImageFont.truetype(FONT_SUB_PATH, sub_size)
        bbox = draw.textbbox((0, 0), subtitle, font=f_test)
        if bbox[2] - bbox[0] <= max_sub_w:
            break
        sub_size -= 1
    font_sub = ImageFont.truetype(FONT_SUB_PATH, sub_size)
    
    draw.text((x1 + 34, y1 + 28), overline, font=font_over, fill=(*GOLD_ACCENT, 240))
    draw.text((x1 + 34, y1 + 56), title, font=font_title, fill=(*WHITE, 255))
    draw.line([(x1 + 34, y1 + 118), (x1 + 190, y1 + 118)], fill=(*GOLD_ACCENT, 200), width=2)
    draw.text((x1 + 34, y1 + 134), subtitle, font=font_sub, fill=(*SUB_COLOR, 230))
    return composed

def make_single_hero(src_path, overline, title, subtitle, logo=None):
    base = Image.open(src_path).convert("RGB")
    cropped = crop_cover(base)
    with_vignette = add_ui_gradients(cropped)
    return draw_branding_badge(with_vignette, overline, title, subtitle, logo)

def make_triptych_collage(bg_src_path, card1_path, card2_path, card3_path, overline, title, subtitle, logo=None):
    bg = Image.open(bg_src_path).convert("RGB")
    bg = crop_cover(bg).filter(ImageFilter.GaussianBlur(35))
    dark = Image.new("RGBA", (1920, 1080), (10, 12, 18, 195))
    canvas = Image.alpha_composite(bg.convert("RGBA"), dark)
    canvas = add_ui_gradients(canvas)
    
    c1 = prepare_card(card1_path, 520, 400)
    c2 = prepare_card(card2_path, 460, 400)
    c3 = prepare_card(card3_path, 740, 225)
    
    canvas.paste(c1, (80, 295), c1)
    canvas.paste(c2, (625, 295), c2)
    canvas.paste(c3, (1110, 470), c3)
    return draw_branding_badge(canvas, overline, title, subtitle, logo)

def main():
    parser = argparse.ArgumentParser(description="Generate 1080p Luxury Hospitality TV Wallpapers")
    parser.add_argument("--photos-dir", required=True, help="Directory containing your property photos (JPG/PNG)")
    parser.add_argument("--logo", default=None, help="Path to your host logo (transparent PNG)")
    parser.add_argument("--property", default="LUXURY VILLA", help="Property / stay name (e.g. VILLA AZURE)")
    parser.add_argument("--subtitle", default="Private Heated Pool · Ocean Sunset · 4 Suites", help="Amenities subtitle")
    parser.add_argument("--overline", default="EXPLORE OUR STAYS", help="Overline text")
    parser.add_argument("--output-dir", default=WALL_OUT_DIR, help="Destination directory for wallpapers")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load and scale logo
    logo_img = None
    if args.logo and os.path.exists(args.logo):
        logo_raw = Image.open(args.logo).convert("RGBA")
        bbox = logo_raw.getbbox()
        if bbox:
            logo_raw = logo_raw.crop(bbox)
        lh = 115
        lw = int(lh * (logo_raw.width / logo_raw.height))
        logo_img = logo_raw.resize((lw, lh), Image.Resampling.LANCZOS)

    # Gather images
    valid_exts = (".jpg", ".jpeg", ".png")
    photos = [
        os.path.join(args.photos_dir, f) for f in sorted(os.listdir(args.photos_dir))
        if f.lower().endswith(valid_exts)
    ]
    if len(photos) < 3:
        sys.exit(f"Please provide at least 3 photos in {args.photos_dir} (found {len(photos)})")

    print(f"Found {len(photos)} photos. Generating 1080p branded wallpapers...")

    # Generate Hero Shot (01.jpg)
    hero = make_single_hero(photos[0], args.overline, args.property.upper(), args.subtitle, logo_img)
    p1 = os.path.join(args.output_dir, "01.jpg")
    hero.convert("RGB").save(p1, "JPEG", quality=92)
    print(f"  [SAVED] 01.jpg (Hero wallpaper)")

    # Generate Triptych Collage (02.jpg)
    p_bg = photos[0]
    p_c1 = photos[1 % len(photos)]
    p_c2 = photos[2 % len(photos)]
    p_c3 = photos[3 % len(photos)] if len(photos) > 3 else photos[0]
    collage = make_triptych_collage(p_bg, p_c1, p_c2, p_c3, args.overline, args.property.upper(), args.subtitle, logo_img)
    p2 = os.path.join(args.output_dir, "02.jpg")
    collage.convert("RGB").save(p2, "JPEG", quality=92)
    print(f"  [SAVED] 02.jpg (Collage wallpaper)")

    print(f"\nComplete! Wallpapers saved to {args.output_dir}")
    print("Now run: python launcher/build.py to bundle your branded wallpapers into the app.")

if __name__ == "__main__":
    main()
