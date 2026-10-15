import math
import os
import random
import struct
import subprocess
import sys
import wave
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATE_DIR = os.path.join(BASE_DIR, "2026-10-15")
WORK_DIR = os.path.join(BASE_DIR, "work_timing_frames")

os.makedirs(DATE_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FPS = 30
DURATION = 18
TOTAL_FRAMES = FPS * DURATION  # 540 frames

FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"
FONT_REG = r"C:\Windows\Fonts\malgun.ttf"

f_huge = ImageFont.truetype(FONT_BOLD, 52)
f_title = ImageFont.truetype(FONT_BOLD, 34)
f_sub = ImageFont.truetype(FONT_BOLD, 22)
f_badge = ImageFont.truetype(FONT_BOLD, 20)
f_small = ImageFont.truetype(FONT_REG, 18)
f_tiny = ImageFont.truetype(FONT_BOLD, 15)
f_cta = ImageFont.truetype(FONT_BOLD, 34)

BG_PATH = os.path.join(ASSETS_DIR, "timing_strike_scene.jpg")
CHEST_PATH = os.path.join(ASSETS_DIR, "mythic_loot_chest.jpg")
APP_ICON_PATH = os.path.join(ASSETS_DIR, "01_App_Icon_512x512.png")

BG_RAW = Image.open(BG_PATH).convert("RGBA")
LOOT_CHEST = Image.open(CHEST_PATH).convert("RGBA")
APP_ICON = Image.open(APP_ICON_PATH).convert("RGBA")
S1_IMG = Image.open(os.path.join(ASSETS_DIR, "sticker_tired_finger.png")).convert("RGBA")
S2_IMG = Image.open(os.path.join(ASSETS_DIR, "sticker_chill_robot.png")).convert("RGBA")

# Phone dimensions on 1080x1920 canvas
PW, PH = 680, 1360
PX = (W - PW) // 2  # 200
PY = 265  # Phone bottom is at Y = 1625

BG_RESIZED = BG_RAW.resize((PW, PH), Image.Resampling.LANCZOS)

# Exact coordinates on 680x1360 screen & 1080x1920 canvas:
# 1) Top Boss HP Bar
SCR_BOSS_X1, SCR_BOSS_X2 = 90, 590
SCR_BOSS_Y1, SCR_BOSS_Y2 = 96, 134

# 2) Precision Timing Bar inside the clean bottom HUD panel (SCR_Y: 880..1335)
SCR_TB_X1, SCR_TB_X2 = 52, 452  # width = 400px
SCR_TB_Y1, SCR_TB_Y2 = 965, 1025  # height = 60px
TB_X1 = PX + SCR_TB_X1  # 252
TB_X2 = PX + SCR_TB_X2  # 652
TB_Y1 = PY + SCR_TB_Y1  # 1230
TB_Y2 = PY + SCR_TB_Y2  # 1290
# Center of the PERFECT Zone (ratio = 0.50 on Timing Bar):
TIMING_WATCH_X = (TB_X1 + TB_X2) // 2  # 452
TIMING_WATCH_Y = (TB_Y1 + TB_Y2) // 2  # 1260

# 3) Combo Power Gauge (Right below Timing Bar inside bottom HUD panel)
SCR_PWR_X1, SCR_PWR_X2 = 52, 452  # width = 400px
SCR_PWR_Y1, SCR_PWR_Y2 = 1145, 1190  # height = 45px
PWR_X1 = PX + SCR_PWR_X1  # 252
PWR_X2 = PX + SCR_PWR_X2  # 652
PWR_Y1 = PY + SCR_PWR_Y1  # 1410
PWR_Y2 = PY + SCR_PWR_Y2  # 1455
PWR_CENTER_X = (PWR_X1 + PWR_X2) // 2  # 452
PWR_CENTER_Y = (PWR_Y1 + PWR_Y2) // 2  # 1432

# 4) [STRIKE!] Action Button on Right side of HUD panel
SCR_STRIKE_X, SCR_STRIKE_Y = 556, 1085
STRIKE_X = PX + SCR_STRIKE_X  # 756
STRIKE_Y = PY + SCR_STRIKE_Y  # 1350

# 5) Hero Hammer & Golem Boss Centers on Canvas:
HERO_X, HERO_Y = PX + 250, PY + 420  # (450, 685)
BOSS_X, BOSS_Y = PX + 460, PY + 360  # (660, 625)


def generate_timing_soundtrack(wav_path):
    print("Generating upbeat Precision Timing soundtrack & SFX...")
    sr = 44100
    total_samples = sr * DURATION
    samples = [0.0] * total_samples

    notes = [293.66, 369.99, 440.00, 587.33, 440.00, 369.99, 329.63, 440.00]
    for i in range(total_samples):
        t = i / sr
        beat_idx = int(t * 4.5) % len(notes)
        freq = notes[beat_idx]
        val = 0.08 * math.sin(2 * math.pi * freq * t)
        val += 0.04 * math.sin(2 * math.pi * (freq * 0.5) * t)
        if (t * 4.5) % 1.0 < 0.12:
            val += 0.05 * math.sin(2 * math.pi * 110.0 * t)
        samples[i] = val

    def add_beep(start_t, freq, dur, amp=0.25, slide=0.0):
        s_idx = int(start_t * sr)
        e_idx = min(total_samples, int((start_t + dur) * sr))
        for k in range(s_idx, e_idx):
            dt = (k - s_idx) / sr
            env = math.sin(math.pi * (dt / dur))
            cur_f = freq + slide * (dt / dur)
            samples[k] += amp * env * math.sin(2 * math.pi * cur_f * dt)

    # Scene 1: Blind spam clicks & MISS failure buzzer
    for b_t in [0.4, 0.9, 1.4, 1.9]:
        add_beep(b_t, 340, 0.08, 0.22)
    add_beep(2.2, 155, 0.50, 0.35, slide=-45)

    # Scene 2: 11x Loupe lock on PERFECT -> Click STRIKE -> Combo Power Rising chime
    add_beep(4.5, 987.77, 0.12, 0.26)
    add_beep(5.6, 1174.66, 0.14, 0.30)
    add_beep(6.3, 659.25, 0.45, 0.28, slide=600)

    # Scene 3: Step chimes
    add_beep(8.0, 659.25, 0.10, 0.20)
    add_beep(9.2, 783.99, 0.12, 0.22)
    add_beep(10.3, 1046.50, 0.15, 0.24)

    # Scene 4: Moving bar hits PERFECT -> Click STRIKE -> Power Rises -> Boss Shattered!
    add_beep(12.4, 1174.66, 0.15, 0.30)
    add_beep(12.8, 1396.91, 0.15, 0.32)
    add_beep(13.3, 783.99, 0.45, 0.30, slide=650)
    add_beep(14.0, 1567.98, 0.35, 0.32)

    # Scene 5: Outro fanfare
    add_beep(15.1, 587.33, 0.15, 0.25)
    add_beep(15.3, 880.00, 0.30, 0.28)

    with wave.open(wav_path, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        raw_bytes = bytearray()
        for s in samples:
            clamped = max(-0.95, min(0.95, s))
            ival = int(clamped * 32767)
            raw_bytes.extend(struct.pack("<hh", ival, ival))
        wf.writeframes(raw_bytes)


def create_base_canvas():
    bg = BG_RAW.resize((W, H), Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(28))
    overlay = Image.new("RGBA", (W, H), (8, 12, 26, 205))
    return Image.alpha_composite(bg, overlay)


def draw_phone_frame(canvas, screen_img, border_color=(56, 189, 248), shake_x=0, shake_y=0):
    draw = ImageDraw.Draw(canvas)
    fx = PX + shake_x
    fy = PY + shake_y
    draw.rounded_rectangle(
        [fx - 12, fy - 12, fx + PW + 12, fy + PH + 12],
        radius=44,
        fill=(15, 23, 42, 255),
        outline=border_color,
        width=5,
    )
    mask = Image.new("L", (PW, PH), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([0, 0, PW, PH], radius=34, fill=255)
    canvas.paste(screen_img, (fx, fy), mask)


def draw_star(draw, cx, cy, r_out, r_in, color=(250, 204, 21)):
    pts = []
    for i in range(10):
        ang = math.radians(i * 36 - 90)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=color)


def draw_sparkle(draw, cx, cy, size, color=(250, 204, 21)):
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


def draw_timing_hud_and_bars(
    sdraw,
    needle_pos=0.50,
    power_ratio=0.25,
    boss_hp_ratio=0.95,
    is_power_rising=False,
    is_button_pressed=False,
):
    """
    Draws the complete Precision Timing Bar (MISS / GOOD / PERFECT / GOOD / MISS) + Moving Slider Needle,
    the Combo Power Gauge, the [STRIKE!] Button, and the Top Boss HP Bar onto the phone screen.
    - needle_pos: 0.0 (far left MISS) .. 0.50 (dead center PERFECT!) .. 1.0 (far right MISS)
    - PERFECT zone is needle_pos in [0.43, 0.57]
    """
    # 1. Top Boss HP Bar
    bx1, bx2, by1, by2 = SCR_BOSS_X1, SCR_BOSS_X2, SCR_BOSS_Y1, SCR_BOSS_Y2
    bw = bx2 - bx1
    boss_hp_ratio = max(0.0, min(1.0, boss_hp_ratio))
    sdraw.rounded_rectangle([bx1, by1, bx2, by2], radius=8, fill=(20, 16, 28), outline=(250, 204, 21), width=2)
    if boss_hp_ratio > 0.01:
        sdraw.rounded_rectangle([bx1 + 3, by1 + 3, bx1 + int(bw * boss_hp_ratio), by2 - 3], radius=6, fill=(220, 38, 38))
    sdraw.text(((bx1 + bx2) // 2, (by1 + by2) // 2), f"THUNDER CRYSTAL BOSS   HP {int(boss_hp_ratio * 100)}%", font=f_small, fill=(255, 255, 255), anchor="mm")

    # 2. Moving Timing Bar Header Label
    tx1, tx2, ty1, ty2 = SCR_TB_X1, SCR_TB_X2, SCR_TB_Y1, SCR_TB_Y2
    tw = tx2 - tx1
    in_perfect = 0.43 <= needle_pos <= 0.57
    in_good = (0.26 <= needle_pos < 0.43) or (0.57 < needle_pos <= 0.74)

    hdr_col = (34, 197, 94) if in_perfect else ((250, 204, 21) if in_good else (248, 113, 113))
    status_str = "★ PERFECT ZONE! ★" if in_perfect else ("GOOD ZONE" if in_good else "MISS ZONE!")
    sdraw.text((tx1 + 4, ty1 - 34), "TIMING GAUGE:", font=f_tiny, fill=(203, 213, 225))
    sdraw.text((tx2 - 4, ty1 - 34), status_str, font=f_tiny, fill=hdr_col, anchor="ra")

    # Outer frame of Timing Bar
    tb_outline = (250, 204, 21) if in_perfect else (148, 163, 184)
    sdraw.rounded_rectangle([tx1 - 3, ty1 - 3, tx2 + 3, ty2 + 3], radius=10, fill=(15, 23, 42), outline=tb_outline, width=3)

    # 5 Timing Zones inside [tx1..tx2]:
    # - Left MISS: 0.00 .. 0.26 (red)
    # - Left GOOD: 0.26 .. 0.43 (amber)
    # - Center PERFECT: 0.43 .. 0.57 (dark green when needle outside, BRIGHT NEON GREEN #22C55E when needle inside!)
    # - Right GOOD: 0.57 .. 0.74 (amber)
    # - Right MISS: 0.74 .. 1.00 (red)
    z_m1 = tx1 + int(tw * 0.26)
    z_g1 = tx1 + int(tw * 0.43)
    z_p2 = tx1 + int(tw * 0.57)
    z_g2 = tx1 + int(tw * 0.74)

    sdraw.rectangle([tx1, ty1, z_m1, ty2], fill=(153, 27, 27))
    sdraw.rectangle([z_m1, ty1, z_g1, ty2], fill=(180, 83, 9))
    perf_fill = (34, 197, 94) if in_perfect else (20, 83, 45)
    sdraw.rectangle([z_g1, ty1, z_p2, ty2], fill=perf_fill)
    sdraw.rectangle([z_p2, ty1, z_g2, ty2], fill=(180, 83, 9))
    sdraw.rectangle([z_g2, ty1, tx2, ty2], fill=(153, 27, 27))

    # Zone Dividers & Labels
    for div_x in [z_m1, z_g1, z_p2, z_g2]:
        sdraw.line([(div_x, ty1), (div_x, ty2)], fill=(255, 255, 255), width=2)
    if in_perfect:
        sdraw.rectangle([z_g1 - 1, ty1 - 2, z_p2 + 1, ty2 + 2], outline=(250, 204, 21), width=3)

    cy_tb = (ty1 + ty2) // 2
    sdraw.text(((tx1 + z_m1) // 2, cy_tb), "MISS", font=f_tiny, fill=(254, 202, 202), anchor="mm")
    sdraw.text(((z_m1 + z_g1) // 2, cy_tb), "GOOD", font=f_tiny, fill=(254, 243, 199), anchor="mm")
    p_txt_col = (15, 23, 42) if in_perfect else (134, 239, 172)
    sdraw.text(((z_g1 + z_p2) // 2, cy_tb), "PERFECT", font=f_tiny, fill=p_txt_col, anchor="mm")
    sdraw.text(((z_p2 + z_g2) // 2, cy_tb), "GOOD", font=f_tiny, fill=(254, 243, 199), anchor="mm")
    sdraw.text(((z_g2 + tx2) // 2, cy_tb), "MISS", font=f_tiny, fill=(254, 202, 202), anchor="mm")

    # Moving Timing Slider Needle (White/Gold glowing vertical bar + top/bottom triangles)
    nx = tx1 + int(tw * max(0.03, min(0.97, needle_pos)))
    needle_col = (250, 204, 21) if in_perfect else (255, 255, 255)
    sdraw.rounded_rectangle([nx - 5, ty1 - 7, nx + 5, ty2 + 7], radius=3, fill=needle_col, outline=(15, 23, 42), width=2)
    sdraw.polygon([(nx - 8, ty1 - 12), (nx + 8, ty1 - 12), (nx, ty1 - 3)], fill=needle_col)
    sdraw.polygon([(nx - 8, ty2 + 12), (nx + 8, ty2 + 12), (nx, ty2 + 3)], fill=needle_col)

    # 3. Combo Power Gauge (SCR_PWR_X1..X2 = 52..452, Y1..Y2 = 1145..1190)
    # Rises from 25% → 100% MAX right AFTER clicking the [STRIKE!] button!
    px1, px2, py1, py2 = SCR_PWR_X1, SCR_PWR_X2, SCR_PWR_Y1, SCR_PWR_Y2
    pw_bar = px2 - px1
    power_ratio = max(0.0, min(1.0, power_ratio))
    sdraw.text((px1 + 4, py1 - 28), "COMBO POWER GAUGE:", font=f_tiny, fill=(203, 213, 225))
    pwr_status = f"{int(power_ratio * 100)}% MAX!" if power_ratio >= 0.95 else f"{int(power_ratio * 100)}%"
    sdraw.text((px2 - 4, py1 - 28), pwr_status, font=f_tiny, fill=(56, 189, 248), anchor="ra")

    pwr_border = (56, 189, 248) if is_power_rising or power_ratio > 0.5 else (148, 163, 184)
    sdraw.rounded_rectangle([px1 - 3, py1 - 3, px2 + 3, py2 + 3], radius=9, fill=(15, 23, 42), outline=pwr_border, width=2)
    if power_ratio > 0.02:
        pwr_col = (16, 185, 129) if is_power_rising or power_ratio > 0.5 else (14, 165, 233)
        p_fill = int(pw_bar * power_ratio)
        sdraw.rounded_rectangle([px1, py1, px1 + p_fill, py2], radius=7, fill=pwr_col)
        if is_power_rising and p_fill < pw_bar - 2:
            edge_x = px1 + p_fill
            sdraw.rectangle([max(px1, edge_x - 8), py1, edge_x + 2, py2], fill=(250, 204, 21))
    sdraw.text(((px1 + px2) // 2, (py1 + py2) // 2), f"CRITICAL POWER  {int(power_ratio * 100)}%", font=f_small, fill=(255, 255, 255), anchor="mm")

    # 4. [STRIKE!] Action Button on Right side of HUD (SCR_STRIKE_X=556, SCR_STRIKE_Y=1085)
    sx, sy = SCR_STRIKE_X, SCR_STRIKE_Y
    btn_r = 68 if is_button_pressed else 74
    btn_bg = (22, 163, 74) if (in_perfect or is_button_pressed) else (30, 58, 138)
    btn_out = (250, 204, 21) if (in_perfect or is_button_pressed) else (56, 189, 248)
    sdraw.ellipse([sx - btn_r - 6, sy - btn_r - 6, sx + btn_r + 6, sy + btn_r + 6], fill=(15, 23, 42), outline=btn_out, width=3)
    sdraw.ellipse([sx - btn_r, sy - btn_r, sx + btn_r, sy + btn_r], fill=btn_bg, outline=(255, 255, 255), width=3)

    # Hammer/Lightning icon inside [STRIKE!] button
    sdraw.polygon(
        [(sx + 6, sy - 46), (sx - 18, sy - 10), (sx - 2, sy - 10), (sx - 10, sy + 18), (sx + 20, sy - 18), (sx + 2, sy - 18)],
        fill=(250, 204, 21),
    )
    sdraw.text((sx, sy + 36), "STRIKE!", font=f_badge, fill=(255, 255, 255), anchor="mm")


def draw_strike_click_effect(draw, progress, label_text="1st: CLICK [STRIKE!]"):
    """
    Clearly visualizes clicking the [STRIKE!] button (STRIKE_X=756, STRIKE_Y=1350) FIRST
    the exact 0.01s instant the moving bar lights up the PERFECT zone!
    """
    progress = max(0.0, min(1.0, progress))
    draw.line([(TIMING_WATCH_X, TIMING_WATCH_Y), (STRIKE_X, STRIKE_Y)], fill=(250, 204, 21), width=4)

    r1 = int(28 + progress * 55)
    r2 = int(18 + ((progress * 1.5) % 1.0) * 42)
    draw.ellipse([STRIKE_X - r1, STRIKE_Y - r1, STRIKE_X + r1, STRIKE_Y + r1], outline=(250, 204, 21), width=4)
    draw.ellipse([STRIKE_X - r2, STRIKE_Y - r2, STRIKE_X + r2, STRIKE_Y + r2], outline=(34, 197, 94), width=4)

    press_r = 24 if (int(progress * 10) % 2 == 0) else 19
    draw.ellipse(
        [STRIKE_X - press_r, STRIKE_Y - press_r, STRIKE_X + press_r, STRIKE_Y + press_r],
        fill=(34, 197, 94),
        outline=(255, 255, 255),
        width=3,
    )
    draw.text((STRIKE_X, STRIKE_Y), "TAP!", font=f_tiny, fill=(255, 255, 255), anchor="mm")

    # Callout badge directly below the STRIKE button (never touches the Timing Bar on the left!)
    draw.rounded_rectangle(
        [STRIKE_X - 102, STRIKE_Y + 84, PX + PW - 10, STRIKE_Y + 130],
        radius=12,
        fill=(22, 163, 74),
        outline=(250, 204, 21),
        width=3,
    )
    draw.text(((STRIKE_X - 102 + PX + PW - 10) // 2, STRIKE_Y + 107), label_text, font=f_small, fill=(255, 255, 255), anchor="mm")


def draw_power_rising_effect(draw, power_ratio, progress, label_text=None):
    """
    Clearly visualizes the Combo Power Gauge rising from 25% → 100% MAX
    right AFTER the [STRIKE!] button was clicked!
    """
    progress = max(0.0, min(1.0, progress))
    draw.ellipse([STRIKE_X - 30, STRIKE_Y - 30, STRIKE_X + 30, STRIKE_Y + 30], outline=(34, 197, 94), width=3)

    target_x = PWR_X1 + int((PWR_X2 - PWR_X1) * max(0.35, power_ratio))
    target_y = PWR_CENTER_Y
    draw.line([(STRIKE_X, STRIKE_Y), (target_x, target_y)], fill=(16, 185, 129), width=3)

    for orb_i in range(4):
        orb_p = (progress * 1.6 + orb_i * 0.25) % 1.0
        ox = int(STRIKE_X + (target_x - STRIKE_X) * orb_p)
        oy = int(STRIKE_Y + (target_y - STRIKE_Y) * orb_p)
        draw.ellipse([ox - 9, oy - 9, ox + 9, oy + 9], fill=(34, 197, 94), outline=(255, 255, 255), width=2)
        draw.line([(ox - 5, oy), (ox + 5, oy)], fill=(255, 255, 255), width=2)
        draw.line([(ox, oy - 5), (ox, oy + 5)], fill=(255, 255, 255), width=2)

    draw.rounded_rectangle(
        [PWR_X1 - 6, PWR_Y1 - 6, PWR_X2 + 6, PWR_Y2 + 6],
        radius=10,
        outline=(52, 211, 153),
        width=3,
    )

    if label_text is None:
        label_text = f"2nd: POWER RISES! 25% → {int(power_ratio * 100)}%"
    draw.rounded_rectangle(
        [PWR_X1, PWR_Y2 + 12, PWR_X2 + 40, PWR_Y2 + 56],
        radius=12,
        fill=(5, 150, 105),
        outline=(250, 204, 21),
        width=3,
    )
    draw.text(
        ((PWR_X1 + PWR_X2 + 40) // 2, PWR_Y2 + 34),
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


WAV_PATH = os.path.join(WORK_DIR, "timing_battle_soundtrack.wav")
generate_timing_soundtrack(WAV_PATH)

print("Starting Global English 2026-10-15 Episode (0.01s Precision Touch Timing Pixel Macro)...")

for frame_idx in range(TOTAL_FRAMES):
    t = frame_idx / FPS

    # -------------------------------------------------------------
    # SCENE 1 (0.0s ~ 3.5s, Frames 0 ~ 104):
    # Dumb Auto Clicker Disaster on a Fast-Moving Timing Bar:
    # Taps blindly while the needle is in the red MISS zone → Attack Fails & Combo Resets to 0!
    # -------------------------------------------------------------
    if frame_idx < 105:
        screen = BG_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        # Needle sweeps rapidly, and dumb auto clicker taps when needle is at 0.14 or 0.86 (Red MISS zone!)
        if frame_idx < 68:
            # Oscillate rapidly, landing in MISS zones during spam taps
            raw_wave = 0.5 + 0.44 * math.sin(frame_idx * 0.32 + 1.2)
            # Keep needle outside PERFECT during blind taps so viewer clearly sees MISS!
            if 0.40 < raw_wave < 0.60:
                needle_p = 0.16 if raw_wave < 0.50 else 0.84
            else:
                needle_p = raw_wave
            pwr_r = 0.10
        else:
            needle_p = 0.88  # Locked in Red MISS zone!
            pwr_r = 0.0

        draw_timing_hud_and_bars(sdraw, needle_pos=needle_p, power_ratio=pwr_r, boss_hp_ratio=0.98)

        if frame_idx >= 68:
            overlay = Image.new("RGBA", (PW, PH), (185, 28, 28, 95))
            screen.paste(overlay, (0, 0), overlay)
            sdraw = ImageDraw.Draw(screen)
            draw_timing_hud_and_bars(sdraw, needle_pos=0.88, power_ratio=0.0, boss_hp_ratio=0.98)
            sdraw.rounded_rectangle(
                [55, PH // 2 - 150, PW - 55, PH // 2 - 10],
                radius=20,
                fill=(15, 23, 42),
                outline=(239, 68, 68),
                width=4,
            )
            sdraw.text((PW // 2, PH // 2 - 100), "TIMING MISS!", font=f_huge, fill=(239, 68, 68), anchor="mm")
            sdraw.text(
                (PW // 2, PH // 2 - 42),
                "Tapped Outside PERFECT Zone → Combo Reset!",
                font=f_sub,
                fill=(255, 255, 255),
                anchor="mm",
            )

        shake = int(7 * math.sin(frame_idx * 1.8)) if (frame_idx % 8 < 4) else 0
        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(239, 68, 68), shake_x=shake)
        draw = ImageDraw.Draw(canvas)

        draw.rounded_rectangle([40, 40, W - 40, 220], radius=28, fill=(220, 38, 38), outline=(255, 255, 255), width=3)
        draw.text((W // 2, 95), "[DUMB AUTO CLICKER] Always Hits MISS?!", font=f_title, fill=(255, 255, 255), anchor="mm")
        draw.text(
            (W // 2, 165),
            "Taps blindly with zero timing → Misses the PERFECT zone every time!",
            font=f_sub,
            fill=(254, 226, 226),
            anchor="mm",
        )

        sx_tap = STRIKE_X + shake
        sy_tap = STRIKE_Y
        draw.ellipse([sx_tap - 44, sy_tap - 44, sx_tap + 44, sy_tap + 44], outline=(239, 68, 68), width=5)
        draw.line([(sx_tap - 26, sy_tap - 26), (sx_tap + 26, sy_tap + 26)], fill=(239, 68, 68), width=5)
        draw.line([(sx_tap + 26, sy_tap - 26), (sx_tap - 26, sy_tap + 26)], fill=(239, 68, 68), width=5)

        draw.rounded_rectangle(
            [STRIKE_X - 102, sy_tap + 84, PX + PW - 10, sy_tap + 130],
            radius=12,
            fill=(220, 38, 38),
            outline=(255, 255, 255),
            width=2,
        )
        draw.text(((STRIKE_X - 102 + PX + PW - 10) // 2, sy_tap + 107), "[MISS!] Wrong Timing!", font=f_small, fill=(255, 255, 255), anchor="mm")

        s1_bob = int(10 * math.sin(frame_idx * 0.4))
        s1_w, s1_h = 280, 280
        s1_resized = S1_IMG.resize((s1_w, s1_h), Image.Resampling.LANCZOS)
        canvas.paste(s1_resized, (W - s1_w - 20, H - s1_h - 10 + s1_bob), s1_resized)

        bx, by, bw, bh = 50, 1660, 690, 190
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=26, fill=(255, 255, 255), outline=(220, 38, 38), width=4)
        draw.text((bx + bw // 2, by + 58), '"The timing bar moves way too fast!!"', font=f_sub, fill=(185, 28, 28), anchor="mm")
        draw.text((bx + bw // 2, by + 125), "Blind tapping hits MISS → Impossible to clear!", font=f_badge, fill=(30, 41, 59), anchor="mm")

    # -------------------------------------------------------------
    # SCENE 2 (3.5s ~ 7.5s, Frames 105 ~ 224):
    # Step 1: Aim 11x Zoom Loupe at the Center [PERFECT] Timing Zone!
    # - rel_f 0..30: Needle sweeps from left (0.12) toward center PERFECT zone (0.50)
    # - rel_f 30..62: Needle hits PERFECT zone (0.50)! Center pixel turns Neon Green (#22C55E) → 11x Loupe locks on!
    # - rel_f 62..86: [1st: CLICK STRIKE!] Clicks [STRIKE!] button FIRST in 0.01s while Power is 25%!
    # - rel_f 86..119: [2nd: POWER RISES!] Right AFTER click, Combo Power Gauge rises 25% → 100% MAX!
    # -------------------------------------------------------------
    elif frame_idx < 225:
        rel_f = frame_idx - 105  # 0..119
        screen = BG_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        s2_pwr_rising = False
        s2_btn_pressed = False
        if rel_f < 30:
            needle_p = 0.12 + (rel_f / 30.0) * 0.38  # Sweeps 0.12 → 0.50 (enters PERFECT at rel_f=25)
            pwr_r = 0.25
        elif rel_f < 62:
            needle_p = 0.50  # Locked right in the center of PERFECT!
            pwr_r = 0.25
        elif rel_f < 86:
            needle_p = 0.50
            pwr_r = 0.25  # Stays at 25% while clicking [STRIKE!] FIRST!
            s2_btn_pressed = True
        else:
            needle_p = 0.50
            s2_pwr_rising = True
            pwr_r = min(1.0, 0.25 + ((rel_f - 86) / 28.0) * 0.75)  # Rises 25% → 100% AFTER click!

        draw_timing_hud_and_bars(
            sdraw,
            needle_pos=needle_p,
            power_ratio=pwr_r,
            boss_hp_ratio=0.95,
            is_power_rising=s2_pwr_rising,
            is_button_pressed=s2_btn_pressed,
        )

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(14, 165, 233))
        draw = ImageDraw.Draw(canvas)

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=False, active_tool="cond")

        draw.rounded_rectangle([40, 40, W - 40, 210], radius=28, fill=(2, 132, 199), outline=(255, 255, 255), width=3)
        draw.text((W // 2, 92), "[STEP 1: PIXEL PICKER] Aim 11x Loupe at PERFECT Zone!", font=f_title, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, 160), "Bar Hits PERFECT (#22C55E) → 1st: Click Strike → 2nd: Power Rises!", font=f_sub, fill=(224, 242, 254), anchor="mm")

        in_perf = 0.43 <= needle_p <= 0.57
        ring_col = (34, 197, 94) if in_perf else (250, 204, 21)

        # 1. Target Crosshair directly ON the center PERFECT zone (TIMING_WATCH_X=452, TIMING_WATCH_Y=1260)
        tx, ty = TIMING_WATCH_X, TIMING_WATCH_Y
        draw.ellipse([tx - 20, ty - 20, tx + 20, ty + 20], outline=(255, 255, 255), width=3)
        draw.ellipse([tx - 13, ty - 13, tx + 13, ty + 13], outline=ring_col, width=3)
        draw.line([(tx - 26, ty), (tx + 26, ty)], fill=ring_col, width=2)
        draw.line([(tx, ty - 26), (tx, ty + 26)], fill=ring_col, width=2)

        # 2. 11x Zoom Loupe placed above the bottom HUD panel (at Y=1030 on canvas) so zero bars are covered
        lx, ly = PX + 115, PY + 765
        loupe_r = 56
        draw.line([(tx, ty - 18), (lx + loupe_r - 10, ly + loupe_r - 10)], fill=ring_col, width=3)

        loupe_img = Image.new("RGBA", (loupe_r * 2, loupe_r * 2), (15, 23, 42, 255))
        ldraw = ImageDraw.Draw(loupe_img)
        cell_sz = (loupe_r * 2) // 9
        # Visualize moving needle entering the center PERFECT pixel grid inside the 11x Loupe!
        needle_grid_col = int(4 + (needle_p - 0.50) * 18)
        for gy in range(9):
            for gx in range(9):
                if 2 <= gy <= 6:
                    if abs(gx - needle_grid_col) <= 1:
                        c_fill = (250, 204, 21)  # Moving Slider Needle
                    elif 2 <= gx <= 6:
                        c_fill = (34, 197, 94) if in_perf else (20, 83, 45)  # PERFECT Zone Pixels
                    else:
                        c_fill = (180, 83, 9)  # Adjacent GOOD Zone
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
        draw.line([(lx - loupe_r - 8, ly), (lx + loupe_r + 8, ly)], fill=(255, 255, 255), width=1)
        draw.line([(lx, ly - loupe_r - 8), (lx, ly + loupe_r + 8)], fill=(255, 255, 255), width=1)
        draw.rectangle([lx - 6, ly - 6, lx + 6, ly + 6], outline=(255, 255, 255), width=2)

        draw.rounded_rectangle([lx - 86, ly - loupe_r - 32, lx + 86, ly - loupe_r - 6], radius=8, fill=(15, 23, 42), outline=ring_col, width=2)
        draw.text((lx, ly - loupe_r - 19), "11x Zoom on PERFECT", font=f_tiny, fill=(250, 204, 21), anchor="mm")

        # Floating Info Card to the right of Loupe
        card_w, card_h = 440, 124
        cx = lx + loupe_r + 18
        cy = ly - 60
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=16, fill=(15, 23, 42), outline=ring_col, width=3)

        sw_col = (34, 197, 94) if in_perf else (20, 83, 45)
        draw.rounded_rectangle([cx + 14, cy + 16, cx + 56, cy + 58], radius=8, fill=sw_col, outline=(255, 255, 255), width=2)

        if rel_f < 30:
            draw.text((cx + 68, cy + 22), "Watching Moving Timing Bar...", font=f_badge, fill=(250, 204, 21))
            draw.text((cx + 68, cy + 50), "Waiting for PERFECT Pixel (#22C55E)...", font=f_small, fill=(226, 232, 240))
            draw.rounded_rectangle([cx + 16, cy + 78, cx + card_w - 16, cy + 110], radius=10, fill=(51, 65, 85))
            draw.text((cx + card_w // 2, cy + 94), f"Target: PERFECT Zone (X {TIMING_WATCH_X}, Y {TIMING_WATCH_Y})", font=f_small, fill=(203, 213, 225), anchor="mm")
        elif rel_f < 62:
            draw.text((cx + 68, cy + 22), "PERFECT TIMING DETECTED! (0.01s)", font=f_badge, fill=(34, 197, 94))
            draw.text((cx + 68, cy + 50), f"Color: #22C55E at (X {TIMING_WATCH_X}, Y {TIMING_WATCH_Y})", font=f_small, fill=(226, 232, 240))
            draw.rounded_rectangle([cx + 16, cy + 78, cx + card_w - 16, cy + 110], radius=10, fill=(16, 185, 129), outline=(255, 255, 255), width=2)
            draw.text((cx + card_w // 2, cy + 94), "LOCKED! Bar Entered PERFECT Zone!", font=f_small, fill=(255, 255, 255), anchor="mm")
        elif rel_f < 86:
            draw.text((cx + 68, cy + 22), "STEP A: Clicking [STRIKE!] First!", font=f_badge, fill=(250, 204, 21))
            draw.text((cx + 68, cy + 50), "PERFECT Matched → Taps Strike in 0.01s!", font=f_small, fill=(226, 232, 240))
            draw.rounded_rectangle([cx + 16, cy + 78, cx + card_w - 16, cy + 110], radius=10, fill=(22, 163, 74), outline=(250, 204, 21), width=2)
            draw.text((cx + card_w // 2, cy + 94), "1st: CLICK [STRIKE!] BUTTON!", font=f_small, fill=(255, 255, 255), anchor="mm")
            draw_strike_click_effect(draw, (rel_f - 62) / 24.0, label_text="1st: CLICK [STRIKE!]")
        else:
            draw.text((cx + 68, cy + 22), f"STEP B: Power Rising! ({int(pwr_r*100)}%)", font=f_badge, fill=(34, 197, 94))
            draw.text((cx + 68, cy + 50), "Clicked → Combo Power Fills to 100%!", font=f_small, fill=(226, 232, 240))
            draw.rounded_rectangle([cx + 16, cy + 78, cx + card_w - 16, cy + 110], radius=10, fill=(5, 150, 105), outline=(255, 255, 255), width=2)
            draw.text((cx + card_w // 2, cy + 94), f"2nd: POWER RISES 25% → {int(pwr_r*100)}%!", font=f_small, fill=(255, 255, 255), anchor="mm")
            draw_power_rising_effect(draw, pwr_r, (rel_f - 86) / 28.0)

        draw.rounded_rectangle([60, 1665, W - 60, 1845], radius=24, fill=(15, 23, 42), outline=(56, 189, 248), width=3)
        draw.text((W // 2, 1720), "1. Detect PERFECT Pixel → 2. Click Strike → 3. Power Rises!", font=f_sub, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, 1785), '"Clicks [STRIKE!] FIRST in 0.01s, then Combo Power hits 100%!"', font=f_badge, fill=(56, 189, 248), anchor="mm")

    # -------------------------------------------------------------
    # SCENE 3 (7.5s ~ 11.5s, Frames 225 ~ 344):
    # Step 2: 3-Step Precision Touch Timing Macro Logic
    # -------------------------------------------------------------
    elif frame_idx < 345:
        rel_f = frame_idx - 225  # 0..119
        screen = BG_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        s3_pwr_rising = False
        s3_btn_pressed = False
        if rel_f < 40:
            s3_needle = 0.14 + (rel_f / 40.0) * 0.36  # Sweeps into PERFECT (0.50)
            s3_pwr = 0.25
            step_idx = 0
        elif rel_f < 68:
            s3_needle = 0.50
            s3_pwr = 0.25
            s3_btn_pressed = True
            step_idx = 1
        elif rel_f < 95:
            s3_needle = 0.50
            s3_pwr_rising = True
            s3_pwr = min(1.0, 0.25 + ((rel_f - 68) / 25.0) * 0.75)
            step_idx = 2
        else:
            s3_needle = 0.50
            s3_pwr = 1.0
            step_idx = 2

        draw_timing_hud_and_bars(
            sdraw,
            needle_pos=s3_needle,
            power_ratio=s3_pwr,
            boss_hp_ratio=0.85,
            is_power_rising=s3_pwr_rising,
            is_button_pressed=s3_btn_pressed,
        )

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(168, 85, 247))
        draw = ImageDraw.Draw(canvas)

        draw.rounded_rectangle([40, 40, W - 40, 210], radius=28, fill=(109, 40, 217), outline=(255, 255, 255), width=3)
        draw.text((W // 2, 92), "[STEP 2: TIMING MACRO] 0.01s Auto-Trigger Setup!", font=f_title, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, 160), "Never miss a fast timing bar again! 100% PERFECT accuracy", font=f_sub, fill=(237, 233, 254), anchor="mm")

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=False, active_tool=None)

        mc_x, mc_y, mc_w, mc_h = PX + 35, PY + 165, PW - 70, 425
        draw.rounded_rectangle([mc_x, mc_y, mc_x + mc_w, mc_y + mc_h], radius=22, fill=(15, 23, 42, 242), outline=(168, 85, 247), width=3)
        draw.text((mc_x + mc_w // 2, mc_y + 34), "[Macro #1] 0.01s Precision Touch Timing Bot", font=f_badge, fill=(250, 204, 21), anchor="mm")
        draw.line([(mc_x + 20, mc_y + 62), (mc_x + mc_w - 20, mc_y + 62)], fill=(51, 65, 85), width=2)

        steps = [
            ("1. Watch PERFECT Zone", "Detect when moving bar turns PERFECT Green (#22C55E)", (56, 189, 248)),
            ("2. Click [STRIKE!] First", "Tap [STRIKE!] button in 0.01s at exact timing!", (34, 197, 94)),
            ("3. Gauge Rises & Critical!", "Combo Power rises 25% → 100% MAX after click!", (245, 158, 11)),
        ]
        for s_i, (st_t, st_d, st_c) in enumerate(steps):
            sy = mc_y + 82 + s_i * 88
            is_active = s_i == step_idx
            bg_col = (30, 41, 59) if not is_active else (51, 65, 85)
            out_col = st_c if is_active else (71, 85, 105)
            draw.rounded_rectangle([mc_x + 20, sy, mc_x + mc_w - 20, sy + 72], radius=14, fill=bg_col, outline=out_col, width=3 if is_active else 1)
            draw.text((mc_x + 38, sy + 23), st_t, font=f_badge, fill=st_c)
            draw.text((mc_x + 38, sy + 48), st_d, font=f_small, fill=(226, 232, 240))
            if is_active:
                draw_sparkle(draw, mc_x + mc_w - 45, sy + 36, 12, color=st_c)

        draw.rounded_rectangle([mc_x + 20, mc_y + mc_h - 50, mc_x + mc_w - 20, mc_y + mc_h - 14], radius=10, fill=(88, 28, 135), outline=(168, 85, 247), width=1)
        draw.text((mc_x + mc_w // 2, mc_y + mc_h - 32), "Works on Blacksmith, Golf, Baseball, Fishing & Boss Timing Bars!", font=f_small, fill=(255, 255, 255), anchor="mm")

        if rel_f < 40:
            rad_r = int(14 + ((rel_f % 15) / 15.0) * 24)
            draw.ellipse([TIMING_WATCH_X - rad_r, TIMING_WATCH_Y - rad_r, TIMING_WATCH_X + rad_r, TIMING_WATCH_Y + rad_r], outline=(56, 189, 248), width=3)
        elif rel_f < 68:
            draw_strike_click_effect(draw, (rel_f - 40) / 28.0, label_text="1st: CLICK [STRIKE!]")
        else:
            draw_power_rising_effect(draw, s3_pwr, min(1.0, (rel_f - 68) / 27.0))

        s_title, s_desc, s_col = steps[step_idx]
        draw.rounded_rectangle([60, 1665, W - 60, 1845], radius=24, fill=(15, 23, 42), outline=s_col, width=3)
        draw.text((W // 2, 1720), f"Active Step: {s_title}", font=f_sub, fill=s_col, anchor="mm")
        draw.text((W // 2, 1785), "1. PERFECT Detected → 2. Clicks Strike FIRST → 3. Power Rises!", font=f_badge, fill=(226, 232, 240), anchor="mm")

    # -------------------------------------------------------------
    # SCENE 4 (11.5s ~ 15.0s, Frames 345 ~ 449):
    # Live Precision Timing Action:
    # - rel_f 0..24: Needle sweeps rapidly from left (0.08) toward center PERFECT zone (Macro waits patiently!)
    # - rel_f 24..34: Needle enters PERFECT zone (0.50)! Center pixel turns #22C55E Neon Green → Detected!
    # - rel_f 34..52: [1st: CLICK STRIKE!] Clicks [STRIKE!] button FIRST in 0.01s while Power is 25%!
    # - rel_f 52..78: [2nd: POWER RISES!] Right AFTER click, Combo Power rises 25% → 100% + Thunder Smash slays Boss!
    # - rel_f 78..104: PERFECT CLEAR & Victory Chest Popup!
    # -------------------------------------------------------------
    elif frame_idx < 450:
        rel_f = frame_idx - 345  # 0..104
        screen = BG_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        s4_pwr_rising = False
        s4_btn_pressed = False
        if rel_f < 24:
            # Sweeps from 0.08 → 0.42 (just before PERFECT zone)
            s4_needle = 0.08 + (rel_f / 24.0) * 0.34
            s4_pwr = 0.25
            s4_boss = 0.95
        elif rel_f < 34:
            # Enters PERFECT zone (0.50)!
            s4_needle = 0.50
            s4_pwr = 0.25
            s4_boss = 0.95
        elif rel_f < 52:
            # Clicking [STRIKE!] FIRST while locked on PERFECT!
            s4_needle = 0.50
            s4_pwr = 0.25
            s4_boss = 0.95
            s4_btn_pressed = True
        elif rel_f < 78:
            # Right AFTER click: Combo Power rises 25% → 100% MAX & Boss HP drops to 0%!
            s4_needle = 0.50
            s4_pwr_rising = True
            s4_pwr = min(1.0, 0.25 + ((rel_f - 52) / 22.0) * 0.75)
            s4_boss = max(0.0, 0.95 - ((rel_f - 52) / 24.0) * 0.95)
        else:
            s4_needle = 0.50
            s4_pwr = 1.0
            s4_boss = 0.0

        draw_timing_hud_and_bars(
            sdraw,
            needle_pos=s4_needle,
            power_ratio=s4_pwr,
            boss_hp_ratio=s4_boss,
            is_power_rising=s4_pwr_rising,
            is_button_pressed=s4_btn_pressed,
        )

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(16, 185, 129))
        draw = ImageDraw.Draw(canvas)

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=True, active_tool=None)

        draw.rounded_rectangle([40, 35, W - 40, 155], radius=24, fill=(16, 185, 129), outline=(255, 255, 255), width=3)
        draw.text((W // 2, 72), "[STEP 3: LIVE TIMING] 0.01s PERFECT Strike!", font=f_title, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, 124), "PERFECT Detected → 1st: Clicks Strike → 2nd: Power 100% MAX!", font=f_sub, fill=(209, 250, 229), anchor="mm")

        t_card_y = 168
        draw.rounded_rectangle([50, t_card_y, W - 50, t_card_y + 84], radius=18, fill=(15, 23, 42), outline=(250, 204, 21), width=2)
        draw.text((80, t_card_y + 26), f"PERFECT Zone Watch Point: (X {TIMING_WATCH_X}, Y {TIMING_WATCH_Y})", font=f_badge, fill=(250, 204, 21))
        draw.text((80, t_card_y + 56), f"Timing Reaction: 0.01s  |  Combo Power: {int(s4_pwr * 100)}%", font=f_small, fill=(255, 255, 255))

        if rel_f < 24:
            draw.rounded_rectangle([W - 340, t_card_y + 16, W - 70, t_card_y + 68], radius=12, fill=(14, 165, 233), outline=(255, 255, 255), width=2)
            draw.text((W - 205, t_card_y + 42), "TRACKING BAR...", font=f_badge, fill=(255, 255, 255), anchor="mm")

            rad_r = int(14 + ((rel_f % 12) / 12.0) * 26)
            draw.ellipse([TIMING_WATCH_X - rad_r, TIMING_WATCH_Y - rad_r, TIMING_WATCH_X + rad_r, TIMING_WATCH_Y + rad_r], outline=(56, 189, 248), width=3)
            draw.rounded_rectangle([TIMING_WATCH_X - 190, TIMING_WATCH_Y - 116, TIMING_WATCH_X + 190, TIMING_WATCH_Y - 72], radius=10, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
            draw.text((TIMING_WATCH_X, TIMING_WATCH_Y - 94), "Bar Approaching → Waiting for PERFECT!", font=f_small, fill=(56, 189, 248), anchor="mm")

        elif rel_f < 34:
            draw.rounded_rectangle([W - 340, t_card_y + 16, W - 70, t_card_y + 68], radius=12, fill=(245, 158, 11), outline=(255, 255, 255), width=2)
            draw.text((W - 205, t_card_y + 42), "PERFECT MATCH!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            draw.ellipse([TIMING_WATCH_X - 26, TIMING_WATCH_Y - 26, TIMING_WATCH_X + 26, TIMING_WATCH_Y + 26], outline=(250, 204, 21), width=4)
            draw.rounded_rectangle([TIMING_WATCH_X - 195, TIMING_WATCH_Y - 116, TIMING_WATCH_X + 195, TIMING_WATCH_Y - 72], radius=10, fill=(22, 163, 74), outline=(250, 204, 21), width=2)
            draw.text((TIMING_WATCH_X, TIMING_WATCH_Y - 94), "PERFECT Green (#22C55E) Detected in 0.01s!", font=f_small, fill=(255, 255, 255), anchor="mm")

        elif rel_f < 52:
            # 1st: CLICK [STRIKE!] BUTTON FIRST!
            draw.rounded_rectangle([W - 340, t_card_y + 16, W - 70, t_card_y + 68], radius=12, fill=(22, 163, 74), outline=(250, 204, 21), width=2)
            draw.text((W - 205, t_card_y + 42), "1st: CLICK STRIKE!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            draw.ellipse([TIMING_WATCH_X - 22, TIMING_WATCH_Y - 22, TIMING_WATCH_X + 22, TIMING_WATCH_Y + 22], outline=(250, 204, 21), width=4)
            draw_strike_click_effect(draw, (rel_f - 34) / 18.0, label_text="1st: CLICK [STRIKE!]")

        elif rel_f < 78:
            # 2nd: COMBO POWER BAR RISES AFTER CLICK + CRITICAL LIGHTNING HAMMER SMASH!
            draw.rounded_rectangle([W - 340, t_card_y + 16, W - 70, t_card_y + 68], radius=12, fill=(16, 185, 129), outline=(255, 255, 255), width=2)
            draw.text((W - 205, t_card_y + 42), f"2nd: POWER {int(s4_pwr*100)}%!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            draw_power_rising_effect(
                draw,
                s4_pwr,
                (rel_f - 52) / 26.0,
                label_text=f"2nd: POWER RISES! 25% → {int(s4_pwr*100)}%",
            )

            if rel_f >= 56:
                # Giant Lightning Critical Strike Impact on the Thunder Crystal Boss!
                draw.line([(HERO_X, HERO_Y), (BOSS_X, BOSS_Y)], fill=(250, 204, 21), width=14)
                draw.line([(HERO_X, HERO_Y), (BOSS_X, BOSS_Y)], fill=(255, 255, 255), width=5)
                draw_sparkle(draw, BOSS_X, BOSS_Y, 52, color=(250, 204, 21))
                draw.rounded_rectangle([BOSS_X - 230, BOSS_Y - 50, BOSS_X + 140, BOSS_Y + 12], radius=14, fill=(22, 163, 74), outline=(250, 204, 21), width=3)
                draw.text((BOSS_X - 45, BOSS_Y - 19), "PERFECT!! CRITICAL -9,999,999!", font=f_sub, fill=(255, 255, 255), anchor="mm")

        else:
            # PERFECT BOSS CLEAR POPUP (while keeping bottom Timing Bar & Combo Power Bar 100% visible!)
            draw.rounded_rectangle([W - 340, t_card_y + 16, W - 70, t_card_y + 68], radius=12, fill=(245, 158, 11), outline=(255, 255, 255), width=2)
            draw.text((W - 205, t_card_y + 42), "100% PERFECT!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            pop_w, pop_h = 540, 490
            pop_x = PX + (PW - pop_w) // 2
            pop_y = PY + 160
            draw.rounded_rectangle([pop_x, pop_y, pop_x + pop_w, pop_y + pop_h], radius=28, fill=(10, 15, 28), outline=(250, 204, 21), width=4)

            chest_sz = 310
            chest_img = LOOT_CHEST.resize((chest_sz, chest_sz), Image.Resampling.LANCZOS)
            canvas.paste(chest_img, (W // 2 - chest_sz // 2, pop_y + 18))

            draw.rounded_rectangle([pop_x + 25, pop_y + 345, pop_x + pop_w - 25, pop_y + 405], radius=14, fill=(16, 185, 129), outline=(255, 255, 255), width=2)
            draw.text((W // 2, pop_y + 375), "★ PERFECT TIMING COMBO x99! ★", font=f_badge, fill=(255, 255, 255), anchor="mm")
            draw.text((W // 2, pop_y + 445), "0.01s PRECISION TOUCH TIMING CLEAR!", font=f_sub, fill=(56, 189, 248), anchor="mm")

            for s_i in range(8):
                random.seed(frame_idx + s_i * 19)
                sx = W // 2 + random.randint(-230, 230)
                sy = pop_y + 200 + random.randint(-170, 170)
                draw_sparkle(draw, sx, sy, random.randint(14, 24), color=(250, 204, 21))

        # Chill Robot & Speech Bubble in bottom margin (Y=1640..1900)
        s2_bob = int(8 * math.sin(rel_f * 0.3))
        s2_w, s2_h = 280, 280
        s2_resized = S2_IMG.resize((s2_w, s2_h), Image.Resampling.LANCZOS)
        canvas.paste(s2_resized, (20, H - s2_h - 10 + s2_bob), s2_resized)

        bx, by, bw, bh = 320, 1660, 710, 190
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=26, fill=(255, 255, 255), outline=(16, 185, 129), width=4)
        draw.text((bx + bw // 2, by + 58), '"Clicks Strike FIRST → Combo Power Hits 100%!"', font=f_sub, fill=(5, 150, 105), anchor="mm")
        draw.text((bx + bw // 2, by + 125), "0.01s Pixel Detection → PERFECT Timing Every Time!", font=f_badge, fill=(30, 41, 59), anchor="mm")

    # -------------------------------------------------------------
    # SCENE 5 (15.0s ~ 18.0s, Frames 450 ~ 539): Global English Outro
    # Shows Autonomous gear icon + Official Google Play App Name: [ Macro ]
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
        draw.ellipse([icon_cx - ring_r, icon_cy - ring_r, icon_cx + ring_r, icon_cy + ring_r], outline=(56, 189, 248), width=5)
        draw.ellipse([icon_cx - ring_r - 12, icon_cy - ring_r - 12, icon_cx + ring_r + 12, icon_cy + ring_r + 12], outline=(168, 85, 247), width=3)

        icon_resized = APP_ICON.resize((230, 230), Image.Resampling.LANCZOS)
        canvas.paste(icon_resized, (icon_cx - 115, icon_cy - 115), icon_resized)

        draw.text((W // 2, 680), "Macro", font=f_huge, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, 755), "0.01s Precision Touch Timing Pixel Macro", font=f_title, fill=(56, 189, 248), anchor="mm")

        for star_i in range(5):
            draw_star(draw, W // 2 - 90 + star_i * 45, 825, 18, 9, color=(250, 204, 21))
        draw.text((W // 2 + 130, 825), "4.1 ★ (Google Play)", font=f_sub, fill=(226, 232, 240), anchor="lm")

        fc_y = 900
        draw.rounded_rectangle([70, fc_y, W - 70, fc_y + 380], radius=28, fill=(15, 23, 42), outline=(56, 189, 248), width=2)

        feats = [
            ("0.01s Timing", "Taps the exact instant the bar enters PERFECT"),
            ("11x Zoom Loupe", "Pick exact PERFECT zone pixel color (#22C55E)"),
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
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=36, fill=(16, 185, 129), outline=(255, 255, 255), width=4)
        draw.text((W // 2, 1450), "Download FREE on Google Play", font=f_cta, fill=(255, 255, 255), anchor="mm")

        draw.rounded_rectangle([140, 1600, W - 140, 1690], radius=24, fill=(30, 41, 59), outline=(71, 85, 105), width=2)
        draw.text((W // 2, 1645), "Search [ Macro ] on Google Play!", font=f_sub, fill=(203, 213, 225), anchor="mm")

    out_fpath = os.path.join(WORK_DIR, f"frame_{frame_idx:04d}.png")
    canvas.save(out_fpath, "PNG")
    if frame_idx % 90 == 0:
        print(f"Rendered {frame_idx}/{TOTAL_FRAMES} frames ({t:.1f}s)...")

print("All 2026-10-15 Precision Touch Timing frames rendered! Encoding MP4 with soundtrack...")

out_mp4 = os.path.join(DATE_DIR, "Macro_Ep02_Perfect_Touch_Timing_Pixel_Macro_EN_1080p.mp4")
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
print(f"Successfully created: {out_mp4}")
