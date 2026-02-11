# دليل استضافة Karys Shop Bot مجاناً

## أفضل الخيارات المجانية:

### 1. **Replit** (الأسهل - موصى به للمبتدئين)
- ✅ مجاني تماماً
- ✅ سهل الاستخدام
- ✅ لا يحتاج معرفة تقنية كبيرة
- ✅ يعمل 24/7 (مع Keep-Alive)

**الخطوات:**
1. اذهب إلى: https://replit.com
2. سجل حساب جديد (مجاني)
3. اضغط "Create Repl"
4. اختر "Python"
5. ارفع ملفات البوت (bot.py, requirements.txt, .env)
6. في ملف `.env` اكتب: `DISCORD_BOT_TOKEN=token_dyalek`
7. اضغط "Run"
8. لإبقاء البوت يعمل 24/7، أضف ملف `keep_alive.py` (موجود أدناه)

### 2. **Railway** (موصى به)
- ✅ مجاني (500 ساعة/شهر)
- ✅ سهل الاستخدام
- ✅ يعمل 24/7

**الخطوات:**
1. اذهب إلى: https://railway.app
2. سجل بحساب GitHub
3. اضغط "New Project"
4. اختر "Deploy from GitHub repo"
5. ارفع ملفات البوت على GitHub
6. Railway سيشغل البوت تلقائياً

### 3. **Render** (موصى به)
- ✅ مجاني
- ✅ يعمل 24/7
- ✅ سهل الاستخدام

**الخطوات:**
1. اذهب إلى: https://render.com
2. سجل حساب جديد
3. اضغط "New" → "Web Service"
4. اربط GitHub repo
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `python bot.py`
7. اضغط "Create Web Service"

### 4. **Heroku** (معقد قليلاً)
- ✅ مجاني (مع قيود)
- ⚠️ يحتاج معرفة تقنية

### 5. **PythonAnywhere** (للمبتدئين)
- ✅ مجاني
- ⚠️ يحتاج إعادة تشغيل يدوي يومياً

---

## ملف keep_alive.py لـ Replit:

```python
from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    keep_alive()
    # Import and run your bot here
    import bot
```

**استخدامه في bot.py:**
- أضف في أول ملف bot.py: `from keep_alive import keep_alive`
- أضف قبل `bot.run(token)`: `keep_alive()`

---

## الملفات المطلوبة للرفع:

1. `bot.py` - الكود الرئيسي
2. `requirements.txt` - المكتبات
3. `.env` - Token (أو استخدم Environment Variables في المنصة)
4. `keep_alive.py` - لإبقاء البوت يعمل (لـ Replit)

---

## نصائح مهمة:

- ⚠️ **لا ترفع ملف `.env` على GitHub!** (يحتوي على Token)
- ✅ استخدم Environment Variables في المنصة بدلاً من ذلك
- ✅ تأكد من أن البوت يعمل محلياً قبل الرفع
- ✅ راقب الـ logs للتأكد من أن البوت يعمل

---

## الأفضل للمبتدئين:

**Replit** - الأسهل والأسرع:
1. سجل في Replit
2. ارفع الملفات
3. أضف Token في Environment Variables
4. اضغط Run
5. البوت يعمل!
