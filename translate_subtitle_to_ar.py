import os
import time
import json
import sys
import re
from pathlib import Path
import webvtt
import pysrt
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

# 2. تحميل المتغيرات من ملف .env
load_dotenv()

# ==========================================
# 1. إعدادات OpenRouter
# ==========================================
# 3. قراءة المفتاح بأمان
API_KEY = os.getenv("API_KEY")

# التحقق من أن المفتاح تم تحميله
if not API_KEY:
    print("❌ Error: Could not find 'API_KEY' in .env file.")
    print("💡 Please create a .env file and add your key.")
    sys.exit(1)

# اسم الموديل
# MODEL_NAME = "google/gemini-2.0-flash-exp:free"
MODEL_NAME = "xiaomi/mimo-v2-flash:free"
# MODEL_NAME = "deepseek/deepseek-r1-0528:free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

SYSTEM_PROMPT = """
You are a Senior Technical Translator and Software Engineering Instructor for Arab developers.
Your task is to translate a list of subtitle lines from English to Arabic, specifically for a programming course.

### 🎯 OBJECTIVE:
Produce a translation that sounds natural to an Arab developer (Tech-Savvy Arabic). Do not use stiff, academic, or "Google Translate" style Arabic.

### ⚠️ CRITICAL TECHNICAL RULES (ZERO TOLERANCE):
1. **JSON Only:** Return NOTHING but a raw JSON list of strings. No Markdown code blocks (```json), no intro text, no explanations.
2. **Line Count:** If I send N lines, you MUST return exactly N lines. Never merge or split lines.
3. **Code Preservation:** NEVER translate code syntax, variable names, function names, file paths, or CLI commands.
   - ❌ Bad: "سجل دوت لوج"
   - ✅ Good: "console.log"
   - ❌ Bad: "المتغير مستخدم"
   - ✅ Good: "user variable"

### 🗣️ TRANSLATION STYLE GUIDE:
1. **Keep Tech Terms English:** Do not translate standard technical terms. Keep them in English.
   - ❌ Bad: "واجهة برمجة التطبيقات", "إطار العمل", "المكون", "الخلفية"
   - ✅ Good: "API", "Framework", "Component", "Backend"
2. **Natural Flow:** Use "Arabizi-style" technical phrasing common in the industry.
   - ❌ Bad: "سوف نقوم بإنشاء مثيل جديد من الفئة"
   - ✅ Good: "سنقوم بإنشاء Instance جديد من الـ Class"
3. **Short Lines:** If a line is very short (1-3 words) and is a label or title (e.g., "Introduction", "Chapter 1", "Next.js"), translate it ONLY if it makes sense. If it's a pure tech term like "React Hooks", keep it English.

### 📝 EXAMPLES (Follow this pattern):

**Input:**
[
  "Welcome back to the course.",
  "In this lecture, we will look at the useEffect hook.",
  "It allows us to handle side effects.",
  "const data = await fetch('/api/user');",
  "So, let's dive into the code."
]

**Output:**
[
  "أهلاً بكم مجدداً في الكورس.",
  "في هذه المحاضرة، سنلقي نظرة على الـ useEffect hook.",
  "إنه يسمح لنا بالتعامل مع الـ side effects.",
  "const data = await fetch('/api/user');",
  "إذًا، دعونا نغوص في الكود."
]

### 🚨 FINAL WARNING:
- Do NOT output English lines for sentences (e.g., "So then..." must become "إذًا بعد ذلك...").
- Only keep English if it is Code, a Tech Term, or a Proper Noun.
"""

RLE = '\u202b'
PDF = '\u202c'

def extract_json_list(text):
    """ استخراج JSON من النص """
    try:
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1:
            clean_json = text[start:end+1]
            return json.loads(clean_json)
        return json.loads(text)
    except:
        return None

def has_arabic(text):
    """ فحص هل يحتوي النص على حروف عربية """
    return bool(re.search(r'[\u0600-\u06FF]', text))

def is_valid_translation(original_batch, translated_batch):
    """
    دالة التحقق الذكية: تميز بين المصطلحات التقنية (المقبولة بالإنجليزية)
    وبين الجمل التي فشل الموديل في ترجمتها.
    """
    if len(original_batch) != len(translated_batch):
        return False, "Mismatch length"

    echo_count = 0
    no_arabic_count = 0
    
    for org, trans in zip(original_batch, translated_batch):
        org_clean = org.strip()
        trans_clean = trans.strip()
        
        # 1. فحص التطابق (Echoing)
        # نتجاهل الأسطر القصيرة جداً (أقل من 4 كلمات) لأن "React" تترجم "React" وهذا صحيح
        word_count = len(trans_clean.split())
        
        if word_count > 3 and org_clean.lower() == trans_clean.lower():
            echo_count += 1
            
        # 2. فحص المحتوى العربي (Arabic Content Check)
        is_code_like = re.search(r'[{}();=><]', trans_clean) or trans_clean.startswith(('import ', 'console.', '<', 'return', 'export'))
        has_ar = has_arabic(trans_clean)
        
        # اللغز هنا: متى نعتبر عدم وجود العربية "مشكلة"؟
        # فقط إذا لم يكن كوداً.. وكان السطر طويلاً (أكثر من 3 كلمات)
        if not is_code_like and not has_ar:
            if word_count > 3: 
                # جملة طويلة إنجليزية؟ هذه مشكلة
                no_arabic_count += 1
            else:
                # كلمة أو كلمتين إنجليزية؟ (مثل "Chapter 1", "JSON Data", "React Hook")
                # هذا طبيعي في الكورسات التقنية، نتجاهلها ولا نعدها خطأ
                pass

    # التسامح في نسبة الخطأ
    
    # نرفض إذا كان أكثر من 30% من الجمل الطويلة منسوخة حرفياً
    if echo_count > (len(original_batch) * 0.3):
        return False, f"Too much echoing in long sentences ({echo_count}/{len(original_batch)})"

    # نرفض إذا كان أكثر من 40% من الجمل الطويلة ليس بها عربية
    if no_arabic_count > (len(original_batch) * 0.4):
        return False, f"Missing Arabic in sentences ({no_arabic_count}/{len(original_batch)})"

    return True, "Valid"

def translate_batch(texts_batch, depth=0):
    """
    ترجمة دفعة مع استراتيجية 'فرق تسد' + التحقق من العروبة
    """
    max_retries = 2
    
    user_message = f"Translate these specific {len(texts_batch)} lines to Arabic. Return exactly {len(texts_batch)} lines in a JSON list:"
    full_user_content = user_message + "\n" + json.dumps(texts_batch)

    for attempt in range(max_retries):
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_user_content}
            ]
            
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                extra_headers={
                    "HTTP-Referer": "https://github.com/mohanad", 
                    "X-Title": "Subtitle Translator Script"
                },
                temperature=0.1 
            )
            
            response_text = completion.choices[0].message.content.strip()
            translated_list = extract_json_list(response_text)
            
            if translated_list is None:
                continue 

            # 🔥 هنا الإضافة الجديدة: التحقق من صحة الترجمة
            is_valid, reason = is_valid_translation(texts_batch, translated_list)
            
            if not is_valid:
                print(f"⚠️ Validation Failed: {reason}. Retrying...")
                # نعتبرها فشلاً ونعيد المحاولة أو التقسيم
                continue 

            return [f"{RLE}{text}{PDF}" for text in translated_list]
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Rate limit" in error_msg:
                wait_time = 30 
                if depth > 0: wait_time = 10
                print(f"⏳ Rate Limit. Cooling down {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                pass
    
    # استراتيجية الفشل الذكي (Recursive Splitting)
    if len(texts_batch) > 1:
        mid = len(texts_batch) // 2
        if depth == 0:
            print(f"🔄 Splitting batch of {len(texts_batch)} into {mid} and {len(texts_batch)-mid} due to validation failure...")
        
        left_batch = texts_batch[:mid]
        right_batch = texts_batch[mid:]
        
        left_result = translate_batch(left_batch, depth=depth+1)
        right_result = translate_batch(right_batch, depth=depth+1)
        
        if left_result and right_result:
            return left_result + right_result
    
    return None

def process_single_file(file_path, is_vtt=True):
    print(f"\n📄 Processing: {file_path.name}")
    
    if is_vtt:
        try:
            subs = list(webvtt.read(file_path))
        except:
            print(f"❌ Error reading VTT file: {file_path.name}")
            return False
    else:
        try:
            subs = pysrt.open(str(file_path), encoding='utf-8')
        except:
             print(f"❌ Error reading SRT file: {file_path.name}")
             return False

    all_texts = [sub.text for sub in subs]
    translated_texts = []
    
    # تقليل حجم الدفعة قليلاً لزيادة الدقة
    BATCH_SIZE = 15 
    
    pbar = tqdm(range(0, len(all_texts), BATCH_SIZE), desc="🌐 AI Translating", leave=False)
    
    for i in pbar:
        batch = all_texts[i : i + BATCH_SIZE]
        
        translated_batch = translate_batch(batch)
        
        if translated_batch is None:
            pbar.close()
            print(f"⚠️ Failed to translate a batch in {file_path.name}. Skipping file.")
            return False 
            
        translated_texts.extend(translated_batch)
        # لا حاجة لانتظار طويل مع OpenRouter
        # time.sleep(0.5) 

    output_ext = ".vtt" if is_vtt else ".srt"
    output_path = file_path.parent / f"{file_path.stem}_ar{output_ext}"

    if is_vtt:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\nSTYLE\n::cue {\n  direction: rtl;\n  text-align: right;\n}\n\n")
            for i, sub in enumerate(subs):
                txt = translated_texts[i] if i < len(translated_texts) else ""
                f.write(f"{sub.start} --> {sub.end} align:right\n{txt}\n\n")
    else:
        for i, sub in enumerate(subs):
            sub.text = translated_texts[i] if i < len(translated_texts) else ""
        subs.save(str(output_path), encoding='utf-8')

    print(f"✅ Success: Saved to {output_path.name}")
    return True

def main():
    if not API_KEY or API_KEY.startswith("sk-or-v1-xx"):
        print("❌ Error: Please insert your OpenRouter API Key in .env file or script.")
        return

    folder_input = input("📁 Enter folder path: ").strip().strip('"')
    folder_path = Path(folder_input)

    if not folder_path.is_dir():
        print("❌ Invalid directory.")
        return

    all_source_files = list(folder_path.glob("*.vtt")) + list(folder_path.glob("*.srt"))
    
    if not all_source_files:
        print("⚠️ No files found.")
        return

    files_to_process = []
    skipped_count = 0
    
    print("\n🔍 Scanning files...")
    for file in all_source_files:
        if file.stem.endswith("_ar"): continue
            
        ext = file.suffix.lower()
        expected_output_name = f"{file.stem}_ar{ext}"
        expected_output_path = file.parent / expected_output_name
        
        if expected_output_path.exists():
            skipped_count += 1
        else:
            files_to_process.append(file)

    print(f"⏭️  Skipped: {skipped_count} files (Already translated).")
    print(f"📋 Remaining: {len(files_to_process)} files.\n")

    if not files_to_process:
        print("🎉 All files are already translated!")
        return

    failed_files = []

    for i, file in enumerate(files_to_process, 1):
        print(f"[{i}/{len(files_to_process)}]", end=" ")
        is_vtt = file.suffix.lower() == '.vtt'
        success = process_single_file(file, is_vtt)
        
        if not success:
            failed_files.append(file)
            print("🔻 Added to Retry Queue.")
            time.sleep(2)

    if failed_files:
        print("\n" + "="*40)
        print(f"⚠️ Retrying {len(failed_files)} failed files...")
        print("="*40 + "\n")
        
        for file in failed_files:
            print(f"🔄 Retrying: {file.name}")
            time.sleep(5) 
            
            is_vtt = file.suffix.lower() == '.vtt'
            success = process_single_file(file, is_vtt)
            
            if not success:
                print(f"❌ Final Failure: {file.name}")
                print("🛑 Script stopped due to persistent errors.")
                sys.exit(1)

    print("\n🎉 All operations completed successfully.")

if __name__ == "__main__":
    main()