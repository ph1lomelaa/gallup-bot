from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio
import gspread
import pandas as pd
from aiogram.utils.keyboard import InlineKeyboardBuilder
from google.oauth2.service_account import Credentials
from aiogram.types import FSInputFile
import os, json, base64
from PIL import Image, ImageDraw, ImageFont

# === Настройки бота ===
API_TOKEN = "8378609723:AAGKdgqccbf1UDcIqjTewWTc6it3jc9fQqA"
SHEET_ID = "11ZYmnqfluiIXmTpQ5Ppg5vNy4lat8xYEeZCUaw-ZaNE"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# === Авторизация Google ===
def load_service_account_credentials():
    b64 = os.getenv("GOOGLE_CREDS_B64")
    raw = os.getenv("GOOGLE_CREDS_JSON")
    if b64:
        data = base64.b64decode(b64).decode("utf-8")
        info = json.loads(data)
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    if raw:
        info = json.loads(raw)
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    raise RuntimeError("Service account creds not provided")

creds = load_service_account_credentials()
gc = gspread.authorize(creds)

# === Настройка aiogram ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === Функция отрисовки карты StrengthsFinder ===
def draw_strengths_chart(name, ranked_list):
    background_path = "Your CliftonStrengths by Domain.png"
    output_path = f"{name}.png"

    # Цвета
    COLOR_EXECUTING_MAIN = "#7a2483"
    COLOR_EXECUTING_FADE = "#eadcea"
    COLOR_INFLUENCING_MAIN = "#f5c89f"
    COLOR_INFLUENCING_FADE = "#fdf1e8"
    COLOR_RELATIONSHIP_MAIN = "#aebfe9"
    COLOR_RELATIONSHIP_FADE = "#d8e2f4"
    COLOR_STRATEGIC_MAIN = "#bfe1d4"
    COLOR_STRATEGIC_FADE = "#e3f1eb"
    TEXT_COLOR = "#000000"
    TEXT_WHITE = "#ffffff"

    # Шрифт
    FONT_PATH = os.path.join(os.path.dirname(__file__), "ArialMdm.ttf")
    def load_font(size):
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except:
            print("⚠️ Файл шрифта не найден, используем стандартный")
            return ImageFont.load_default()
    font_name = load_font(14)
    font_num_big = load_font(33)
    font_num_small = load_font(21)
    font_header = load_font(36)

    # Координаты блоков
    executing_blocks = [
        ("Achiever", 6.7, 190, 151.6, 127),
        ("Discipline", 165.1, 190, 151.6, 127),
        ("Arranger", 6.7, 322, 151.6, 127),
        ("Focus", 165.1, 322, 151.6, 127),
        ("Belief", 6.7, 454.1, 151.6, 127),
        ("Responsibility", 165.1, 454.1, 151.6, 127),
        ("Consistency", 6.7, 586.1, 151.6, 127),
        ("Restorative", 165.1, 586.1, 151.6, 127),
        ("Deliberative", 6.7, 718.1, 151.6, 127),
    ]
    influencing_blocks = [
        ("Activator", 325.2, 190, 151.6, 127),
        ("Maximizer", 483.9, 190, 151.6, 127),
        ("Command", 323.2, 322, 151.6, 127),
        ("Self-Assurance", 483.9, 322, 151.6, 127),
        ("Communication", 323.2, 454.1, 151.6, 127),
        ("Significance", 482.6, 454.1, 151.6, 127),
        ("Competition", 323.8, 586.1, 151.6, 127),
        ("Woo", 482.6, 586.1, 151.6, 127),
    ]
    relationship_blocks = [
        ("Adaptability", 644.6, 190, 151.6, 127),
        ("Includer", 802.6, 190, 151.6, 127),
        ("Connectedness", 645, 322, 151.6, 127),
        ("Individualization", 802.6, 322, 151.6, 127),
        ("Developer", 642.3, 454.1, 151.6, 127),
        ("Positivity", 801.9, 454.1, 151.6, 127),
        ("Empathy", 642.3, 588.6, 151.6, 127),
        ("Relator", 802.6, 591.1, 151.6, 127),
        ("Harmony", 640, 723.1, 151.6, 127),
    ]
    strategic_blocks = [
        ("Analytical", 963.3, 190, 151.6, 127),
        ("Input", 1120.9, 190, 151.6, 127),
        ("Context", 960.3, 322, 151.6, 127),
        ("Intellection", 1120.9, 322, 151.6, 127),
        ("Futuristic", 961.6, 454.1, 151.6, 127),
        ("Learner", 1121.2, 454.1, 151.6, 127),
        ("Ideation", 961.6, 588.6, 151.6, 127),
        ("Strategic", 1119.7, 588.6, 151.6, 127),
    ]

    # Создание изображения
    img = Image.open(background_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Имя участника
    bbox = draw.textbbox((0, 0), name, font=font_header)
    text_w = bbox[2] - bbox[0]
    x_pos = img.width - text_w - 85
    draw.text((x_pos, 40), name, fill="#333333", font=font_header)

    # Отрисовка блоков
    def draw_blocks(blocks, main_color, fade_color, col_index):
        for theme, x, y, w, h in blocks:
            rank = ranked_list.index(theme) + 1 if theme in ranked_list else None
            if not rank: continue
            is_top10 = rank <= 10
            color = main_color if is_top10 else fade_color
            draw.rectangle([x, y, x + w, y + h], fill=color, outline="#fff", width=2)
            text_color = TEXT_WHITE if (is_top10 and col_index <= 3) else TEXT_COLOR
            font_num = font_num_big if is_top10 else font_num_small
            num_text = str(rank)
            bbox = draw.textbbox((0, 0), num_text, font=font_num)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text((x+(w-tw)/2, y+(h-th)/2-10), num_text, fill=text_color, font=font_num)
            bbox = draw.textbbox((0, 0), theme, font=font_name)
            nw, nh = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text((x+(w-nw)/2, y+h-nh-25), theme, fill=text_color, font=font_name)

    draw_blocks(executing_blocks, COLOR_EXECUTING_MAIN, COLOR_EXECUTING_FADE, 1)
    draw_blocks(influencing_blocks, COLOR_INFLUENCING_MAIN, COLOR_INFLUENCING_FADE, 2)
    draw_blocks(relationship_blocks, COLOR_RELATIONSHIP_MAIN, COLOR_RELATIONSHIP_FADE, 3)
    draw_blocks(strategic_blocks, COLOR_STRATEGIC_MAIN, COLOR_STRATEGIC_FADE, 4)

    img.save(output_path)
    return output_path

# === Расчёт StrengthsFinder ===
def calculate_strengths():
    sheet_data = gc.open_by_key(SHEET_ID)
    form = pd.DataFrame(sheet_data.worksheet("Form_Responses").get_all_records())
    map_df = pd.DataFrame(sheet_data.worksheet("Map").get_all_records())

    q_columns = [c for c in form.columns if c.startswith("Q")]
    themes = sorted(list(set(map_df["Качество_А"]) | set(map_df["Качество_Б"])))

    results = []
    for _, row in form.iterrows():
        scores = {t: 0 for t in themes}
        for q in q_columns:
            qnum = q.replace("Q", "")
            if not qnum.isdigit(): continue
            try:
                pair = map_df.loc[map_df["№"] == int(qnum)].iloc[0]
            except IndexError:
                continue
            left, right = pair["Качество_А"], pair["Качество_Б"]
            try:
                val = int(row[q])
            except:
                continue
            if val <= 2: scores[left] += (3 - val)
            elif val >= 4: scores[right] += (val - 3)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results.append({"Имя": row["Как вас зовут?"], **{t: r+1 for r, (t, _) in enumerate(ranked)}})
    return pd.DataFrame(results)

# === Команда /start ===
@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Список прошедших тест", callback_data="show_list")
    builder.button(text="🔍 Поиск по имени", callback_data="search_name")
    builder.adjust(1)
    await message.answer(
        f"🕌 Ассаляму алейкум, {message.from_user.first_name}!\n\n"
        "Я бот *Gallup Hickmet*.\nВыберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# === Показ списка имён ===
@dp.callback_query(F.data == "show_list")
async def show_list(callback: types.CallbackQuery):
    df = calculate_strengths()
    names = sorted(df["Имя"].dropna().unique())
    builder = InlineKeyboardBuilder()
    for n in names:
        builder.button(text=n, callback_data=f"show_{n}")
    builder.button(text="⬅️ Назад", callback_data="back_to_start")  # добавлена кнопка внизу
    builder.adjust(2)
    await callback.message.answer("👥 Выберите участника:", reply_markup=builder.as_markup())

# === Назад в начало ===
@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery):
    await start(callback.message)
    
# === Показ результатов ===
@dp.callback_query(F.data.startswith("show_"))
async def show_result(callback: types.CallbackQuery):
    name = callback.data.replace("show_", "")
    df = calculate_strengths()
    row = df[df["Имя"] == name].iloc[0]
    all_themes = sorted([(k, v) for k, v in row.items() if k != "Имя"], key=lambda x: x[1])
    ranked_list = [t[0] for t in all_themes]
    chart_path = draw_strengths_chart(name, ranked_list)
    top10 = all_themes[:10]
    text = f"📊 *Результаты StrengthsFinder для {name}:*\n\n" + "\n".join([f"{i+1}. {t[0]}" for i, t in enumerate(top10)])
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="show_list")
    photo = FSInputFile(chart_path)
    await callback.message.answer_photo(photo=photo, caption=text, parse_mode="Markdown", reply_markup=builder.as_markup())

# === Поиск по имени ===
@dp.callback_query(F.data == "search_name")
async def ask_name(callback: types.CallbackQuery):
    await callback.message.answer("Введите имя участника:")

@dp.message()
async def manual_search(message: types.Message):
    query = message.text.strip().lower()
    df = calculate_strengths()
    row = df[df["Имя"].str.lower().str.contains(query, na=False)]
    if row.empty:
        await message.answer("❌ Участник не найден. Попробуйте снова.")
        return
    for _, r in row.iterrows():
        all_themes = sorted([(k, v) for k, v in r.items() if k != "Имя"], key=lambda x: x[1])
        ranked_list = [t[0] for t in all_themes]
        chart_path = draw_strengths_chart(r["Имя"], ranked_list)
        top10 = all_themes[:10]
        text = f"📊 *Результаты StrengthsFinder для {r['Имя']}:*\n\n" + "\n".join([f"{i+1}. {t[0]}" for i, t in enumerate(top10)])
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data="show_list")
        photo = FSInputFile(chart_path)
        await message.answer_photo(photo=photo, caption=text, parse_mode="Markdown", reply_markup=builder.as_markup())

# === Запуск ===
async def main():
    print("🤖 Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
