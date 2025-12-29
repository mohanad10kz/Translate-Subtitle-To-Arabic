import os
import time
import json
import sys
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

# إعداد العميل
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY, # تم استخدام المتغير الصحيح
)

# تحديث البرومبت ليكون صارماً جداً بشأن العدد
SYSTEM_PROMPT = """
You are a strictly mechanical technical translator for subtitle files.
Your task is to translate Software Engineering content from English to Arabic.

STRICT RULES:
1. **Output Format:** You must return ONLY a raw JSON list of strings. No Markdown code blocks. No intro/outro text.
2. **One-to-One Mapping:** If I send you 20 lines, you MUST return exactly 20 translated lines. DO NOT merge lines. DO NOT split lines. DO NOT summarize.
3. **Code Safety:** Never translate variable names, function names, or file paths (keep them English).
4. **Terminology:** Use standard technical Arabic (API, JSON, Framework stay English).
"""

RLE = '\u202b'
PDF = '\u202c'

def extract_json_list(text):
    """
    دالة جراحية لاستخراج القائمة من وسط النص مهما كان حولها من شوائب
    """
    try:
        # البحث عن أول قوس مصفوفة وأخر قوس
        start = text.find('[')
        end = text.rfind(']')
        
        if start != -1 and end != -1:
            # استخراج ما بين القوسين فقط
            clean_json = text[start:end+1]
            return json.loads(clean_json)
        
        # محاولة أخيرة: ربما النص نظيف أصلاً
        return json.loads(text)
    except:
        return None

def translate_batch(texts_batch, depth=0):
    """
    ترجمة دفعة مع استراتيجية 'فرق تسد' (Recursive Fallback)
    إذا فشل العدد الكبير، يقسمه لنصفين ويعيد المحاولة.
    """
    max_retries = 2 # تقليل المحاولات لأننا سنعتمد على التقسيم
    
    # رسالة ديناميكية
    user_message = f"Translate these specific {len(texts_batch)} lines. Return exactly {len(texts_batch)} lines in a JSON list:"
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
                # إذا كان الرد فاسداً، نعيد المحاولة
                continue 

            if len(translated_list) != len(texts_batch):
                print(f"⚠️ Mismatch: Sent {len(texts_batch)}, Got {len(translated_list)}.")
                # نعتبرها فشلاً ونكمل للمحاولة التالية أو التقسيم
                continue 

            # نجاح!
            return [f"{RLE}{text}{PDF}" for text in translated_list]
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Rate limit" in error_msg:
                wait_time = 30 
                print(f"⏳ Rate Limit. Cooling down {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ API Error: {error_msg}")
    
    # ========================================================
    # 🔥 هنا السحر: استراتيجية الفشل الذكي (Fallback Strategy)
    # ========================================================
    # إذا وصلنا هنا، يعني أن المحاولات فشلت.
    # إذا كانت الدفعة أكبر من سطر واحد، نقسمها لنصفين ونحاول مجدداً
    if len(texts_batch) > 1:
        mid = len(texts_batch) // 2
        print(f"🔄 Splitting batch of {len(texts_batch)} into {mid} and {len(texts_batch)-mid}...")
        
        left_batch = texts_batch[:mid]
        right_batch = texts_batch[mid:]
        
        # استدعاء ذاتي (Recursion)
        left_result = translate_batch(left_batch, depth=depth+1)
        right_result = translate_batch(right_batch, depth=depth+1)
        
        if left_result and right_result:
            return left_result + right_result
    
    # إذا وصلنا لسطر واحد وفشل، فلا حل له (نرجع None)
    return None

def process_single_file(file_path, is_vtt=True):
    print(f"\n📄 Processing: {file_path.name}")
    
    if is_vtt:
        subs = list(webvtt.read(file_path))
    else:
        subs = pysrt.open(str(file_path), encoding='utf-8')

    all_texts = [sub.text for sub in subs]
    translated_texts = []
    
    BATCH_SIZE = 20
    
    pbar = tqdm(range(0, len(all_texts), BATCH_SIZE), desc="🌐 AI Translating", leave=False)
    
    for i in pbar:
        batch = all_texts[i : i + BATCH_SIZE]
        
        translated_batch = translate_batch(batch)
        
        if translated_batch is None:
            pbar.close()
            print(f"⚠️ Failed to translate a batch in {file_path.name}. Skipping file.")
            return False 
            
        translated_texts.extend(translated_batch)
        time.sleep(1) 

    output_ext = ".vtt" if is_vtt else ".srt"
    output_path = file_path.parent / f"{file_path.stem}_ar{output_ext}"

    if is_vtt:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\nSTYLE\n::cue {\n  direction: rtl;\n  text-align: right;\n}\n\n")
            for i, sub in enumerate(subs):
                f.write(f"{sub.start} --> {sub.end} align:right\n{translated_texts[i]}\n\n")
    else:
        for i, sub in enumerate(subs):
            sub.text = translated_texts[i]
        subs.save(str(output_path), encoding='utf-8')

    print(f"✅ Success: Saved to {output_path.name}")
    return True

def main():
    # التحقق باستخدام الاسم الموحد API_KEY
    if API_KEY.startswith("sk-or-v1-xx"):
        print("❌ Error: Please insert your OpenRouter API Key.")
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

    # الفلترة
    files_to_process = []
    skipped_count = 0
    
    print("\n🔍 Scanning files...")
    
    for file in all_source_files:
        if file.stem.endswith("_ar"):
            continue
            
        ext = file.suffix.lower()
        expected_output_name = f"{file.stem}_ar{ext}"
        expected_output_path = file.parent / expected_output_name
        
        if expected_output_path.exists():
            skipped_count += 1
        else:
            files_to_process.append(file)

    print(f"⏭️  Skipped: {skipped_count} files (Already translated).")
    print(f"📋 Remaining: {len(files_to_process)} files using OpenRouter.\n")

    if not files_to_process:
        print("🎉 All files are already translated!")
        return

    # المعالجة
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