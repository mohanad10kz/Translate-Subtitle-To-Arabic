# 🎬 AI Tech Subtitle Translator

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat&logo=python)](https://www.python.org/)
[![AI Model](https://img.shields.io/badge/Model-Gemini%202.0%20Flash-orange?style=flat&logo=google)](https://openrouter.ai/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)
[![Open Source](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/)

---

## 📑 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)
- [Arabic Description](#arabic-description)

---

## 📝 Overview

A robust, **open-source** Python automation tool designed to translate technical subtitle files (`.vtt`, `.srt`) from English to Arabic.
It utilizes **Google's Gemini 2.0 Flash** model (via OpenRouter) to provide context-aware translations while strictly preserving code snippets, technical terminology, and variable names—making it perfect for **Software Engineering courses**.

---

## ✨ Key Features

- **🛡️ Recursive Fallback Strategy (Smart Error Handling):**
  Uses a "Divide and Conquer" algorithm. If a batch of 20 lines fails to translate (due to AI hallucinations or mismatch), the script automatically splits the batch into smaller chunks recursively until it succeeds.
- **⏯️ Idempotent Execution:**
  Automatically detects already translated files and skips them. You can stop and restart the script anytime without re-translating completed files.
- **👨‍💻 Developer-Centric:**
  - Strictly preserves code blocks, variables, and paths (e.g., `console.log`, `./src/app.js`).
  - Forces **RTL (Right-to-Left)** styling for correct Arabic playback.
- **🔒 Secure:**
  Loads API credentials securely from a `.env` file using `python-dotenv`.

---

## 🛠️ Prerequisites

1. **Python 3.8+** installed.
2. An API Key from [OpenRouter](https://openrouter.ai/) (Access to free/paid Gemini models).

---

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mohanad10kz/ai-subtitle-translator.git
   cd ai-subtitle-translator
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   > Make sure you have a requirements.txt file containing: openai, webvtt-py, pysrt, tqdm, python-dotenv
3. **Setup Environment Variables:**
   Create a `.env` file in the root directory and add your key:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## 🚀 Usage

Run the script:

```bash
python translate_subtitle_to_ar.py
```

Paste the full path to the folder containing your subtitles when prompted.

The script will generate new files with an `_ar` suffix (e.g., lecture_ar.vtt).

---

## 📜 License

This project is open-source and available under the MIT License.

---

## 🇸🇦 Arabic Summary

أداة بايثون مفتوحة المصدر لترجمة ملفات الترجمة التقنية من الإنجليزية إلى العربية مع الحفاظ على الأكواد والمصطلحات البرمجية. سهلة الاستخدام وتدعم الترجمة الذكية والسريعة.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📧 Contact

For questions or suggestions, open an issue or contact the repository owner.

pip install -r requirements.txt
(Make sure you have a requirements.txt file containing: openai, webvtt-py, pysrt, tqdm, python-dotenv)

Setup Environment Variables: Create a .env file in the root directory and add your key:

مقتطف الرمز

OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
🚀 Usage
Run the script:

Bash

python translator.py
Paste the full path to the folder containing your subtitles when prompted.

The script will generate new files with an \_ar suffix (e.g., lecture_ar.vtt).

📜 License
This project is open-source and available under the MIT License.

🎬 مترجم ملفات الترجمة التقنية بالذكاء الاصطناعي
أداة مفتوحة المصدر وتلقائية مبنية بلغة بايثون لترجمة ملفات الترجمة (.vtt, .srt) من الإنجليزية إلى العربية باحترافية.

تعتمد الأداة على نموذج Google Gemini 2.0 Flash (عبر OpenRouter) لتقديم ترجمة تفهم السياق، مع التركيز بشكل خاص على الكورسات البرمجية والتقنية، حيث تضمن عدم ترجمة الأكواد البرمجية، أسماء المتغيرات، والمصطلحات التقنية الدقيقة.

✨ المميزات الرئيسية
🛡️ استراتيجية المعالجة الذاتية (Recursive Fallback): تستخدم الأداة خوارزمية "فرّق تسد". إذا فشل النموذج في ترجمة دفعة من 20 سطراً، يقوم السكربت تلقائياً بتقسيم الدفعة إلى نصفين وإعادة المحاولة بشكل تكراري حتى تنجح الترجمة، مما يضمن عدم فقدان أي سطر.

⏯️ الذكاء في الاستكمال (Idempotency): يقوم السكربت بفحص المجلد، ويتخطى تلقائياً الملفات التي تمت ترجمتها سابقاً. يمكنك إيقاف البرنامج وتشغيله لاحقاً ليكمل من حيث توقف.

👨‍💻 مخصص للمبرمجين:

يحافظ بصرامة على كتل الكود (Code Blocks)، المسارات، وأسماء الدوال باللغة الإنجليزية.

يضيف تنسيقات RTL (من اليمين لليسار) لضمان ظهور الترجمة بشكل صحيح في مشغلات الفيديو.

🔒 آمن: يتم تحميل مفاتيح الـ API بشكل آمن من ملف .env لضمان عدم مشاركتها في الكود.

🛠️ المتطلبات
تثبيت Python 3.8 أو أحدث.

الحصول على مفتاح API من منصة OpenRouter.

📦 طريقة التثبيت
نسخ المستودع (Clone):

Bash

git clone [https://github.com/mohanad10kz/ai-subtitle-translator.git](https://github.com/mohanad10kz/ai-subtitle-translator.git)
cd ai-subtitle-translator
تثبيت المكتبات المطلوبة:

Bash

pip install -r requirements.txt
إعداد متغيرات البيئة: أنشئ ملفاً جديداً باسم .env بجانب السكربت، وضع فيه مفتاحك:

مقتطف الرمز

OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
🚀 طريقة الاستخدام
شغل السكربت:

Bash

python translator.py
سيطلب منك البرنامج مسار المجلد (Folder Path) الذي يحتوي على ملفات الترجمة.

سيبدأ البرنامج بالترجمة وإنشاء ملفات جديدة تنتهي بـ \_ar (مثال: lecture_ar.vtt).
