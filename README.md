# 👁️✨ VibeVision Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI](https://img.shields.io/badge/AI-Google_Gemini-orange)
![Telegram](https://img.shields.io/badge/Interface-Aiogram_3-blue)
![Aesthetics](https://img.shields.io/badge/Vibe-Curator-purple)

A Telegram bot that acts as an **elite aesthetic curator**. Send it a photo, and it analyzes the deep "vibe" to recommend perfectly matching books, movies, niche perfumes, and music tracks.

The bot uses Google's Gemini Vision API to understand mood, lighting, colors, and context, translating visual data into curated lifestyle recommendations.

---

## 🚀 Features

* **🖼️ Deep Visual Analysis:** Goes beyond basic object recognition to understand the atmosphere, emotion, and aesthetic of any uploaded image.
* **🎭 Smart Categorization:** Generates curated picks across 4 distinct categories:
    * 📚 **Books:** Title, author, and thematic match.
    * 🎬 **Movies/TV:** Title, release year, and visual style comparison.
    * ☁️ **Niche Perfumes:** Brand, name, fragrance notes, and emotional association.
    * 🎧 **Music Tracks:** Artist, track name, genre, tempo, and sonic vibe.
    * ✨ **Full Vibe:** A complete mix of all the above with a unique aesthetic title (e.g., *Neon Noir*).
* **🔄 Multi-Key Rotation System:** Built-in API key load balancer. Automatically switches between multiple Gemini API keys to bypass free-tier rate limits (429 errors) and ensure 100% uptime.
* **⚡ Fully Asynchronous:** Built on `aiogram 3.x`, handling multiple users concurrently without blocking the main thread.
* **📝 Graceful Formatting:** Strict Markdown/HTML parsing with fallback mechanisms to ensure messages are always delivered beautifully in Telegram.

---

## 🛠️ Tech Stack & Architecture

The processing pipeline is designed for speed and stability:

1.  **Input:** User sends a photo via Telegram (`aiogram`).
2.  **State Management:** FSM (Finite State Machine) captures the user's desired category and quantity.
3.  **In-Memory Processing:** The image is downloaded to RAM (not saved to disk) for fast processing and optimal cloud deployment.
4.  **AI Generation (`google-generativeai`):**
    * A highly structured prompt forces the LLM to output specific formatting.
    * The image bytes are passed to the `gemini-flash-latest` model.
    * If a rate limit is hit, the `rotate_key()` function hot-swaps the API key and retries seamlessly.
5.  **Output:** Long responses are smartly chunked (keeping formatting intact) and sent back to the user.

---

## ⚙️ Installation

### Prerequisites
* **Python 3.10+**
* A Telegram Bot Token from [@BotFather](https://t.me/botfather).
* One or more API keys from [Google AI Studio](https://aistudio.google.com/).

### Steps

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/VibeVision.git](https://github.com/YOUR_USERNAME/VibeVision.git)
    cd VibeVision
    ```

2.  **Create and activate a virtual environment**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**
    Create a `.env` file in the root directory. Add multiple Gemini keys separated by commas to enable the Key Rotation feature.
    ```env
    BOT_TOKEN=your_telegram_bot_token_here
    GEMINI_API_KEY=key1,key2,key3
    ```

5.  **Run the bot**
    ```bash
    python main.py
    ```

---

## 📂 Project Structure

* `main.py` - Core application logic, FSM, and Telegram handlers.
* `.env` - Environment variables (ignored by git).
* `requirements.txt` - Python dependencies for deployment.

---

## 🐛 Troubleshooting

* **API Key Invalid (400):** Ensure your `GEMINI_API_KEY` string has no spaces around the commas or equal sign.
* **Rate Limits (429):** The bot handles this automatically if multiple keys are provided. If all keys are exhausted, the bot will notify the user to wait.
* **Missing Dependencies:** Ensure your virtual environment is activated `(venv)` before running `pip install`.

---

## 📜 License


This project is open-source and created for educational and aesthetic purposes.


