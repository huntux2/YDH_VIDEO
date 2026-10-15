import os
import sys
import math
import random
import shutil
import wave
import struct
import subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

sys.stdout.reconfigure(line_buffering=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VIDEO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(VIDEO_ROOT, "assets")
DATE_DIR = os.path.join(VIDEO_ROOT, "2026-10-14")
WORK_DIR = os.path.join(VIDEO_ROOT, "work_rpg_frames")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(DATE_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

BOSS_ASSET_PATH = os.path.join(ASSETS_DIR, "rpg_boss_scene.jpg")
CHEST_ASSET_PATH = os.path.join(ASSETS_DIR, "mythic_loot_chest.jpg")

FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"
FONT_REG = r"C:\Windows\Fonts\malgun.ttf"

f_title = ImageFont.truetype(FONT_BOLD, 34)
f_sub = ImageFont.truetype(FONT_BOLD, 22)
f_badge = ImageFont.truetype(FONT_BOLD, 20)
f_small = ImageFont.truetype(FONT_REG, 18)
f_tiny = ImageFont.truetype(FONT_BOLD, 15)
f_cta = ImageFont.truetype(FONT_BOLD, 34)
f_huge = ImageFont.truetype(FONT_BOLD, 52)

S1_IMG = Image.open(os.path.join(ASSETS_DIR, "sticker_tired_finger.png")).convert("RGBA")
S2_IMG = Image.open(os.path.join(ASSETS_DIR, "sticker_chill_robot.png")).convert("RGBA")
APP_ICON = Image.open(os.path.join(ASSETS_DIR, "01_App_Icon_512x512.png")).convert("RGBA")
GAME_BG = Image.open(BOSS_ASSET_PATH).convert("RGBA")
LOOT_CHEST = Image.open(CHEST_ASSET_PATH).convert("RGBA")

W, H = 1080, 1920
FPS = 30
TOTAL_FRAMES = 540  # 18 seconds

# Phone dimensions: shifted slightly higher (PY=265) so bottom area (Y=1635..1900)
# can hold comic speech bubbles & stickers WITHOUT ever covering the HP Bar!
PW, PH = 680, 1360
PX = (W - PW) // 2  # 200
PY = 265  # Phone bottom is at Y = 1625

GAME_RESIZED = GAME_BG.resize((PW, PH), Image.Resampling.LANCZOS)

# Exact scanned coordinates inside 680x1360 screen:
# Green HP Bar is at screen X: 136..398, screen Y: 1250..1281
SCR_HP_X1, SCR_HP_X2 = 136, 398
SCR_HP_Y1, SCR_HP_Y2 = 1250, 1281

# Canvas coordinates of HP bar:
HP_BAR_X1 = PX + SCR_HP_X1  # 336
HP_BAR_X2 = PX + SCR_HP_X2  # 598
HP_BAR_Y1 = PY + SCR_HP_Y1  # 1515
HP_BAR_Y2 = PY + SCR_HP_Y2  # 1546

# Target Low-HP Watch Point: right ON the HP Bar at the 35% mark!
HP_WATCH_X = HP_BAR_X1 + int((HP_BAR_X2 - HP_BAR_X1) * 0.35)  # ~428
HP_WATCH_Y = (HP_BAR_Y1 + HP_BAR_Y2) // 2  # ~1530

# Potion Button center in canvas coords
POTION_X = PX + int(PW * 0.112)  # ~276
POTION_Y = PY + int(PH * 0.800)  # ~1353

# Ultimate Skill Button center in canvas coords
ULT_X = PX + int(PW * 0.815)  # ~754
ULT_Y = PY + int(PH * 0.785)  # ~1332

# Dragon Boss center in canvas coords
BOSS_X = PX + PW // 2  # 540
BOSS_Y = PY + int(PH * 0.35)  # ~741


def generate_rpg_soundtrack(wav_path):
    print("Generating custom RPG Boss Battle audio soundtrack...")
    sr = 44100
    duration = 18.0
    total_samples = int(sr * duration)
    samples = []

    for i in range(total_samples):
        t = i / sr
        val = 0.0

        beat = int(t * 4)
        notes = [110.0, 130.81, 146.83, 164.81]
        freq = notes[beat % 4]
        val += 0.12 * math.sin(2 * math.pi * freq * t)

        if t < 3.5:
            if (t % 0.45) < 0.12:
                val += 0.18 * math.sin(2 * math.pi * 150 * t)
            if 2.3 <= t <= 3.3:
                df = 320 - (t - 2.3) * 200
                val += 0.25 * math.sin(2 * math.pi * df * t)
        elif t < 7.5:
            # Sound when HP drops and locks on at ~5.2s
            if 4.8 <= t <= 5.1:
                val += 0.22 * math.sin(2 * math.pi * 880 * t)
            if 5.1 < t <= 5.5:
                val += 0.25 * math.sin(2 * math.pi * 1174.66 * t)
        elif t < 11.5:
            rel = t - 7.5
            if (rel % 1.0) < 0.12:
                val += 0.20 * math.sin(2 * math.pi * 659.25 * t)
        elif t < 15.0:
            rel = t - 11.5
            if rel < 1.1:
                if (rel % 0.4) < 0.08:
                    val += 0.15 * math.sin(2 * math.pi * 523.25 * t)
            elif rel < 2.2:
                hf = 523.25 + (rel - 1.1) * 550
                val += 0.28 * math.sin(2 * math.pi * hf * t)
            else:
                v_notes = [523.25, 659.25, 783.99, 1046.50]
                vn = v_notes[int((rel - 2.2) * 8) % 4]
                val += 0.25 * math.sin(2 * math.pi * vn * t)
        else:
            val += 0.15 * math.sin(2 * math.pi * 523.25 * t)
            val += 0.12 * math.sin(2 * math.pi * 659.25 * t)
            val += 0.12 * math.sin(2 * math.pi * 783.99 * t)

        val = max(-0.95, min(0.95, val))
        s_int = int(val * 32767)
        samples.append(struct.pack("<hh", s_int, s_int))

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b"".join(samples))


def create_base_canvas():
    canvas = Image.new("RGB", (W, H), (11, 17, 32))
    draw = ImageDraw.Draw(canvas)
    for y in range(0, H, 4):
        t = y / H
        r = int(11 * (1 - t) + 18 * t)
        g = int(17 * (1 - t) + 20 * t)
        b = int(32 * (1 - t) + 46 * t)
        draw.rectangle([(0, y), (W, y + 4)], fill=(r, g, b))
    return canvas


def draw_phone_frame(canvas, screen_img, border_color=(56, 189, 248), shake_x=0):
    pdraw = ImageDraw.Draw(canvas)
    cur_px = PX + shake_x
    pdraw.rounded_rectangle(
        [cur_px - 14, PY - 14, cur_px + PW + 14, PY + PH + 14],
        radius=48,
        fill=(5, 8, 15),
    )
    pdraw.rounded_rectangle(
        [cur_px - 8, PY - 8, cur_px + PW + 8, PY + PH + 8],
        radius=44,
        fill=(30, 41, 59),
        outline=border_color,
        width=3,
    )
    pdraw.rounded_rectangle([cur_px, PY, cur_px + PW, PY + PH], radius=36, fill=(0, 0, 0))
    if screen_img:
        canvas.paste(screen_img, (cur_px, PY))
    pdraw.rounded_rectangle(
        [cur_px + PW // 2 - 50, PY + 14, cur_px + PW // 2 + 50, PY + 20],
        radius=3,
        fill=(71, 85, 105),
    )


def draw_star(draw, cx, cy, r_out, r_in, color):
    pts = []
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(pts, fill=color)


def draw_sparkle(draw, cx, cy, size, color=(255, 255, 255, 255)):
    pts = [
        (cx, cy - size),
        (cx + size * 0.25, cy - size * 0.25),
        (cx + size, cy),
        (cx + size * 0.25, cy + size * 0.25),
        (cx, cy + size),
        (cx - size * 0.25, cy + size * 0.25),
        (cx - size, cy),
        (cx - size * 0.25, cy - size * 0.25),
    ]
    draw.polygon(pts, fill=color)


def draw_vector_check(draw, x, y, size=24, color=(56, 189, 248)):
    draw.line([(x, y + size * 0.5), (x + size * 0.4, y + size * 0.9)], fill=color, width=3)
    draw.line([(x + size * 0.4, y + size * 0.9), (x + size, y + size * 0.1)], fill=color, width=3)


def draw_dynamic_hp_bar(screen_draw, hp_ratio, is_healing=False):
    """
    Draws the dynamic HP bar right over the original green HP bar on the game screen
    (SCR_HP_X1..SCR_HP_X2 = 136..398, SCR_HP_Y1..SCR_HP_Y2 = 1250..1281).
    As hp_ratio drops below 0.35, the bar turns RED (#EF4444) and the empty right portion
    becomes dark red/black (#2D1216) so the color change at the 35% mark is crystal clear!
    """
    x1, x2 = SCR_HP_X1, SCR_HP_X2
    y1, y2 = SCR_HP_Y1, SCR_HP_Y2
    total_w = x2 - x1
    hp_ratio = max(0.0, min(1.0, hp_ratio))
    fill_w = int(total_w * hp_ratio)

    # Background of empty HP bar (Dark crimson when low!)
    empty_bg = (45, 18, 22) if hp_ratio <= 0.38 else (25, 35, 28)
    border_col = (239, 68, 68) if hp_ratio <= 0.38 else (255, 255, 255)
    if is_healing:
        border_col = (56, 189, 248)

    screen_draw.rounded_rectangle([x1 - 2, y1 - 2, x2 + 2, y2 + 2], radius=7, fill=empty_bg, outline=border_col, width=2)

    # Filled HP portion
    if fill_w > 4:
        if is_healing:
            bar_col = (16, 185, 129) if hp_ratio < 0.45 else (34, 197, 94)
        elif hp_ratio > 0.5:
            bar_col = (34, 197, 94)  # Bright Green
        elif hp_ratio > 0.35:
            bar_col = (245, 158, 11)  # Warning Orange
        else:
            bar_col = (239, 68, 68)  # Danger Red (#EF4444)
        screen_draw.rounded_rectangle([x1, y1, x1 + fill_w, y2], radius=5, fill=bar_col)
        # Bright rising leading edge when healing so the viewer's eye tracks the bar rising!
        if is_healing and fill_w < total_w - 2:
            edge_x = x1 + fill_w
            screen_draw.rectangle([max(x1, edge_x - 6), y1, edge_x + 2, y2], fill=(167, 243, 208))

    # Draw 35% Threshold Marker Line on the HP bar
    thresh_x = x1 + int(total_w * 0.35)
    screen_draw.line([(thresh_x, y1 - 4), (thresh_x, y2 + 4)], fill=(250, 204, 21), width=2)

    # HP Text inside bar
    cur_hp = int(14500 * hp_ratio)
    hp_label = f"HP  {cur_hp:,} / 14,500 ({int(hp_ratio * 100)}%)"
    screen_draw.text(((x1 + x2) // 2, (y1 + y2) // 2), hp_label, font=f_tiny, fill=(255, 255, 255), anchor="mm")


def draw_potion_click_effect(draw, progress, label_text="1st: CLICK POTION!"):
    """
    Clearly visualizes clicking the Healing Potion button (POTION_X, POTION_Y) FIRST.
    Draws a trigger line from HP Watch Point -> Potion Button, shockwave rings,
    a pressed Touch #1 target icon on the Potion button, and a bold callout badge.
    """
    progress = max(0.0, min(1.0, progress))
    # Trigger line from HP Bar 35% Watch Point -> Potion Button
    draw.line([(HP_WATCH_X, HP_WATCH_Y), (POTION_X, POTION_Y)], fill=(250, 204, 21), width=4)

    # Expanding click shockwave rings around Potion Button
    r1 = int(24 + progress * 48)
    r2 = int(16 + ((progress * 1.5) % 1.0) * 38)
    draw.ellipse([POTION_X - r1, POTION_Y - r1, POTION_X + r1, POTION_Y + r1], outline=(250, 204, 21), width=4)
    draw.ellipse([POTION_X - r2, POTION_Y - r2, POTION_X + r2, POTION_Y + r2], outline=(34, 197, 94), width=4)

    # Touch #1 Target Button pressing directly on the Potion icon
    press_r = 22 if (int(progress * 10) % 2 == 0) else 18
    draw.ellipse(
        [POTION_X - press_r, POTION_Y - press_r, POTION_X + press_r, POTION_Y + press_r],
        fill=(34, 197, 94),
        outline=(255, 255, 255),
        width=3,
    )
    draw.text((POTION_X, POTION_Y), "TAP", font=f_tiny, fill=(255, 255, 255), anchor="mm")

    # Callout badge right above Potion Button (compact width so it never touches the 11x Loupe)
    draw.rounded_rectangle(
        [POTION_X - 68, POTION_Y - 98, POTION_X + 172, POTION_Y - 54],
        radius=12,
        fill=(22, 163, 74),
        outline=(250, 204, 21),
        width=3,
    )
    draw.text((POTION_X + 52, POTION_Y - 76), label_text, font=f_small, fill=(255, 255, 255), anchor="mm")


def draw_hp_rising_effect(draw, hp_ratio, progress, label_text=None):
    """
    Clearly visualizes the HP Bar rising AFTER the Potion button was clicked.
    Draws green healing energy particles flowing from the Potion Button into the HP Bar,
    highlights the HP Bar border on canvas, and shows a bold rising HP percentage badge.
    """
    progress = max(0.0, min(1.0, progress))

    # Keep a subtle clicked ring on Potion Button as source of heal
    draw.ellipse([POTION_X - 28, POTION_Y - 28, POTION_X + 28, POTION_Y + 28], outline=(34, 197, 94), width=3)

    # Stream of green healing orbs + crosses moving from Potion Button (276, 1353) -> HP Bar (440, 1530)
    target_x = HP_BAR_X1 + int((HP_BAR_X2 - HP_BAR_X1) * max(0.35, hp_ratio))
    target_y = HP_WATCH_Y
    draw.line([(POTION_X, POTION_Y), (target_x, target_y)], fill=(16, 185, 129), width=3)

    for orb_i in range(4):
        orb_p = (progress * 1.6 + orb_i * 0.25) % 1.0
        ox = int(POTION_X + (target_x - POTION_X) * orb_p)
        oy = int(POTION_Y + (target_y - POTION_Y) * orb_p)
        draw.ellipse([ox - 9, oy - 9, ox + 9, oy + 9], fill=(34, 197, 94), outline=(255, 255, 255), width=2)
        draw.line([(ox - 5, oy), (ox + 5, oy)], fill=(255, 255, 255), width=2)
        draw.line([(ox, oy - 5), (ox, oy + 5)], fill=(255, 255, 255), width=2)

    # Glowing green frame around the entire HP Bar on canvas
    draw.rounded_rectangle(
        [HP_BAR_X1 - 6, HP_BAR_Y1 - 6, HP_BAR_X2 + 6, HP_BAR_Y2 + 6],
        radius=10,
        outline=(52, 211, 153),
        width=3,
    )

    # Floating badge right above the HP Bar showing the live HP rise
    if label_text is None:
        label_text = f"2nd: HP RISING! -> {int(hp_ratio * 100)}% (+HEAL!)"
    draw.rounded_rectangle(
        [HP_BAR_X1 - 10, HP_BAR_Y1 - 62, HP_BAR_X2 + 75, HP_BAR_Y1 - 16],
        radius=12,
        fill=(5, 150, 105),
        outline=(250, 204, 21),
        width=3,
    )
    draw.text(
        ((HP_BAR_X1 + HP_BAR_X2 + 65) // 2, HP_BAR_Y1 - 39),
        label_text,
        font=f_small,
        fill=(255, 255, 255),
        anchor="mm",
    )


def draw_autonomous_hud(canvas, hx, hy, is_running=False, active_tool=None):
    hud_w, hud_h = 440, 58
    hud_img = Image.new("RGBA", (hud_w, hud_h), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(hud_img)

    border_col = (16, 185, 129, 255) if is_running else (56, 189, 248, 220)
    hdraw.rounded_rectangle(
        [0, 0, hud_w, hud_h],
        radius=29,
        fill=(15, 23, 42, 235),
        outline=border_col,
        width=2,
    )

    cx_list = [36, 98, 160, 222, 284, 346, 404]

    run_bg = (16, 185, 129) if is_running else (34, 197, 94)
    hdraw.ellipse([cx_list[0] - 18, 29 - 18, cx_list[0] + 18, 29 + 18], fill=run_bg)
    if is_running:
        hdraw.rectangle([cx_list[0] - 6, 21, cx_list[0] - 2, 37], fill=(255, 255, 255))
        hdraw.rectangle([cx_list[0] + 2, 21, cx_list[0] + 6, 37], fill=(255, 255, 255))
    else:
        hdraw.polygon(
            [(cx_list[0] - 5, 21), (cx_list[0] + 8, 29), (cx_list[0] - 5, 37)],
            fill=(255, 255, 255),
        )

    c2 = cx_list[1]
    is_cond = active_tool == "cond"
    if is_cond:
        hdraw.ellipse([c2 - 18, 29 - 18, c2 + 18, 29 + 18], fill=(14, 165, 233))
    hdraw.ellipse([c2 - 10, 29 - 12, c2 + 4, 29 + 2], outline=(255, 255, 255), width=2)
    hdraw.line([(c2 + 2, 29), (c2 + 10, 29 + 8)], fill=(255, 255, 255), width=3)
    hdraw.ellipse([c2 + 6, 29 - 18, c2 + 18, 29 - 6], fill=(56, 189, 248))
    hdraw.text((c2 + 12, 29 - 12), "1", font=f_tiny, fill=(15, 23, 42), anchor="mm")

    c3 = cx_list[2]
    hdraw.ellipse([c3 - 10, 29 - 10, c3 + 10, 29 + 10], outline=(148, 163, 184), width=2)
    hdraw.ellipse([c3 - 4, 29 - 4, c3 + 4, 29 + 4], fill=(34, 197, 94))
    hdraw.ellipse([c3 + 6, 29 - 18, c3 + 18, 29 - 6], fill=(34, 197, 94))
    hdraw.text((c3 + 12, 29 - 12), "1", font=f_tiny, fill=(255, 255, 255), anchor="mm")

    c4 = cx_list[3]
    hdraw.line([(c4 - 10, 29), (c4 + 10, 29)], fill=(245, 158, 11), width=2)
    hdraw.polygon([(c4 + 12, 29), (c4 + 6, 25), (c4 + 6, 33)], fill=(245, 158, 11))
    hdraw.ellipse([c4 + 6, 29 - 18, c4 + 18, 29 - 6], fill=(245, 158, 11))
    hdraw.text((c4 + 12, 29 - 12), "1", font=f_tiny, fill=(255, 255, 255), anchor="mm")

    c5 = cx_list[4]
    hdraw.arc([c5 - 10, 29 - 10, c5 + 10, 29 + 10], start=45, end=315, fill=(168, 85, 247), width=2)
    hdraw.polygon([(c5 + 9, 23), (c5 + 4, 17), (c5 + 12, 17)], fill=(168, 85, 247))

    c6 = cx_list[5]
    hdraw.ellipse([c6 - 8, 29 - 8, c6 + 8, 29 + 8], outline=(148, 163, 184), width=2)
    hdraw.ellipse([c6 - 3, 29 - 3, c6 + 3, 29 + 3], fill=(148, 163, 184))

    c7 = cx_list[6]
    hdraw.line([(c7 - 6, 23), (c7 + 6, 35)], fill=(148, 163, 184), width=2)
    hdraw.line([(c7 + 6, 23), (c7 - 6, 35)], fill=(148, 163, 184), width=2)

    canvas.paste(hud_img, (hx, hy), hud_img)


WAV_PATH = os.path.join(WORK_DIR, "rpg_boss_soundtrack.wav")
generate_rpg_soundtrack(WAV_PATH)

print("Starting Global English RPG Auto HP Potion (v3: Click Potion FIRST -> Then HP Rises)...")

for frame_idx in range(TOTAL_FRAMES):
    t = frame_idx / FPS

    # -------------------------------------------------------------
    # SCENE 1 (0.0s ~ 3.5s, Frames 0 ~ 104): Dumb Auto Clicker Wasting Potions -> HP Drops to 0!
    # -------------------------------------------------------------
    if frame_idx < 105:
        screen = GAME_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        # 0..55: HP is 100% full while dumb clicker wastes all potions
        # 55..80: Boss attacks! HP rapidly drains 100% -> 0%
        # 80..104: Dead (0% HP)
        if frame_idx < 55:
            cur_hp_ratio = 1.0
        elif frame_idx < 80:
            cur_hp_ratio = max(0.0, 1.0 - (frame_idx - 55) / 22.0)
        else:
            cur_hp_ratio = 0.0

        draw_dynamic_hp_bar(sdraw, cur_hp_ratio)

        if frame_idx >= 75:
            overlay = Image.new("RGBA", (PW, PH), (185, 28, 28, 110))
            screen.paste(overlay, (0, 0), overlay)
            sdraw = ImageDraw.Draw(screen)
            draw_dynamic_hp_bar(sdraw, 0.0)
            sdraw.rounded_rectangle(
                [60, PH // 2 - 110, PW - 60, PH // 2 + 30],
                radius=20,
                fill=(15, 23, 42),
                outline=(239, 68, 68),
                width=4,
            )
            sdraw.text((PW // 2, PH // 2 - 60), "YOU DIED!", font=f_huge, fill=(239, 68, 68), anchor="mm")
            sdraw.text(
                (PW // 2, PH // 2 - 2),
                "0 Potions Left when HP Dropped!",
                font=f_sub,
                fill=(255, 255, 255),
                anchor="mm",
            )

        shake = int(7 * math.sin(frame_idx * 1.8)) if (frame_idx % 8 < 4) else 0
        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(239, 68, 68), shake_x=shake)
        draw = ImageDraw.Draw(canvas)

        # Top Alert Banner
        draw.rounded_rectangle(
            [40, 40, W - 40, 220],
            radius=28,
            fill=(220, 38, 38),
            outline=(255, 255, 255),
            width=3,
        )
        draw.text(
            (W // 2, 95),
            "[DUMB AUTO CLICKER] Wasting All Potions?!",
            font=f_title,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 165),
            "Spams Heal at 100% Full HP -> 0 Potions left when HP drops!",
            font=f_sub,
            fill=(254, 226, 226),
            anchor="mm",
        )

        # Blind clicks on Potion button
        px_tap = POTION_X + shake
        py_tap = POTION_Y
        draw.ellipse([px_tap - 42, py_tap - 42, px_tap + 42, py_tap + 42], outline=(239, 68, 68), width=5)
        draw.line([(px_tap - 25, py_tap - 25), (px_tap + 25, py_tap + 25)], fill=(239, 68, 68), width=5)
        draw.line([(px_tap + 25, py_tap - 25), (px_tap - 25, py_tap + 25)], fill=(239, 68, 68), width=5)

        pot_left = max(0, 5 - (frame_idx // 10))
        msg_txt = f"[WASTED!] HP is 100%! (Potion x{pot_left})" if pot_left > 0 else "[EMPTY!] 0 Potions Left!"
        draw.rounded_rectangle(
            [px_tap - 45, py_tap - 110, px_tap + 335, py_tap - 62],
            radius=12,
            fill=(220, 38, 38),
            outline=(255, 255, 255),
            width=2,
        )
        draw.text((px_tap + 145, py_tap - 86), msg_txt, font=f_small, fill=(255, 255, 255), anchor="mm")

        # Bottom area (Y=1640..1900): Speech bubble & Tired Hand BELOW the phone so HP Bar is 100% visible!
        s1_bob = int(10 * math.sin(frame_idx * 0.4))
        s1_w, s1_h = 280, 280
        s1_resized = S1_IMG.resize((s1_w, s1_h), Image.Resampling.LANCZOS)
        canvas.paste(s1_resized, (W - s1_w - 20, H - s1_h - 10 + s1_bob), s1_resized)

        bx, by, bw, bh = 50, 1660, 690, 190
        draw.rounded_rectangle(
            [bx, by, bx + bw, by + bh],
            radius=26,
            fill=(255, 255, 255),
            outline=(220, 38, 38),
            width=4,
        )
        draw.text(
            (bx + bw // 2, by + 58),
            '"Why drink potions at 100% Full HP?!"',
            font=f_sub,
            fill=(185, 28, 28),
            anchor="mm",
        )
        draw.text(
            (bx + bw // 2, by + 125),
            "Wasted all potions -> Died when Boss attacked!",
            font=f_badge,
            fill=(30, 41, 59),
            anchor="mm",
        )

    # -------------------------------------------------------------
    # SCENE 2 (3.5s ~ 7.5s, Frames 105 ~ 224):
    # 1) HP drops 100% -> 25% (Red) & 11x Loupe locks on HP Bar
    # 2) FIRST: Potion Button is clicked while HP is 25%!
    # 3) SECOND: Right after Potion click, HP Bar rises 25% -> 100%!
    # -------------------------------------------------------------
    elif frame_idx < 225:
        rel_f = frame_idx - 105  # 0..119
        screen = GAME_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        # Causal sequence in Scene 2:
        # rel_f 0..28: HP drops smoothly from 100% (Green) -> 25% (Red Alert!)
        # rel_f 28..62: Holds at 25% (Red) while 11x Loupe locks on & saves Condition #1!
        # rel_f 62..84: [STEP A] Potion Button is CLICKED first (while HP is still at 25% Red!)
        # rel_f 84..112: [STEP B] Right after Potion click, HP Bar rises smoothly 25% -> 100% Full Green!
        # rel_f 112..119: Holds at 100% Full Green!
        s2_is_healing = False
        if rel_f < 28:
            cur_hp_ratio = 1.0 - (rel_f / 28.0) * 0.75  # 1.0 -> 0.25
        elif rel_f < 84:
            cur_hp_ratio = 0.25  # Stays at 25% before & during the Potion Button click!
        elif rel_f < 112:
            s2_is_healing = True
            cur_hp_ratio = 0.25 + ((rel_f - 84) / 28.0) * 0.75  # Rises 25% -> 100% AFTER click!
        else:
            cur_hp_ratio = 1.0

        draw_dynamic_hp_bar(sdraw, cur_hp_ratio, is_healing=s2_is_healing)

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(14, 165, 233))
        draw = ImageDraw.Draw(canvas)

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=False, active_tool="cond")

        # Top Banner
        draw.rounded_rectangle(
            [40, 40, W - 40, 210],
            radius=28,
            fill=(2, 132, 199),
            outline=(255, 255, 255),
            width=3,
        )
        draw.text(
            (W // 2, 92),
            "[STEP 1: PIXEL PICKER] Aim 11x Loupe at the HP Bar!",
            font=f_title,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 160),
            "HP < 35% (Red) -> 1st: Click Potion -> 2nd: HP Rises to 100%!",
            font=f_sub,
            fill=(224, 242, 254),
            anchor="mm",
        )

        is_low_locked = cur_hp_ratio <= 0.35
        ring_col = (239, 68, 68) if is_low_locked else (34, 197, 94)

        # 1. Draw Target Crosshair directly ON the HP Bar 35% point:
        tx, ty = HP_WATCH_X, HP_WATCH_Y
        draw.ellipse([tx - 18, ty - 18, tx + 18, ty + 18], outline=(250, 204, 21), width=3)
        draw.ellipse([tx - 12, ty - 12, tx + 12, ty + 12], outline=ring_col, width=3)
        draw.line([(tx - 24, ty), (tx + 24, ty)], fill=(250, 204, 21), width=2)
        draw.line([(tx, ty - 24), (tx, ty + 24)], fill=(250, 204, 21), width=2)
        draw.rectangle([tx - 4, ty - 4, tx + 4, ty + 4], fill=ring_col, outline=(255, 255, 255), width=1)

        # 2. Draw 11x Zoom Loupe well above the HP Bar & Potion Button so zero badges overlap
        lx, ly = HP_WATCH_X + 5, HP_BAR_Y1 - 245
        loupe_r = 56
        draw.line([(tx, ty - 18), (lx, ly + loupe_r)], fill=(250, 204, 21), width=3)

        # Live 11x Pixel Grid inside Loupe showing the actual HP gauge edge moving across the center pixel!
        loupe_img = Image.new("RGBA", (loupe_r * 2, loupe_r * 2), (25, 15, 20, 255))
        ldraw = ImageDraw.Draw(loupe_img)
        edge_offset_cells = int((cur_hp_ratio - 0.35) * 18)
        center_cell = 4
        cell_sz = (loupe_r * 2) // 9
        for gy in range(9):
            for gx in range(9):
                if 2 <= gy <= 6:
                    if gx <= center_cell + edge_offset_cells:
                        c_fill = (34, 197, 94) if cur_hp_ratio > 0.35 else (239, 68, 68)
                    else:
                        c_fill = (239, 68, 68) if is_low_locked else (45, 18, 22)
                else:
                    c_fill = (15, 23, 42)
                ldraw.rectangle(
                    [gx * cell_sz, gy * cell_sz, (gx + 1) * cell_sz - 1, (gy + 1) * cell_sz - 1],
                    fill=c_fill,
                    outline=(30, 41, 59),
                )

        mask = Image.new("L", (loupe_r * 2, loupe_r * 2), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.ellipse([0, 0, loupe_r * 2, loupe_r * 2], fill=255)
        canvas.paste(loupe_img, (lx - loupe_r, ly - loupe_r), mask)

        draw.ellipse([lx - loupe_r, ly - loupe_r, lx + loupe_r, ly + loupe_r], outline=ring_col, width=4)
        draw.ellipse(
            [lx - loupe_r - 3, ly - loupe_r - 3, lx + loupe_r + 3, ly + loupe_r + 3],
            outline=(250, 204, 21),
            width=2,
        )
        draw.line([(lx - loupe_r - 10, ly), (lx + loupe_r + 10, ly)], fill=(255, 255, 255), width=1)
        draw.line([(lx, ly - loupe_r - 10), (lx, ly + loupe_r + 10)], fill=(255, 255, 255), width=1)
        draw.rectangle([lx - 6, ly - 6, lx + 6, ly + 6], outline=(250, 204, 21), width=2)

        # Loupe Top Badge
        draw.rounded_rectangle(
            [lx - 82, ly - loupe_r - 32, lx + 82, ly - loupe_r - 6],
            radius=8,
            fill=(15, 23, 42),
            outline=ring_col,
            width=2,
        )
        draw.text(
            (lx, ly - loupe_r - 19),
            "11x Zoom on HP Bar",
            font=f_tiny,
            fill=(250, 204, 21),
            anchor="mm",
        )

        # Floating Info Card to the right of the Loupe
        card_w, card_h = 390, 126
        cx = lx + loupe_r + 18
        cy = ly - 62
        draw.line([(lx + loupe_r, ly), (cx, cy + card_h // 2)], fill=ring_col, width=3)
        draw.rounded_rectangle(
            [cx, cy, cx + card_w, cy + card_h],
            radius=16,
            fill=(15, 23, 42),
            outline=ring_col,
            width=3,
        )

        swatch_col = (239, 68, 68) if is_low_locked else (34, 197, 94)
        draw.rounded_rectangle(
            [cx + 14, cy + 16, cx + 56, cy + 58],
            radius=8,
            fill=swatch_col,
            outline=(255, 255, 255),
            width=2,
        )

        if rel_f < 28:
            draw.text(
                (cx + 68, cy + 23),
                f"Live HP: {int(cur_hp_ratio*100)}% (Dropping...)",
                font=f_badge,
                fill=(34, 197, 94),
            )
            draw.text(
                (cx + 68, cy + 50),
                "Watching HP Bar 35% threshold...",
                font=f_small,
                fill=(226, 232, 240),
            )
            draw.rounded_rectangle(
                [cx + 16, cy + 78, cx + card_w - 16, cy + 110],
                radius=10,
                fill=(51, 65, 85),
                outline=(148, 163, 184),
                width=1,
            )
            draw.text(
                (cx + card_w // 2, cy + 94),
                "Target: HP Bar 35% Point (X 428, Y 1530)",
                font=f_small,
                fill=(203, 213, 225),
                anchor="mm",
            )
        elif rel_f < 62:
            draw.text(
                (cx + 68, cy + 23),
                "HP < 35%! Red Pixel Detected!",
                font=f_badge,
                fill=(248, 113, 113),
            )
            draw.text(
                (cx + 68, cy + 50),
                "Color: #EF4444 at (X 428, Y 1530)",
                font=f_small,
                fill=(226, 232, 240),
            )
            draw.rounded_rectangle(
                [cx + 16, cy + 78, cx + card_w - 16, cy + 110],
                radius=10,
                fill=(16, 185, 129),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text(
                (cx + card_w // 2, cy + 94),
                "LOCKED! Condition #1 -> Tap Potion!",
                font=f_small,
                fill=(255, 255, 255),
                anchor="mm",
            )
        elif rel_f < 84:
            # STEP A in Scene 2: Show Potion Button being clicked FIRST while HP is 25%!
            draw.text(
                (cx + 68, cy + 23),
                "STEP A: Clicking Potion Button!",
                font=f_badge,
                fill=(250, 204, 21),
            )
            draw.text(
                (cx + 68, cy + 50),
                "Low HP matched -> Taps Potion first!",
                font=f_small,
                fill=(226, 232, 240),
            )
            draw.rounded_rectangle(
                [cx + 16, cy + 78, cx + card_w - 16, cy + 110],
                radius=10,
                fill=(22, 163, 74),
                outline=(250, 204, 21),
                width=2,
            )
            draw.text(
                (cx + card_w // 2, cy + 94),
                "1st: CLICK POTION BUTTON!",
                font=f_small,
                fill=(255, 255, 255),
                anchor="mm",
            )
            click_prog = (rel_f - 62) / 22.0
            draw_potion_click_effect(draw, click_prog, label_text="1st: CLICK POTION!")
        else:
            # STEP B in Scene 2: Right AFTER Potion Click, HP Bar rises 25% -> 100%!
            draw.text(
                (cx + 68, cy + 23),
                f"STEP B: HP Rising! ({int(cur_hp_ratio*100)}%)",
                font=f_badge,
                fill=(34, 197, 94),
            )
            draw.text(
                (cx + 68, cy + 50),
                "Potion Used -> HP Refills to 100%!",
                font=f_small,
                fill=(226, 232, 240),
            )
            draw.rounded_rectangle(
                [cx + 16, cy + 78, cx + card_w - 16, cy + 110],
                radius=10,
                fill=(5, 150, 105),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text(
                (cx + card_w // 2, cy + 94),
                f"2nd: HP RISES 25% -> {int(cur_hp_ratio*100)}%!",
                font=f_small,
                fill=(255, 255, 255),
                anchor="mm",
            )
            rise_prog = (rel_f - 84) / 28.0
            draw_hp_rising_effect(
                draw,
                cur_hp_ratio,
                rise_prog,
                label_text=f"2nd: HP RISING! 25% -> {int(cur_hp_ratio*100)}%",
            )

        # Bottom explanation card (in Y=1665..1855 below the phone)
        draw.rounded_rectangle(
            [60, 1665, W - 60, 1845],
            radius=24,
            fill=(15, 23, 42),
            outline=(56, 189, 248),
            width=3,
        )
        draw.text(
            (W // 2, 1720),
            "1. Detect Low HP (<35%) -> 2. Click Potion -> 3. HP Rises!",
            font=f_sub,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 1785),
            '"Clicks the Potion FIRST, then your HP Bar refills to 100%!"',
            font=f_badge,
            fill=(56, 189, 248),
            anchor="mm",
        )

    # -------------------------------------------------------------
    # SCENE 3 (7.5s ~ 11.5s, Frames 225 ~ 344): Smart RPG Boss Logic
    # Synchronized background: Watch HP drop -> Click Potion FIRST -> HP Rises -> Ultimate!
    # -------------------------------------------------------------
    elif frame_idx < 345:
        rel_f = frame_idx - 225  # 0..119
        screen = GAME_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        # Synchronize the HP Bar and Potion Click in Scene 3 with the 3 steps:
        # rel_f 0..39 (Step 1 - Watch HP Bar): HP drops 100% -> 26% (Red)
        # rel_f 40..61 (Step 2a - Click Potion FIRST): HP holds at 26% while Potion Button is clicked!
        # rel_f 62..84 (Step 2b - HP Rises AFTER Click): HP rises 26% -> 100% Full Green!
        # rel_f 85..119 (Step 3 - Ultimate Counter): HP is 100% Full Green while Ultimate fires!
        s3_is_healing = False
        if rel_f < 40:
            s3_hp = 1.0 - (rel_f / 40.0) * 0.74  # 1.0 -> 0.26
            step_idx = 0
        elif rel_f < 62:
            s3_hp = 0.26  # Holds at 26% while clicking Potion!
            step_idx = 1
        elif rel_f < 85:
            s3_is_healing = True
            s3_hp = 0.26 + ((rel_f - 62) / 23.0) * 0.74  # Rises 26% -> 100% AFTER click!
            step_idx = 1
        else:
            s3_hp = 1.0
            step_idx = 2

        draw_dynamic_hp_bar(sdraw, s3_hp, is_healing=s3_is_healing)

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(168, 85, 247))
        draw = ImageDraw.Draw(canvas)

        draw.rounded_rectangle(
            [40, 40, W - 40, 210],
            radius=28,
            fill=(109, 40, 217),
            outline=(255, 255, 255),
            width=3,
        )
        draw.text(
            (W // 2, 92),
            "[STEP 2: BOSS COMBO] Click Potion -> HP Rises + Ultimate!",
            font=f_title,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 160),
            "0% Potion Waste! Smart pixel monitoring for immortal AFK farming",
            font=f_sub,
            fill=(237, 233, 254),
            anchor="mm",
        )

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=False, active_tool=None)

        mc_x = PX + 35
        mc_y = PY + 200
        mc_w = PW - 70
        mc_h = 435
        draw.rounded_rectangle(
            [mc_x, mc_y, mc_x + mc_w, mc_y + mc_h],
            radius=22,
            fill=(15, 23, 42),
            outline=(168, 85, 247),
            width=3,
        )

        draw.text(
            (mc_x + mc_w // 2, mc_y + 35),
            "[Macro #1] Immortal Boss Hunter Combo",
            font=f_badge,
            fill=(250, 204, 21),
            anchor="mm",
        )
        draw.line([(mc_x + 20, mc_y + 65), (mc_x + mc_w - 20, mc_y + 65)], fill=(51, 65, 85), width=2)

        steps = [
            ("1. Watch HP Bar", "Detect when 35% mark on HP Bar turns Red", (56, 189, 248)),
            ("2. Click Potion -> Heal", "Click Potion FIRST -> HP Bar rises to 100%!", (34, 197, 94)),
            ("3. Ultimate Counter", "Trigger Ultimate Sword Slash at Boss!", (245, 158, 11)),
        ]

        for s_i, (st_t, st_d, st_c) in enumerate(steps):
            sy = mc_y + 85 + s_i * 92
            is_active = s_i == step_idx
            bg_col = (30, 41, 59) if not is_active else (51, 65, 85)
            out_col = st_c if is_active else (71, 85, 105)
            draw.rounded_rectangle(
                [mc_x + 20, sy, mc_x + mc_w - 20, sy + 74],
                radius=14,
                fill=bg_col,
                outline=out_col,
                width=3 if is_active else 1,
            )

            draw.text((mc_x + 38, sy + 24), st_t, font=f_badge, fill=st_c)
            draw.text((mc_x + 38, sy + 49), st_d, font=f_small, fill=(226, 232, 240))
            if is_active:
                draw_sparkle(draw, mc_x + mc_w - 45, sy + 37, 12, color=st_c)

        draw.rounded_rectangle(
            [mc_x + 20, mc_y + mc_h - 52, mc_x + mc_w - 20, mc_y + mc_h - 14],
            radius=10,
            fill=(88, 28, 135),
            outline=(168, 85, 247),
            width=1,
        )
        draw.text(
            (mc_x + mc_w // 2, mc_y + mc_h - 33),
            "24/7 Immortal Loop: Auto-Heal & Farm Bosses AFK!",
            font=f_small,
            fill=(255, 255, 255),
            anchor="mm",
        )

        # Live visual action on the game UI below the card in Scene 3:
        if rel_f < 40:
            rad_r = int(14 + ((rel_f % 15) / 15.0) * 24)
            draw.ellipse(
                [HP_WATCH_X - rad_r, HP_WATCH_Y - rad_r, HP_WATCH_X + rad_r, HP_WATCH_Y + rad_r],
                outline=(56, 189, 248),
                width=3,
            )
        elif rel_f < 62:
            draw_potion_click_effect(draw, (rel_f - 40) / 22.0, label_text="1st: CLICK POTION!")
        elif rel_f < 85:
            draw_hp_rising_effect(
                draw,
                s3_hp,
                (rel_f - 62) / 23.0,
                label_text=f"2nd: HP RISING! 26% -> {int(s3_hp*100)}%",
            )
        else:
            draw.ellipse([ULT_X - 42, ULT_Y - 42, ULT_X + 42, ULT_Y + 42], outline=(250, 204, 21), width=4)

        s_title, s_desc, s_col = steps[step_idx]
        draw.rounded_rectangle(
            [60, 1665, W - 60, 1845],
            radius=24,
            fill=(15, 23, 42),
            outline=s_col,
            width=3,
        )
        draw.text((W // 2, 1720), f"Active Step: {s_title}", font=f_sub, fill=s_col, anchor="mm")
        draw.text(
            (W // 2, 1785),
            "Clicks Potion FIRST when HP < 35% -> HP Rises to 100%!",
            font=f_badge,
            fill=(226, 232, 240),
            anchor="mm",
        )

    # -------------------------------------------------------------
    # SCENE 4 (11.5s ~ 15.0s, Frames 345 ~ 449):
    # Live Battle:
    # - Phase A (rel_f 0..24): HP drops 100% -> 46% (Green = Safe, holds potion)
    # - Phase B1 (rel_f 24..34): Boss hits! HP drops to 24% (RED < 35% Detected!)
    # - Phase B2 (rel_f 34..52): [1st: CLICK POTION!] Potion button is clicked FIRST while HP is 24%!
    # - Phase B3 (rel_f 52..78): [2nd: HP RISES!] Right AFTER Potion click, HP Bar rises 24% -> 100% + Ultimate!
    # - Phase C (rel_f 78..104): Boss Slain & Mythic Chest Popup (with 100% Full HP Bar!)
    # -------------------------------------------------------------
    elif frame_idx < 450:
        rel_f = frame_idx - 345  # 0..104
        screen = GAME_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        is_healing_now = False
        if rel_f < 24:
            cur_hp_ratio = 1.0 - (rel_f / 24.0) * 0.54  # 1.0 -> 0.46 (Green)
        elif rel_f < 52:
            cur_hp_ratio = 0.24  # Stays at 24% (Red) during Low-HP detection AND while clicking Potion FIRST!
        elif rel_f < 78:
            is_healing_now = True
            cur_hp_ratio = min(1.0, 0.24 + ((rel_f - 52) / 22.0) * 0.76)  # Rises 24% -> 100% AFTER Potion click!
        else:
            cur_hp_ratio = 1.0

        draw_dynamic_hp_bar(sdraw, cur_hp_ratio, is_healing=is_healing_now)

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(16, 185, 129))
        draw = ImageDraw.Draw(canvas)

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=True, active_tool=None)

        # Top Banner
        draw.rounded_rectangle(
            [40, 35, W - 40, 155],
            radius=24,
            fill=(16, 185, 129),
            outline=(255, 255, 255),
            width=3,
        )
        draw.text(
            (W // 2, 72),
            "[STEP 3: LIVE BATTLE] Click Potion -> HP Rises to 100%!",
            font=f_title,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 124),
            "Low HP Detected -> 1st: Clicks Potion -> 2nd: HP Rises & Slays Boss!",
            font=f_sub,
            fill=(209, 250, 229),
            anchor="mm",
        )

        # Target Status Box at Y: 168..252
        t_card_y = 168
        draw.rounded_rectangle(
            [50, t_card_y, W - 50, t_card_y + 84],
            radius=18,
            fill=(15, 23, 42),
            outline=(250, 204, 21),
            width=2,
        )
        draw.text(
            (80, t_card_y + 26),
            f"HP Bar Watch Point: (X {HP_WATCH_X}, Y {HP_WATCH_Y})",
            font=f_badge,
            fill=(250, 204, 21),
        )
        draw.text(
            (80, t_card_y + 56),
            f"Live HP: {int(cur_hp_ratio * 100)}%  |  Sequence: Low HP -> Click Potion -> HP Rises!",
            font=f_small,
            fill=(255, 255, 255),
        )

        if rel_f < 24:
            # PHASE A: HP > 35% (GREEN) -> SAVING POTIONS
            draw.rounded_rectangle(
                [W - 330, t_card_y + 16, W - 70, t_card_y + 68],
                radius=12,
                fill=(14, 165, 233),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text(
                (W - 200, t_card_y + 42),
                f"HP {int(cur_hp_ratio*100)}% (SAFE)",
                font=f_badge,
                fill=(255, 255, 255),
                anchor="mm",
            )

            rad_r = int(14 + ((rel_f % 12) / 12.0) * 28)
            draw.ellipse(
                [HP_WATCH_X - rad_r, HP_WATCH_Y - rad_r, HP_WATCH_X + rad_r, HP_WATCH_Y + rad_r],
                outline=(56, 189, 248),
                width=3,
            )
            draw.rounded_rectangle(
                [HP_WATCH_X - 150, HP_WATCH_Y - 72, HP_WATCH_X + 170, HP_WATCH_Y - 32],
                radius=10,
                fill=(15, 23, 42),
                outline=(56, 189, 248),
                width=2,
            )
            draw.text(
                (HP_WATCH_X + 10, HP_WATCH_Y - 52),
                f"HP {int(cur_hp_ratio*100)}% Green -> Saving Potion!",
                font=f_small,
                fill=(56, 189, 248),
                anchor="mm",
            )

        elif rel_f < 34:
            # PHASE B1: LOW HP (24% RED) DETECTED ON HP BAR!
            draw.rounded_rectangle(
                [W - 330, t_card_y + 16, W - 70, t_card_y + 68],
                radius=12,
                fill=(220, 38, 38),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text((W - 200, t_card_y + 42), "HP 24% LOW!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            draw.ellipse(
                [HP_WATCH_X - 26, HP_WATCH_Y - 26, HP_WATCH_X + 26, HP_WATCH_Y + 26],
                outline=(239, 68, 68),
                width=4,
            )
            draw.rounded_rectangle(
                [HP_WATCH_X - 155, HP_WATCH_Y - 74, HP_WATCH_X + 185, HP_WATCH_Y - 30],
                radius=10,
                fill=(185, 28, 28),
                outline=(250, 204, 21),
                width=2,
            )
            draw.text(
                (HP_WATCH_X + 15, HP_WATCH_Y - 52),
                "HP 24% (<35%) Red Pixel Detected!",
                font=f_small,
                fill=(255, 255, 255),
                anchor="mm",
            )

        elif rel_f < 52:
            # PHASE B2: STEP 1 -> CLICK POTION BUTTON FIRST! (while HP is still 24%)
            draw.rounded_rectangle(
                [W - 330, t_card_y + 16, W - 70, t_card_y + 68],
                radius=12,
                fill=(22, 163, 74),
                outline=(250, 204, 21),
                width=2,
            )
            draw.text((W - 200, t_card_y + 42), "1st: CLICK POTION!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            draw.ellipse(
                [HP_WATCH_X - 22, HP_WATCH_Y - 22, HP_WATCH_X + 22, HP_WATCH_Y + 22],
                outline=(250, 204, 21),
                width=4,
            )
            click_p = (rel_f - 34) / 18.0
            draw_potion_click_effect(draw, click_p, label_text="1st: CLICK POTION! (0.01s)")

        elif rel_f < 78:
            # PHASE B3: STEP 2 -> HP BAR RISES AFTER POTION CLICK (24% -> 100%) + ULTIMATE SKILL!
            draw.rounded_rectangle(
                [W - 330, t_card_y + 16, W - 70, t_card_y + 68],
                radius=12,
                fill=(16, 185, 129),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text(
                (W - 200, t_card_y + 42),
                f"2nd: HP {int(cur_hp_ratio*100)}% UP!",
                font=f_badge,
                fill=(255, 255, 255),
                anchor="mm",
            )

            rise_p = (rel_f - 52) / 26.0
            draw_hp_rising_effect(
                draw,
                cur_hp_ratio,
                rise_p,
                label_text=f"2nd: HP RISING! 24% -> {int(cur_hp_ratio*100)}% (+HEAL!)",
            )

            # Ultimate Skill Slash Beam from ULT_X, ULT_Y to Dragon Boss (starts once heal is underway)
            if rel_f >= 58:
                draw.ellipse([ULT_X - 48, ULT_Y - 48, ULT_X + 48, ULT_Y + 48], outline=(250, 204, 21), width=5)
                draw.line([(ULT_X, ULT_Y), (BOSS_X, BOSS_Y)], fill=(56, 189, 248), width=8)
                draw.line([(ULT_X, ULT_Y), (BOSS_X, BOSS_Y)], fill=(255, 255, 255), width=3)
                draw_sparkle(draw, BOSS_X, BOSS_Y, 45, color=(250, 204, 21))
                draw.rounded_rectangle(
                    [BOSS_X - 180, BOSS_Y - 40, BOSS_X + 180, BOSS_Y + 15],
                    radius=14,
                    fill=(220, 38, 38),
                    outline=(250, 204, 21),
                    width=3,
                )
                draw.text(
                    (BOSS_X, BOSS_Y - 12),
                    "CRITICAL! -9,999,999 DMG!",
                    font=f_sub,
                    fill=(255, 255, 255),
                    anchor="mm",
                )

        else:
            # PHASE C: BOSS SLAIN & MYTHIC LOOT CHEST POPUP (HP Bar stays 100% visible!)
            draw.rounded_rectangle(
                [W - 330, t_card_y + 16, W - 70, t_card_y + 68],
                radius=12,
                fill=(245, 158, 11),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text((W - 200, t_card_y + 42), "BOSS SLAIN!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            pop_w, pop_h = 540, 500
            pop_x = PX + (PW - pop_w) // 2
            pop_y = PY + 180
            draw.rounded_rectangle(
                [pop_x, pop_y, pop_x + pop_w, pop_y + pop_h],
                radius=28,
                fill=(10, 15, 28),
                outline=(250, 204, 21),
                width=4,
            )

            chest_sz = 320
            chest_img = LOOT_CHEST.resize((chest_sz, chest_sz), Image.Resampling.LANCZOS)
            canvas.paste(chest_img, (W // 2 - chest_sz // 2, pop_y + 18))

            draw.rounded_rectangle(
                [pop_x + 25, pop_y + 355, pop_x + pop_w - 25, pop_y + 415],
                radius=14,
                fill=(245, 158, 11),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text(
                (W // 2, pop_y + 385),
                "★ MYTHIC SWORD & 9,999 GEMS! ★",
                font=f_badge,
                fill=(255, 255, 255),
                anchor="mm",
            )
            draw.text(
                (W // 2, pop_y + 455),
                "INFERNO DRAGON DEFEATED (100% AFK)",
                font=f_sub,
                fill=(56, 189, 248),
                anchor="mm",
            )

            for s_i in range(8):
                random.seed(frame_idx + s_i * 19)
                sx = W // 2 + random.randint(-230, 230)
                sy = pop_y + 200 + random.randint(-170, 170)
                draw_sparkle(draw, sx, sy, random.randint(14, 24), color=(250, 204, 21))

        # Chill Robot & Speech Bubble placed in bottom margin (Y=1640..1900) BELOW the phone
        # so the HP Bar at Y=1530 is NEVER covered!
        s2_bob = int(8 * math.sin(rel_f * 0.3))
        s2_w, s2_h = 280, 280
        s2_resized = S2_IMG.resize((s2_w, s2_h), Image.Resampling.LANCZOS)
        canvas.paste(s2_resized, (20, H - s2_h - 10 + s2_bob), s2_resized)

        bx, by, bw, bh = 320, 1660, 710, 190
        draw.rounded_rectangle(
            [bx, by, bx + bw, by + bh],
            radius=26,
            fill=(255, 255, 255),
            outline=(16, 185, 129),
            width=4,
        )
        draw.text(
            (bx + bw // 2, by + 58),
            '"Clicks Potion FIRST -> HP Rises to 100%!"',
            font=f_sub,
            fill=(5, 150, 105),
            anchor="mm",
        )
        draw.text(
            (bx + bw // 2, by + 125),
            "Zero Potion Waste & Immortal AFK Boss Farming!",
            font=f_badge,
            fill=(30, 41, 59),
            anchor="mm",
        )

    # -------------------------------------------------------------
    # SCENE 5 (15.0s ~ 18.0s, Frames 450 ~ 539): Global English Outro
    # -------------------------------------------------------------
    else:
        rel_f = frame_idx - 450
        canvas = create_base_canvas()
        draw = ImageDraw.Draw(canvas)

        for s_idx in range(12):
            random.seed(s_idx * 17)
            sx = random.randint(80, W - 80)
            sy = random.randint(100, H - 200)
            sp_size = int(10 + 6 * math.sin(rel_f * 0.2 + s_idx))
            draw_sparkle(draw, sx, sy, sp_size, color=(250, 204, 21, 220))

        icon_cx = W // 2
        icon_cy = 480
        ring_r = int(135 + 8 * math.sin(rel_f * 0.25))
        draw.ellipse(
            [icon_cx - ring_r, icon_cy - ring_r, icon_cx + ring_r, icon_cy + ring_r],
            outline=(56, 189, 248),
            width=5,
        )
        draw.ellipse(
            [icon_cx - ring_r - 12, icon_cy - ring_r - 12, icon_cx + ring_r + 12, icon_cy + ring_r + 12],
            outline=(168, 85, 247),
            width=3,
        )

        icon_resized = APP_ICON.resize((230, 230), Image.Resampling.LANCZOS)
        canvas.paste(icon_resized, (icon_cx - 115, icon_cy - 115), icon_resized)

        draw.text((W // 2, 680), "Macro", font=f_huge, fill=(255, 255, 255), anchor="mm")
        draw.text(
            (W // 2, 755),
            "Smart Pixel Color Detection Auto Clicker",
            font=f_title,
            fill=(56, 189, 248),
            anchor="mm",
        )

        for star_i in range(5):
            draw_star(draw, W // 2 - 90 + star_i * 45, 825, 18, 9, color=(250, 204, 21))
        draw.text((W // 2 + 130, 825), "4.1 ★ (Google Play)", font=f_sub, fill=(226, 232, 240), anchor="lm")

        fc_y = 900
        draw.rounded_rectangle(
            [70, fc_y, W - 70, fc_y + 380],
            radius=28,
            fill=(15, 23, 42),
            outline=(56, 189, 248),
            width=2,
        )

        feats = [
            ("IF Pixel Match", "Heals & attacks ONLY when target color appears"),
            ("11x Zoom Loupe", "Pick exact HP bar / skill cooldown pixel color"),
            ("Combo Gestures", "Combine Tap + Swipe + Infinite Loop freely"),
            ("No Root Needed", "Works on all Android 7.0+ devices safely"),
        ]
        for f_i, (feat_h, feat_d) in enumerate(feats):
            fy = fc_y + 40 + f_i * 80
            draw_vector_check(draw, 105, fy + 4, size=20, color=(56, 189, 248))
            draw.text((145, fy - 2), feat_h, font=f_sub, fill=(255, 255, 255))
            draw.text((400, fy + 2), f"· {feat_d}", font=f_small, fill=(148, 163, 184))

        btn_pulse = int(8 * math.sin(rel_f * 0.3))
        bx1 = 80 - btn_pulse
        by1 = 1380 - btn_pulse
        bx2 = W - 80 + btn_pulse
        by2 = 1520 + btn_pulse
        draw.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=36,
            fill=(16, 185, 129),
            outline=(255, 255, 255),
            width=4,
        )
        draw.text(
            (W // 2, 1450),
            "Download FREE on Google Play",
            font=f_cta,
            fill=(255, 255, 255),
            anchor="mm",
        )

        draw.rounded_rectangle(
            [140, 1600, W - 140, 1690],
            radius=24,
            fill=(30, 41, 59),
            outline=(71, 85, 105),
            width=2,
        )
        draw.text(
            (W // 2, 1645),
            "Search [ Macro ] on Google Play!",
            font=f_sub,
            fill=(203, 213, 225),
            anchor="mm",
        )

    out_fpath = os.path.join(WORK_DIR, f"frame_{frame_idx:04d}.png")
    canvas.save(out_fpath, "PNG")
    if frame_idx % 90 == 0:
        print(f"Rendered {frame_idx}/{TOTAL_FRAMES} frames ({t:.1f}s)...")

print("All RPG Auto-Potion v2 frames rendered! Encoding MP4 with soundtrack...")

out_mp4 = os.path.join(DATE_DIR, "Autonomous_RPG_Auto_Potion_Pixel_Macro_EN_1080p.mp4")
cmd = [
    FFMPEG,
    "-y",
    "-framerate",
    str(FPS),
    "-i",
    os.path.join(WORK_DIR, "frame_%04d.png"),
    "-i",
    WAV_PATH,
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-shortest",
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-crf",
    "18",
    "-preset",
    "fast",
    out_mp4,
]
subprocess.run(cmd, check=True)
print(f"Successfully updated: {out_mp4}")
