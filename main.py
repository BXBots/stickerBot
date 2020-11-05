import os
import asyncio
import secrets
import logging
import configparser
from textwrap import wrap
from pyrogram import Client, idle, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont, ImageChops

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger(__name__)

app_config = configparser.ConfigParser()
app_config.read("config.ini")
bot_api_key = app_config.get("bot-configuration", "api_key")

some_sticker_bot = Client(
    session_name="some_sticker_bot",
    bot_token=bot_api_key,
    workers=200
)


async def get_y_and_heights(text_wrapped, dimensions, margin, font):
    ascent, descent = font.getmetrics()
    line_heights = [font.getmask(text_line).getbbox()[3] + descent + margin for text_line in text_wrapped]
    line_heights[-1] -= margin
    height_text = sum(line_heights)
    y = (dimensions[1] - height_text) // 2
    return y, line_heights


async def crop_to_circle(im):
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, im.split()[-1])
    im.putalpha(mask)


@some_sticker_bot.on_message(filters.text)
async def create_sticker_handler(c: Client, m: Message):
    font = ImageFont.truetype("TitilliumWeb-Regular.ttf", 34)

    img = Image.new("RGBA", (512, 512), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    text_lines = wrap(m.text, 30)

    y, line_heights = await get_y_and_heights(
        text_lines,
        (512, 512),
        10,
        font
    )

    user_profile_pic = await c.get_profile_photos(m.from_user.id)
    photo = await c.download_media(user_profile_pic[0].file_id, file_ref=user_profile_pic[0].file_ref)
    im = Image.open(photo).convert("RGBA")
    im.thumbnail((60, 60))
    await crop_to_circle(im)
    img.paste(im, (30, y))

    for i, line in enumerate(text_lines):
        x = 100
        draw.text((x, y), line, (0, 0, 0), font=font)
        draw.text((x, y), line, (0, 0, 0), font=font)
        y += line_heights[i]

    sticker_file = f"{secrets.token_hex(2)}.webp"

    img.save(sticker_file)

    await m.reply_sticker(
        sticker=sticker_file
    )

    try:
        if os.path.isfile(sticker_file):
            os.remove(sticker_file)

        if os.path.isfile(photo):
            os.remove(photo)
    except Exception as e:
        logging.error(e)


async def main():
    await some_sticker_bot.start()
    await idle()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())