import io
import base64
import requests
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ключи
RECAPTCHA_SECRET = "6LckNAwuAAAAAOtzBqHZCR0V6JBPKKkGmkNAqEfa"
RECAPTCHA_SITEKEY = "6LckNAwuAAAAAMVYUctaoMor6JPJ5_UX48tKcTli"


def sum_two_args(x, y):
    return x + y


def chessboard(arr: np.ndarray, cell_percent: float) -> np.ndarray:
    h, w, _ = arr.shape
    cell = max(1, int(round(min(h, w) * cell_percent / 100.0)))

    rows = np.arange(h)
    cols = np.arange(w)
    cell_row = rows // cell
    cell_col = cols // cell

    mask = ((cell_row[:, None] + cell_col[None, :]) % 2) == 1

    out = arr.copy()
    out[mask] = 255
    return out


def color_distribution(img: Image.Image) -> str:
    arr = np.array(img.convert("RGB"))
    fig, ax = plt.subplots(figsize=(6, 3))
    for i, c in enumerate(("r", "g", "b")):
        ax.hist(arr[:, :, i].ravel(), bins=32, color=c, alpha=0.5, label=c.upper())
    ax.set_title("Распределение цветов")
    ax.set_xlabel("Интенсивность")
    ax.set_ylabel("Частота")
    ax.legend()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@app.get("/", response_class=HTMLResponse) #для главной страницы
async def read_root(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"sitekey": RECAPTCHA_SITEKEY},
    )


@app.post("/process", response_class=HTMLResponse) #для обработки формы
async def process(
    request: Request,
    cell_percent: float = Form(10.0),
    resp: str = Form(""),
    add_watermark: str=Form("no"),
):
    # 1. проверка CAPTCHA
    payload = {"secret": RECAPTCHA_SECRET, "response": resp}
    r = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
    if not r.json().get("success"):
        print("ОТВЕТ ОТ GOOGLE:", r.json())
        raise HTTPException(status_code=400, detail="Ошибка проверки капчи")

    # 2. исходное изображение
    with Image.open("static/is1.jpg") as img:
        img = img.convert("RGB").resize((400, 400))
    arr = np.array(img)

    # 3. обработка под шахматы
    out_arr = chessboard(arr, cell_percent)
    result = Image.fromarray(out_arr)
    if add_watermark=="yes":
        draw = ImageDraw.Draw(result)
        try:
        # Указываем полный путь к шрифту Windows
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()

        text = "С. Настя"
        text_x = 20
        text_y = 340

        draw.text((text_x + 2, text_y + 2), text, font=font, fill=(0, 0, 0))
        draw.text((text_x, text_y), text, font=font, fill=(255, 0, 0))

    result.save("static/result.jpg")

    # 4. Кодируем картинки в base64
    orig_b64 = base64.b64encode(open("static/is1.jpg", "rb").read()).decode()
    res_b64 = base64.b64encode(open("static/result.jpg", "rb").read()).decode()

    # 5. графики распределения цветов
    dist_orig = color_distribution(img)
    dist_res = color_distribution(result)

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "orig": orig_b64,
            "res": res_b64,
            "dist_orig": dist_orig,
            "dist_res": dist_res,
            "cell_percent": cell_percent,
        },
    )
