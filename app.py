from flask import Flask, request, send_file
import barcode
from barcode.writer import ImageWriter
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import re

app = Flask(__name__)


def generate_gs1_128_binary(code: str):
    code_for_barcode = re.sub(r"[()]", "", code)

    gs1_128 = barcode.get_barcode_class("gs1_128")
    barcode_instance = gs1_128(code_for_barcode, writer=ImageWriter())

    buffer = io.BytesIO()
    barcode_instance.write(buffer, {'write_text': False})
    buffer.seek(0)

    barcode_img = Image.open(buffer)
    width, height = barcode_img.size

    new_width = int(width * 1.4)
    new_height = int(height / 1.2)
    barcode_img = barcode_img.resize((new_width, new_height), Image.LANCZOS)

    font_size = 24
    text_height = font_size + 10
    new_img = Image.new("RGB", (new_width, new_height + text_height), "white")
    new_img.paste(barcode_img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    font = ImageFont.truetype("arial.ttf", 24)

    text_width = draw.textlength(code, font=font)
    text_x = (new_width - text_width) // 2
    text_y = new_height + 5
    draw.text((text_x, text_y), code, fill="black", font=font)

    final_buffer = io.BytesIO()
    new_img.save(final_buffer, format="PNG")
    final_buffer.seek(0)

    return final_buffer


@app.route("/barcode", methods=["GET"])
def get_barcode():
    code_base64 = request.headers.get("code")

    if not code_base64:
        return {"error": "Missing 'code' parameter"}, 400

    try:
        code = base64.b64decode(code_base64).decode('utf-8')
    except Exception as e:
        return {"error": f"Invalid BASE64 encoding: {str(e)}"}, 400

    barcode_binary = generate_gs1_128_binary(code)
    return send_file(barcode_binary, mimetype="image/png", as_attachment=True, download_name="barcode.png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
