import os
import re
import aiohttp
import aiofiles

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from py_yt import VideosSearch

from config import YOUTUBE_IMG_URL


# -------------------- helpers -------------------- #

def clean_text(text: str, limit: int = 45):
    text = unidecode(text)
    text = re.sub(r"\s+", " ", text)
    return text[:limit].strip()


# -------------------- main -------------------- #

async def get_thumb(videoid: str):
    cache_path = f"cache/{videoid}.png"
    os.makedirs("cache", exist_ok=True)

    if os.path.isfile(cache_path):
        return cache_path

    try:
        search = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        data = (await search.next())["result"][0]

        title = clean_text(data.get("title", "Unknown Title"))
        duration = data.get("duration", "00:00")
        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        # download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL
                img_bytes = await resp.read()

        temp_img = f"cache/temp_{videoid}.jpg"
        async with aiofiles.open(temp_img, "wb") as f:
            await f.write(img_bytes)

        # ---------------- base image ---------------- #
        base = Image.open(temp_img).convert("RGB").resize((1280, 720))

        # blurred background
        bg = base.filter(ImageFilter.GaussianBlur(22))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)

        draw = ImageDraw.Draw(bg)

        # ---------------- fonts ---------------- #
        title_font = ImageFont.truetype("assets/font.ttf", 42)
        artist_font = ImageFont.truetype("assets/font2.ttf", 28)
        small_font = ImageFont.truetype("assets/font2.ttf", 24)

        # ---------------- card ---------------- #
        card_x1, card_y1 = 120, 200
        card_x2, card_y2 = 1160, 520

        card = Image.new(
            "RGBA",
            (card_x2 - card_x1, card_y2 - card_y1),
            (15, 15, 15, 210),
        )
        bg.paste(card, (card_x1, card_y1), card)

        # ---------------- song square ---------------- #
        song_img = base.resize((240, 240))
        bg.paste(song_img, (card_x1 + 30, card_y1 + 40))

        text_x = card_x1 + 300

        # ---------------- texts ---------------- #
        draw.text(
            (text_x, card_y1 + 45),
            title,
            fill="white",
            font=title_font,
        )

        draw.text(
            (text_x, card_y1 + 100),
            "AYUSH MUSIC",
            fill="#b3b3b3",
            font=artist_font,
        )

        draw.text(
            (text_x, card_y1 + 135),
            "PLAYING",
            fill="#1db954",
            font=artist_font,
        )

        # ---------------- progress bar ---------------- #
        bar_y = card_y2 - 70

        # time labels
        draw.text(
            (card_x1 + 30, bar_y),
            "00:00",
            fill="white",
            font=small_font,
        )
        draw.text(
            (card_x2 - 90, bar_y),
            duration,
            fill="white",
            font=small_font,
        )

        bar_start = card_x1 + 95
        bar_end = card_x2 - 120

        # background bar
        draw.line(
            [(bar_start, bar_y + 14), (bar_end, bar_y + 14)],
            fill="#404040",
            width=5,
        )

        # filled part (start only – static Spotify look)
        fill_end = bar_start + int((bar_end - bar_start) * 0.18)

        draw.line(
            [(bar_start, bar_y + 14), (fill_end, bar_y + 14)],
            fill="#1db954",
            width=5,
        )

        # progress dot
        draw.ellipse(
            (fill_end - 6, bar_y + 8, fill_end + 6, bar_y + 20),
            fill="white",
        )

        # ---------------- save ---------------- #
        bg.save(cache_path)
        os.remove(temp_img)
        return cache_path

    except Exception as e:
        print("Thumbnail error:", e)
        return YOUTUBE_IMG_URL
