import os
import sys
import asyncio
import logging
import random
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

try:
    from dotenv import load_dotenv
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.types import (
        InlineKeyboardMarkup, InlineKeyboardButton,
        ReplyKeyboardMarkup, KeyboardButton
    )
    import google.generativeai as genai
except ImportError:
    print("❌ Помилка: Не всі бібліотеки встановлені.")
    sys.exit(1)

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.INFO)

raw_keys = os.getenv("GEMINI_API_KEY")
if not raw_keys:
    print("❌ Помилка: Відсутній GEMINI_API_KEY в файлі .env")
    sys.exit(1)

API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]
print(f"✅ Завантажено {len(API_KEYS)} API ключів Google.")

current_key_index = 0

def configure_genai():
    global current_key_index
    key = API_KEYS[current_key_index]
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-flash-latest')

def rotate_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return configure_genai()

model = configure_genai()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

class AnalysisState(StatesGroup):
    waiting_for_category = State()
    waiting_for_quantity = State()

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🚀 Старт"), KeyboardButton(text="ℹ️ Про бота")],
        [KeyboardButton(text="🆘 Допомога")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_category_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📚 Книга", callback_data="category_book"),
         InlineKeyboardButton(text="🎬 Кіно", callback_data="category_movie")],
        [InlineKeyboardButton(text="☁️ Парфум", callback_data="category_perfume"),
         InlineKeyboardButton(text="🎧 Трек", callback_data="category_track")],
        [InlineKeyboardButton(text="✨ Все разом (Full Vibe)", callback_data="category_all")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quantity_keyboard():
    buttons = [[InlineKeyboardButton(text=f"{i} 🔮", callback_data=f"qty_{i}") for i in range(1, 6)]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def build_prompt(category: str, quantity: int) -> str:
    base_role = """
    Ти — елітний куратор естетики. Твоя відповідь буде відправлена в Telegram, тому ти маєш суворі технічні обмеження.
    
    🚫 КРИТИЧНО ВАЖЛИВІ ПРАВИЛА ФОРМАТУВАННЯ:
    1. ЗАБОРОНЕНО використовувати теги: <p>, <div>, <h1>, <h2>, <br>, <ul>, <li>.
    2. ДОЗВОЛЕНО тільки ці теги: <b>жирний</b>, <i>курсив</i>, <code>код</code>.
    3. Не використовуй Markdown (ніяких ** або __).
    4. Для перенесення рядка просто роби відступ (Enter).
    5. Використовуй емодзі для списків замість тегів <li>.
    """

    task_intro = f"Проаналізуй це зображення. Визнач його глибинний 'вайб'. Згенеруй добірку з {quantity} варіантів."

    specific_tasks = {
        "book": """
        Підбери <b>КНИГИ</b>.
        Формат відповіді (повтори для кожного варіанту):
        📖 <b>Назва та Автор</b>
        
        💬 <i>Чому це метч:</i> поясни зв'язок з настроєм фото.
        """,
        
        "movie": """
        Підбери <b>ФІЛЬМИ або СЕРІАЛИ</b>.
        Формат відповіді (повтори для кожного варіанту):
        🎬 <b>Назва (Рік)</b>
        
        💬 <i>Візуальний аналіз:</i> чому картинка фільму нагадує це фото.
        """,
        
        "perfume": """
        Підбери <b>НІШЕВІ ПАРФУМИ</b>.
        Формат відповіді (повтори для кожного варіанту):
        ☁️ <b>Бренд — Назва</b>
        
        🎼 <i>Ноти:</i> перелік основних нот.
        💭 <i>Асоціація:</i> опиши аромат емоційно.
        """,
        
        "track": """
        Підбери <b>МУЗИЧНІ ТРЕКИ</b>.
        Формат відповіді (повтори для кожного варіанту):
        🎧 <b>Виконавець — Назва треку</b>
        
        🎹 <i>Звучання:</i> жанр, темп, настрій.
        💭 <i>Вайб:</i> чому цей трек ідеально пасує до фото.
        """,

        "all": """
        Зроби повний розбір (Книга + Фільм + Парфум + Трек).
        Дай коротку назву цьому вайбу (наприклад: <b>Neon Noir</b>).
        
        Використовуй структуру:
        
        📖 <b>Книга:</b> Назва
        <i>Короткий опис, чому підходить.</i>
        
        🎬 <b>Кіно:</b> Назва
        <i>Короткий опис візуалу.</i>
        
        ☁️ <b>Аромат:</b> Назва
        <i>Короткий опис нот.</i>
 
        🎧 <b>Трек:</b> Назва
        <i>Вайб.</i>
        """
    }

    task_desc = specific_tasks.get(category, specific_tasks['all'])
    
    quantity_instr = f"\n\n⚠️ ВАЖЛИВО: Згенеруй рівно {quantity} різних позицій (варіантів)."
    
    prompt = f"{base_role}\n{task_intro}\nКлієнт обрав категорію: {category}.\n{task_desc}\n{quantity_instr}\n\nВідповідай українською мовою."
    return prompt

def smart_split_text(text: str, chunk_size: int = 4000) -> list[str]:
    if len(text) <= chunk_size: return [text]
    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break
        split_idx = text.rfind('\n', 0, chunk_size)
        if split_idx == -1: split_idx = chunk_size
        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip()
    return chunks

@dp.message(Command("start"))
@dp.message(F.text == "🚀 Старт")
async def start_handler(message: types.Message):
    await message.answer(
        "Привіт! Я — VibeVision 👁️.\n\n"
        "Я вмію бачити естетику на фото і підбирати под неї музику, книги та аромати.\n\n"
        "📸 **Просто надішли мені фото, щоб почати!**",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
@dp.message(F.text == "🆘 Допомога")
async def help_handler(message: types.Message):
    await message.answer(
        "🛠 **Технічна підтримка**\n\n"
        "Якщо бот працює некоректно, завис або у вас є ідеї для покращення, пишіть сюди:\n"
        "👉 @hamatum\n\n"
        "Ми на зв'язку! ⚡️",
        parse_mode="Markdown"
    )

@dp.message(F.text == "ℹ️ Про бота")
async def about_handler(message: types.Message):
    await message.answer(
        "🤖 **Про VibeVision**\n\n"
        "Цей бот використовує штучний інтелект Google Gemini для аналізу візуального контенту.\n"
        "Ми не просто розпізнаємо об'єкти, ми інтерпретуємо атмосферу (вайб) зображення.\n\n"
        "🖼 **Що надсилати:**\n"
        "- Естетичні колажі\n"
        "- Фото природи\n"
        "- Архітектуру\n"
        "- Одяг або інтер'єр\n\n"
        "Спробуй прямо зараз! 👇",
        parse_mode="Markdown"
    )

@dp.message(F.photo)
async def photo_receipt(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    await state.set_state(AnalysisState.waiting_for_category)
    await message.answer(
        "📸 Фото отримано! Що саме підібрати під цей настрій?", 
        reply_markup=get_category_keyboard()
    )

@dp.callback_query(AnalysisState.waiting_for_category)
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    selected_category = callback.data.split("_")[1]
    await state.update_data(category=selected_category)
    
    category_names = {
        "book": "Книги", "movie": "Кіно", 
        "perfume": "Парфуми", "track": "Музика", "all": "Повний вайб"
    }
    cat_display = category_names.get(selected_category, "Естетика")

    await state.set_state(AnalysisState.waiting_for_quantity)
    await callback.message.edit_text(
        f"Категорія: <b>{cat_display}</b>.\n"
        "Скільки варіантів згенерувати? (Макс 5)",
        reply_markup=get_quantity_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(AnalysisState.waiting_for_quantity)
async def process_final_generation(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    selected_qty = int(callback.data.split("_")[1])
    data = await state.get_data()
    
    status_msg = await callback.message.edit_text(
        f"⏳ <i>Аналізую вайб... Шукаю {selected_qty} варіантів...</i>", 
        parse_mode="HTML"
    )
    
    try:
        file = await bot.get_file(data['photo_id'])
        file_content = await bot.download_file(file.file_path)
        img_data = {"mime_type": "image/jpeg", "data": file_content.getvalue()}
        
        final_prompt = build_prompt(data['category'], selected_qty)
        
        global model
        response = None
        for attempt in range(len(API_KEYS)):
            try:
                response = await model.generate_content_async([final_prompt, img_data])
                break
            except Exception as e:
                error_text = str(e)
                if "429" in error_text or "400" in error_text or "403" in error_text:
                    print(f"⚠️ Ключ #{current_key_index + 1} втомився. Ротація...")
                    model = rotate_key()
                    await asyncio.sleep(1)
                else:
                    raise e

        if not response:
            await status_msg.edit_text("❌ Всі ключі вичерпано. Спробуй пізніше.")
            return

        chunks = smart_split_text(response.text)
        for i, chunk in enumerate(chunks):
            try:
                if i == 0: await status_msg.edit_text(chunk, parse_mode="HTML")
                else: await callback.message.answer(chunk, parse_mode="HTML")
            except Exception as e:
                print(f"Помилка HTML парсингу: {e}")
                if i == 0: await status_msg.edit_text(chunk, parse_mode=None)
                else: await callback.message.answer(chunk, parse_mode=None)
            await asyncio.sleep(0.3)
        
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Помилка: {e}")
    finally:
        await state.clear()

async def main():
    print("🚀 Бот запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
