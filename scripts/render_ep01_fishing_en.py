import os
import sys
import math
import random
import subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

sys.stdout.reconfigure(line_buffering=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = r"D:\AI-Antigravity"
VIDEO_ROOT = os.path.join(BASE_DIR, "autonomous", "YDH_VIDEO")
EP_DIR = os.path.join(VIDEO_ROOT, "releases", "Ep01_Fishing_Pixel_Macro_EN")
WORK_DIR = os.path.join(VIDEO_ROOT, "work_ep01_frames")
os.makedirs(EP_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"
FONT_REG = r"C:\Windows\Fonts\malgun.ttf"

f_title = ImageFont.truetype(FONT_BOLD, 34)
f_sub = ImageFont.truetype(FONT_BOLD, 22)
f_badge = ImageFont.truetype(FONT_BOLD, 20)
f_small = ImageFont.truetype(FONT_REG, 18)
f_tiny = ImageFont.truetype(FONT_BOLD, 15)
f_cta = ImageFont.truetype(FONT_BOLD, 34)
f_huge = ImageFont.truetype(FONT_BOLD, 54)

# Assets from workspace
S1_IMG = Image.open(os.path.join(BASE_DIR, "sticker_tired_finger.png")).convert("RGBA")
S2_IMG = Image.open(os.path.join(BASE_DIR, "sticker_chill_robot.png")).convert("RGBA")
APP_ICON = Image.open(
    os.path.join(
        BASE_DIR,
        "스토어등록정보_PlayStore_Listing",
        "02_영문버전_English (en-US)",
        "02_Graphics_Images",
        "01_App_Icon_512x512.png",
    )
).convert("RGBA")
GAME_BG = Image.open(os.path.join(BASE_DIR, "fishing_game_scene.png")).convert("RGBA")
GOLDEN_FISH = Image.open(os.path.join(BASE_DIR, "golden_fish_transparent.png")).convert("RGBA")
SOUNDTRACK = os.path.join(BASE_DIR, "virtual_fishing_ad_work", "fishing_soundtrack.wav")

W, H = 1080, 1920
FPS = 30
TOTAL_FRAMES = 540  # 18 seconds

# Phone dimensions
PW, PH = 680, 1360
PX = (W - PW) // 2  # 200
PY = 320

# Resized game background
GAME_RESIZED = GAME_BG.resize((PW, PH), Image.Resampling.LANCZOS)

# Coordinate of the bobber in canvas space
BOBBER_X = PX + int(247 * (PW / 768))  # ~418
BOBBER_Y = PY + int(1036 * (PH / 1376))  # ~1343


def create_base_canvas():
    canvas = Image.new("RGB", (W, H), (11, 17, 32))
    draw = ImageDraw.Draw(canvas)
    for y in range(0, H, 4):
        t = y / H
        r = int(11 * (1 - t) + 15 * t)
        g = int(17 * (1 - t) + 23 * t)
        b = int(32 * (1 - t) + 48 * t)
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

    # 1. Run/Play
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

    # 2. Condition (Loupe)
    c2 = cx_list[1]
    is_cond = active_tool == "cond"
    if is_cond:
        hdraw.ellipse([c2 - 18, 29 - 18, c2 + 18, 29 + 18], fill=(14, 165, 233))
    hdraw.ellipse([c2 - 10, 29 - 12, c2 + 4, 29 + 2], outline=(255, 255, 255), width=2)
    hdraw.line([(c2 + 2, 29), (c2 + 10, 29 + 8)], fill=(255, 255, 255), width=3)
    hdraw.ellipse([c2 + 6, 29 - 18, c2 + 18, 29 - 6], fill=(56, 189, 248))
    hdraw.text((c2 + 12, 29 - 12), "1", font=f_tiny, fill=(15, 23, 42), anchor="mm")

    # 3. Touch
    c3 = cx_list[2]
    hdraw.ellipse([c3 - 10, 29 - 10, c3 + 10, 29 + 10], outline=(148, 163, 184), width=2)
    hdraw.ellipse([c3 - 4, 29 - 4, c3 + 4, 29 + 4], fill=(34, 197, 94))
    hdraw.ellipse([c3 + 6, 29 - 18, c3 + 18, 29 - 6], fill=(34, 197, 94))
    hdraw.text((c3 + 12, 29 - 12), "1", font=f_tiny, fill=(255, 255, 255), anchor="mm")

    # 4. Swipe
    c4 = cx_list[3]
    hdraw.line([(c4 - 10, 29), (c4 + 10, 29)], fill=(245, 158, 11), width=2)
    hdraw.polygon([(c4 + 12, 29), (c4 + 6, 25), (c4 + 6, 33)], fill=(245, 158, 11))
    hdraw.ellipse([c4 + 6, 29 - 18, c4 + 18, 29 - 6], fill=(245, 158, 11))
    hdraw.text((c4 + 12, 29 - 12), "1", font=f_tiny, fill=(255, 255, 255), anchor="mm")

    # 5. Loop
    c5 = cx_list[4]
    hdraw.arc([c5 - 10, 29 - 10, c5 + 10, 29 + 10], start=45, end=315, fill=(168, 85, 247), width=2)
    hdraw.polygon([(c5 + 9, 23), (c5 + 4, 17), (c5 + 12, 17)], fill=(168, 85, 247))

    # 6. Gear
    c6 = cx_list[5]
    hdraw.ellipse([c6 - 8, 29 - 8, c6 + 8, 29 + 8], outline=(148, 163, 184), width=2)
    hdraw.ellipse([c6 - 3, 29 - 3, c6 + 3, 29 + 3], fill=(148, 163, 184))

    # 7. Close
    c7 = cx_list[6]
    hdraw.line([(c7 - 6, 23), (c7 + 6, 35)], fill=(148, 163, 184), width=2)
    hdraw.line([(c7 + 6, 23), (c7 - 6, 35)], fill=(148, 163, 184), width=2)

    canvas.paste(hud_img, (hx, hy), hud_img)


print("Starting English Global Ep01 Fishing Pixel Macro Render...")

for frame_idx in range(TOTAL_FRAMES):
    t = frame_idx / FPS

    # -------------------------------------------------------------
    # SCENE 1 (0.0s ~ 3.5s, Frames 0 ~ 104): Dumb Auto Clicker Disaster
    # -------------------------------------------------------------
    if frame_idx < 105:
        screen = GAME_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        r_cycle = (frame_idx % 20) / 20.0
        r_radius = int(12 + r_cycle * 30)
        bx_rel = BOBBER_X - PX
        by_rel = BOBBER_Y - PY
        sdraw.ellipse(
            [
                bx_rel - r_radius,
                by_rel - r_radius * 0.4,
                bx_rel + r_radius,
                by_rel + r_radius * 0.4,
            ],
            outline=(255, 255, 255, 160),
            width=2,
        )

        shake = int(6 * math.sin(frame_idx * 1.6)) if (frame_idx % 8 < 4) else 0
        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(239, 68, 68), shake_x=shake)
        draw = ImageDraw.Draw(canvas)

        # Top Alert Banner
        draw.rounded_rectangle(
            [40, 60, W - 40, 240],
            radius=28,
            fill=(220, 38, 38),
            outline=(255, 255, 255),
            width=3,
        )
        draw.text(
            (W // 2, 115),
            "[DUMB AUTO CLICKER] Tapping Blindly?!",
            font=f_title,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 185),
            "No fish bite yet, but it keeps tapping & wastes all your bait!",
            font=f_sub,
            fill=(254, 226, 226),
            anchor="mm",
        )

        # Blind wrong clicks on phone
        random.seed(frame_idx // 6)
        rx = PX + 120 + random.randint(0, PW - 240)
        ry = PY + 300 + random.randint(0, PH - 600)
        draw.line([(rx - 25, ry - 25), (rx + 25, ry + 25)], fill=(239, 68, 68), width=5)
        draw.line([(rx + 25, ry - 25), (rx - 25, ry + 25)], fill=(239, 68, 68), width=5)

        fail_msgs = [
            "[FAIL] Missed! Bait -1",
            "[ERROR] Fish Escaped!",
            "[WARN] Wrong Timing!",
        ]
        cur_msg = fail_msgs[(frame_idx // 12) % len(fail_msgs)]
        draw.rounded_rectangle(
            [rx - 135, ry - 65, rx + 145, ry - 25],
            radius=12,
            fill=(220, 38, 38),
            outline=(255, 255, 255),
            width=2,
        )
        draw.text((rx + 5, ry - 45), cur_msg, font=f_small, fill=(255, 255, 255), anchor="mm")

        # Tired Hand
        s1_bob = int(14 * math.sin(frame_idx * 0.4))
        s1_w, s1_h = 440, 440
        s1_resized = S1_IMG.resize((s1_w, s1_h), Image.Resampling.LANCZOS)
        canvas.paste(s1_resized, (W - s1_w + 30, H - s1_h - 40 + s1_bob), s1_resized)

        if frame_idx >= 15:
            bx, by, bw, bh = 60, H - 460, 580, 160
            draw.rounded_rectangle(
                [bx, by, bx + bw, by + bh],
                radius=26,
                fill=(255, 255, 255),
                outline=(220, 38, 38),
                width=4,
            )
            draw.polygon(
                [(bx + bw - 10, by + 70), (bx + bw + 35, by + 90), (bx + bw - 10, by + 110)],
                fill=(255, 255, 255),
            )
            draw.line([(bx + bw - 10, by + 70), (bx + bw + 35, by + 90)], fill=(220, 38, 38), width=4)
            draw.line([(bx + bw + 35, by + 90), (bx + bw - 10, by + 110)], fill=(220, 38, 38), width=4)
            draw.text(
                (bx + bw // 2, by + 48),
                '"Stop tapping before the fish bites!!"',
                font=f_sub,
                fill=(185, 28, 28),
                anchor="mm",
            )
            draw.text(
                (bx + bw // 2, by + 108),
                "Lost all my rare bait & every fish ran away!",
                font=f_badge,
                fill=(30, 41, 59),
                anchor="mm",
            )

    # -------------------------------------------------------------
    # SCENE 2 (3.5s ~ 7.5s, Frames 105 ~ 224): 11x Loupe Pixel Picker
    # -------------------------------------------------------------
    elif frame_idx < 225:
        rel_f = frame_idx - 105
        screen = GAME_RESIZED.copy()

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(14, 165, 233))
        draw = ImageDraw.Draw(canvas)

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=False, active_tool="cond")

        # Top Banner
        draw.rounded_rectangle(
            [40, 60, W - 40, 220],
            radius=28,
            fill=(2, 132, 199),
            outline=(255, 255, 255),
            width=3,
        )
        draw.text(
            (W // 2, 110),
            "[STEP 1: PIXEL PICKER] 11x Zoom on the Bite Alert!",
            font=f_title,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 175),
            "Trigger ONLY when the Red '!' Pixel (#FF2A2A) appears!",
            font=f_sub,
            fill=(224, 242, 254),
            anchor="mm",
        )

        lx, ly = BOBBER_X, BOBBER_Y
        loupe_r = 75
        crop_box = (
            int((BOBBER_X - PX) * (768 / PW) - 15),
            int((BOBBER_Y - PY) * (1376 / PH) - 15),
            int((BOBBER_X - PX) * (768 / PW) + 15),
            int((BOBBER_Y - PY) * (1376 / PH) + 15),
        )
        crop_zoom = GAME_BG.crop(crop_box).resize((loupe_r * 2, loupe_r * 2), Image.Resampling.NEAREST)

        mask = Image.new("L", (loupe_r * 2, loupe_r * 2), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.ellipse([0, 0, loupe_r * 2, loupe_r * 2], fill=255)
        canvas.paste(crop_zoom, (lx - loupe_r, ly - loupe_r), mask)

        draw.ellipse([lx - loupe_r, ly - loupe_r, lx + loupe_r, ly + loupe_r], outline=(56, 189, 248), width=5)
        draw.ellipse(
            [lx - loupe_r - 4, ly - loupe_r - 4, lx + loupe_r + 4, ly + loupe_r + 4],
            outline=(250, 204, 21),
            width=2,
        )
        draw.line([(lx - loupe_r - 20, ly), (lx + loupe_r + 20, ly)], fill=(56, 189, 248), width=2)
        draw.line([(lx, ly - loupe_r - 20), (lx, ly + loupe_r + 20)], fill=(56, 189, 248), width=2)
        draw.rectangle([lx - 4, ly - 4, lx + 4, ly + 4], outline=(239, 68, 68), width=2)

        # Loupe Top Badge
        draw.rounded_rectangle(
            [lx - 95, ly - loupe_r - 40, lx + 95, ly - loupe_r - 10],
            radius=10,
            fill=(15, 23, 42),
            outline=(56, 189, 248),
            width=2,
        )
        draw.text((lx, ly - loupe_r - 25), "11x Pixel Loupe", font=f_tiny, fill=(56, 189, 248), anchor="mm")

        # Loupe Floating Info Card
        card_w, card_h = 370, 115
        cx = lx + 65
        cy = ly - 235
        draw.rounded_rectangle(
            [cx, cy, cx + card_w, cy + card_h],
            radius=16,
            fill=(15, 23, 42),
            outline=(56, 189, 248),
            width=3,
        )
        draw.rounded_rectangle(
            [cx + 15, cy + 18, cx + 55, cy + 58],
            radius=8,
            fill=(239, 68, 68),
            outline=(255, 255, 255),
            width=2,
        )
        draw.text((cx + 68, cy + 25), "Target Color: #FF2A2A ('!')", font=f_badge, fill=(250, 204, 21))
        draw.text((cx + 68, cy + 50), f"Coords: X {BOBBER_X}, Y {BOBBER_Y}", font=f_small, fill=(226, 232, 240))

        draw.rounded_rectangle(
            [cx + 20, cy + 74, cx + card_w - 20, cy + 104],
            radius=10,
            fill=(16, 185, 129),
            outline=(255, 255, 255),
            width=1,
        )
        draw.text(
            (cx + card_w // 2, cy + 89),
            "Condition #1 Saved!",
            font=f_small,
            fill=(255, 255, 255),
            anchor="mm",
        )

        # Bottom guide card
        draw.rounded_rectangle(
            [60, H - 180, W - 60, H - 70],
            radius=24,
            fill=(15, 23, 42),
            outline=(56, 189, 248),
            width=3,
        )
        draw.text(
            (W // 2, H - 142),
            "Aim with 11x Loupe -> Tap [Save Condition #1]!",
            font=f_sub,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, H - 98),
            '"Wait silently until the Red \'!\' appears on screen!"',
            font=f_small,
            fill=(148, 163, 184),
            anchor="mm",
        )

    # -------------------------------------------------------------
    # SCENE 3 (7.5s ~ 11.5s, Frames 225 ~ 344): Smart Combo Logic
    # -------------------------------------------------------------
    elif frame_idx < 345:
        rel_f = frame_idx - 225
        screen = GAME_RESIZED.copy()

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(168, 85, 247))
        draw = ImageDraw.Draw(canvas)

        draw.rounded_rectangle(
            [40, 60, W - 40, 220],
            radius=28,
            fill=(109, 40, 217),
            outline=(255, 255, 255),
            width=3,
        )
        draw.text(
            (W // 2, 110),
            "[STEP 2: SMART LOGIC] 1 Condition + 1 Tap + 1 Swipe!",
            font=f_title,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 175),
            "No blind clicking! Wait for bite -> Hook -> Reel in smoothly",
            font=f_sub,
            fill=(237, 233, 254),
            anchor="mm",
        )

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=False, active_tool=None)

        mc_x = PX + 40
        mc_y = PY + 240
        mc_w = PW - 80
        mc_h = 440
        draw.rounded_rectangle(
            [mc_x, mc_y, mc_x + mc_w, mc_y + mc_h],
            radius=22,
            fill=(15, 23, 42),
            outline=(168, 85, 247),
            width=3,
        )

        draw.text(
            (mc_x + mc_w // 2, mc_y + 35),
            "[Macro #1] Auto Fishing Master Combo",
            font=f_badge,
            fill=(250, 204, 21),
            anchor="mm",
        )
        draw.line([(mc_x + 20, mc_y + 65), (mc_x + mc_w - 20, mc_y + 65)], fill=(51, 65, 85), width=2)

        step_idx = (rel_f // 30) % 3
        steps = [
            ("1. Detect Pixel", "Scan for Red '!' (#FF2A2A) in real-time", (56, 189, 248)),
            ("2. Instant Hook", "Tap fishing rod in 0.01s upon match!", (34, 197, 94)),
            ("3. Auto Reel-In", "Swipe UP immediately to pull the fish", (245, 158, 11)),
        ]

        for s_i, (st_t, st_d, st_c) in enumerate(steps):
            sy = mc_y + 90 + s_i * 95
            is_active = s_i == step_idx
            bg_col = (30, 41, 59) if not is_active else (51, 65, 85)
            out_col = st_c if is_active else (71, 85, 105)
            draw.rounded_rectangle(
                [mc_x + 20, sy, mc_x + mc_w - 20, sy + 75],
                radius=14,
                fill=bg_col,
                outline=out_col,
                width=3 if is_active else 1,
            )

            draw.text((mc_x + 40, sy + 25), st_t, font=f_badge, fill=st_c)
            draw.text((mc_x + 40, sy + 50), st_d, font=f_small, fill=(226, 232, 240))
            if is_active:
                draw_sparkle(draw, mc_x + mc_w - 45, sy + 38, 12, color=st_c)

        draw.rounded_rectangle(
            [mc_x + 20, mc_y + mc_h - 55, mc_x + mc_w - 20, mc_y + mc_h - 15],
            radius=10,
            fill=(88, 28, 135),
            outline=(168, 85, 247),
            width=1,
        )
        draw.text(
            (mc_x + mc_w // 2, mc_y + mc_h - 35),
            "Infinite Auto-Loop: Cast & Catch 24/7 AFK!",
            font=f_small,
            fill=(255, 255, 255),
            anchor="mm",
        )

        s_title, s_desc, s_col = steps[step_idx]
        draw.rounded_rectangle(
            [60, H - 200, W - 60, H - 70],
            radius=24,
            fill=(15, 23, 42),
            outline=s_col,
            width=3,
        )
        draw.text((W // 2, H - 155), f"Active Step: {s_title}", font=f_sub, fill=s_col, anchor="mm")
        draw.text(
            (W // 2, H - 105),
            "Never taps unless the pixel color matches! (0% Misfire)",
            font=f_small,
            fill=(226, 232, 240),
            anchor="mm",
        )

    # -------------------------------------------------------------
    # SCENE 4 (11.5s ~ 15.0s, Frames 345 ~ 449): Live Run -> Legendary Catch!
    # -------------------------------------------------------------
    elif frame_idx < 450:
        rel_f = frame_idx - 345
        screen = GAME_RESIZED.copy()
        sdraw = ImageDraw.Draw(screen)

        bx_rel = BOBBER_X - PX
        by_rel = BOBBER_Y - PY

        r_cycle = (frame_idx % 24) / 24.0
        r_radius = int(14 + r_cycle * 36)
        sdraw.ellipse(
            [
                bx_rel - r_radius,
                by_rel - r_radius * 0.4,
                bx_rel + r_radius,
                by_rel + r_radius * 0.4,
            ],
            outline=(255, 255, 255, 180),
            width=2,
        )

        canvas = create_base_canvas()
        draw_phone_frame(canvas, screen, border_color=(16, 185, 129))
        draw = ImageDraw.Draw(canvas)

        draw_autonomous_hud(canvas, PX + 120, PY + 25, is_running=True, active_tool=None)

        # Top Banner
        draw.rounded_rectangle(
            [40, 50, W - 40, 190],
            radius=26,
            fill=(16, 185, 129),
            outline=(255, 255, 255),
            width=3,
        )
        draw.text(
            (W // 2, 95),
            "[STEP 3: LIVE ACTION] Instant 0.01s Hook -> JACKPOT!!",
            font=f_title,
            fill=(255, 255, 255),
            anchor="mm",
        )
        draw.text(
            (W // 2, 150),
            "Autonomous watches the screen 24/7 & strikes at the exact millisecond!",
            font=f_sub,
            fill=(209, 250, 229),
            anchor="mm",
        )

        t_card_y = 205
        draw.rounded_rectangle(
            [50, t_card_y, W - 50, t_card_y + 110],
            radius=20,
            fill=(15, 23, 42),
            outline=(250, 204, 21),
            width=3,
        )

        draw.rounded_rectangle(
            [75, t_card_y + 15, 155, t_card_y + 95],
            radius=14,
            fill=(239, 68, 68),
            outline=(255, 255, 255),
            width=2,
        )
        draw.text((115, t_card_y + 55), "!", font=f_huge, fill=(255, 255, 255), anchor="mm")

        draw.text((175, t_card_y + 22), "Watch Target: Bite Alert '!'", font=f_badge, fill=(250, 204, 21))
        draw.text((175, t_card_y + 48), f"Position: X {BOBBER_X}, Y {BOBBER_Y}", font=f_small, fill=(255, 255, 255))
        draw.text(
            (175, t_card_y + 75),
            "Color: #FF2A2A (Tap on Match)",
            font=f_small,
            fill=(248, 113, 113),
        )

        tx, ty = BOBBER_X, BOBBER_Y

        if rel_f < 45:
            # PHASE A: WAITING
            draw.rounded_rectangle(
                [W - 330, t_card_y + 25, W - 70, t_card_y + 85],
                radius=14,
                fill=(245, 158, 11),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text((W - 200, t_card_y + 55), "SCANNING...", font=f_badge, fill=(255, 255, 255), anchor="mm")

            rad_cycle = (rel_f % 18) / 18.0
            rad_r = int(20 + rad_cycle * 50)
            draw.ellipse([tx - 40, ty - 40, tx + 40, ty + 40], outline=(245, 158, 11), width=3)
            draw.ellipse([tx - rad_r, ty - rad_r, tx + rad_r, ty + rad_r], outline=(245, 158, 11), width=2)

            draw.rounded_rectangle(
                [tx - 190, ty - 90, tx + 60, ty - 50],
                radius=10,
                fill=(15, 23, 42),
                outline=(245, 158, 11),
                width=2,
            )
            draw.text(
                (tx - 65, ty - 70),
                "Waiting for Bite (No Tap)",
                font=f_small,
                fill=(245, 158, 11),
                anchor="mm",
            )

        elif rel_f < 70:
            # PHASE B: BITE & INSTANT TAP
            draw.rounded_rectangle(
                [W - 330, t_card_y + 25, W - 70, t_card_y + 85],
                radius=14,
                fill=(16, 185, 129),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text((W - 200, t_card_y + 55), "MATCH! STRIKE!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            ex_y = ty - 80 + int(6 * math.sin((rel_f - 45) * 0.8))
            draw.ellipse(
                [tx - 28, ex_y - 28, tx + 28, ex_y + 28],
                fill=(239, 68, 68),
                outline=(255, 255, 255),
                width=3,
            )
            draw.text((tx, ex_y), "!", font=f_title, fill=(255, 255, 255), anchor="mm")

            tap_p = (rel_f - 45) / 25.0
            r_tap = int(25 + tap_p * 70)
            draw.ellipse([tx - r_tap, ty - r_tap, tx + r_tap, ty + r_tap], outline=(34, 197, 94), width=5)
            draw.ellipse([tx - 35, ty - 35, tx + 35, ty + 35], outline=(250, 204, 21), width=3)
            draw_sparkle(draw, tx, ty - 45, 16, color=(250, 204, 21))

            draw.rounded_rectangle(
                [tx - 210, ty - 130, tx + 60, ty - 90],
                radius=10,
                fill=(15, 23, 42),
                outline=(34, 197, 94),
                width=2,
            )
            draw.text(
                (tx - 75, ty - 110),
                "MATCH! 0.01s Instant Tap!",
                font=f_small,
                fill=(34, 197, 94),
                anchor="mm",
            )

            sw_x = tx + 100
            sw_y1 = ty - 20
            sw_y2 = ty - 220
            draw.line([(sw_x, sw_y1), (sw_x, sw_y2)], fill=(56, 189, 248), width=6)
            draw.polygon(
                [(sw_x, sw_y2 - 20), (sw_x - 18, sw_y2 + 10), (sw_x + 18, sw_y2 + 10)],
                fill=(56, 189, 248),
            )
            draw.text((sw_x + 25, (sw_y1 + sw_y2) // 2), "Swipe Reel-In", font=f_small, fill=(56, 189, 248))

        else:
            # PHASE C: GOLDEN FISH JUMP!!
            draw.rounded_rectangle(
                [W - 330, t_card_y + 25, W - 70, t_card_y + 85],
                radius=14,
                fill=(245, 158, 11),
                outline=(255, 255, 255),
                width=2,
            )
            draw.text((W - 200, t_card_y + 55), "PERFECT CATCH!", font=f_badge, fill=(255, 255, 255), anchor="mm")

            jump_p = (rel_f - 70) / 35.0
            fish_w, fish_h = 360, 360
            fish_resized = GOLDEN_FISH.resize((fish_w, fish_h), Image.Resampling.LANCZOS)

            fish_cx = tx + int(jump_p * 120)
            fish_cy = ty - 100 - int(math.sin(jump_p * math.pi) * 220)

            canvas.paste(fish_resized, (fish_cx - fish_w // 2, fish_cy - fish_h // 2), fish_resized)

            for s_i in range(8):
                random.seed(frame_idx + s_i * 13)
                sx = fish_cx + random.randint(-180, 180)
                sy = fish_cy + random.randint(-180, 180)
                draw_sparkle(draw, sx, sy, random.randint(12, 22), color=(250, 204, 21))

            draw.rounded_rectangle(
                [PX + 50, PY + 120, PX + PW - 50, PY + 200],
                radius=18,
                fill=(245, 158, 11),
                outline=(255, 255, 255),
                width=3,
            )
            draw.text(
                (PX + PW // 2, PY + 160),
                "★ LEGENDARY GOLDEN FISH CAUGHT! ★",
                font=f_badge,
                fill=(255, 255, 255),
                anchor="mm",
            )

        # Chill Robot on bottom left
        s2_bob = int(10 * math.sin(rel_f * 0.3))
        s2_w, s2_h = 440, 440
        s2_resized = S2_IMG.resize((s2_w, s2_h), Image.Resampling.LANCZOS)
        s2_pos = (15, H - s2_h - 20 + s2_bob)
        canvas.paste(s2_resized, s2_pos, s2_resized)

        bx, by, bw, bh = 400, H - 460, 640, 160
        draw.rounded_rectangle(
            [bx, by, bx + bw, by + bh],
            radius=26,
            fill=(255, 255, 255),
            outline=(16, 185, 129),
            width=4,
        )
        draw.polygon([(bx, by + 60), (bx - 28, by + 85), (bx, by + 105)], fill=(255, 255, 255))
        draw.line([(bx, by + 60), (bx - 28, by + 85)], fill=(16, 185, 129), width=4)
        draw.line([(bx - 28, by + 85), (bx, by + 105)], fill=(16, 185, 129), width=4)

        draw.text(
            (bx + bw // 2, by + 45),
            '"I just chilled on the couch & caught 100 fish!"',
            font=f_sub,
            fill=(5, 150, 105),
            anchor="mm",
        )
        draw.text(
            (bx + bw // 2, by + 105),
            "0.01s Pixel Detection = 100% AFK Farming!",
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

        draw.text((W // 2, 680), "Autonomous", font=f_huge, fill=(255, 255, 255), anchor="mm")
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
            ("IF Pixel Match", "Taps ONLY when target color appears (0% Error)"),
            ("11x Zoom Loupe", "Pick exact screen pixel color & coordinates"),
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
            'Search [ Autonomous ] on Google Play!',
            font=f_sub,
            fill=(203, 213, 225),
            anchor="mm",
        )

    out_fpath = os.path.join(WORK_DIR, f"frame_{frame_idx:04d}.png")
    canvas.save(out_fpath, "PNG")
    if frame_idx % 90 == 0:
        print(f"Rendered {frame_idx}/{TOTAL_FRAMES} frames ({t:.1f}s)...")

print("All English frames rendered! Encoding MP4 with soundtrack...")

out_mp4 = os.path.join(EP_DIR, "Autonomous_Ep01_Fishing_Pixel_Macro_EN_1080p.mp4")
cmd = [
    FFMPEG,
    "-y",
    "-framerate",
    str(FPS),
    "-i",
    os.path.join(WORK_DIR, "frame_%04d.png"),
]
if os.path.exists(SOUNDTRACK):
    cmd += ["-i", SOUNDTRACK, "-c:a", "aac", "-b:a", "192k", "-shortest"]
cmd += [
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
