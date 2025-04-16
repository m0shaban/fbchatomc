# شات بوت مجمع عمال مصر

نظام ذكي للرد على استفسارات زوار صفحة مجمع عمال مصر على فيسبوك سواء عبر الماسنجر أو تعليقات المنشورات.

## المميزات

- الرد التلقائي على تعليقات الفيسبوك
- التعامل مع رسائل الماسنجر 
- تصنيف المستخدمين حسب الفئة (باحث عن عمل، مستثمر، صحفي، إلخ)
- تحليل الاستفسارات وتوجيه المستخدم للخدمة المناسبة
- نظام إحصائيات متكامل لمتابعة أداء النظام
- تنقية الردود من أي إشارات للذكاء الاصطناعي
- معالجة متقدمة للغة العربية

## المتطلبات

- Python 3.8+
- وصول إلى DeepSeek API
- وصول إلى Facebook Graph API (للاستخدام في الإنتاج)

## التثبيت

1. نسخ المستودع:
```bash
git clone https://github.com/username/fbchatomc.git
cd fbchatomc
```

2. تثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

3. إنشاء ملف `.env` وتعديل الإعدادات حسب متطلباتك:
```
# إعدادات API
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEFAULT_MODEL=deepseek-chat
MAX_TOKENS=1000
TEMPERATURE=0.7

# إعدادات الشات بوت
DATA_FILE=data.json
LOG_FILE=logs/chatbot.log
SIMILARITY_THRESHOLD=0.4
PERSONALIZE_RESPONSE=True
SAVE_CONVERSATIONS=True
CONVERSATIONS_DIR=conversations

# إعدادات فيسبوك
FB_PAGE_TOKEN=your_page_access_token_here
FB_VERIFY_TOKEN=your_verify_token
FB_APP_SECRET=your_app_secret_here
FB_PAGE_ID=your_page_id_here
FB_IGNORE_PRAISE=True
FB_COMMENT_LENGTH=3

# إعدادات الويب سيرفر
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
WEBHOOK_ROUTE=/webhook

# إعدادات التطبيق
DEBUG_MODE=False
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## الاستخدام

### تشغيل معالج تعليقات الفيسبوك
```bash
python facebook_comments.py
```

### تشغيل واجهة API
```bash
python server.py
```

### عرض الإحصائيات
```bash
python analytics.py --charts
```

## الهيكل العام للمشروع

- `bot.py`: المكون الرئيسي للشات بوت
- `api.py`: واجهة للاتصال مع DeepSeek API
- `config.py`: إعدادات التطبيق
- `facebook_comments.py`: معالج تعليقات الفيسبوك
- `server.py`: خادم الويب للتعامل مع webhook
- `analytics.py`: أدوات تحليل وعرض الإحصائيات
- `data.json`: قاعدة البيانات المعرفية للشات بوت
- `test_chatbot.py`: اختبارات آلية للشات بوت

## الترخيص

جميع الحقوق محفوظة © لمجمع عمال مصر