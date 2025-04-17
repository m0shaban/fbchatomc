# شات بوت مجمع عمال مصر - محمد سلامة

هذا المشروع عبارة عن شات بوت ذكي لمجمع عمال مصر، يعمل على منصة فيسبوك ماسنجر ويوفر خدمات معلوماتية وتفاعلية للمستخدمين.

## الميزات الرئيسية

- ✅ دعم كامل للغة العربية
- ✅ واجهة ماسنجر فيسبوك تفاعلية مع أزرار وقوائم
- ✅ إجابات ذكية على استفسارات المستخدمين
- ✅ قائمة خدمات تفاعلية
- ✅ آلية احتياطية للردود المحلية عند فشل الاتصال بواجهة الذكاء الاصطناعي
- ✅ واجهة اختبار محلية لتجربة الشات بوت قبل النشر

## متطلبات التشغيل

- Python 3.8 أو أحدث
- مفتاح API من DeepSeek أو OpenAI
- حساب فيسبوك وصفحة فيسبوك للأعمال
- توكن وصول للصفحة من فيسبوك

## طريقة التثبيت

1. استنساخ المستودع:
```
git clone https://github.com/yourusername/fbchatomc.git
cd fbchatomc
```

2. تثبيت المكتبات المطلوبة:
```
pip install -r requirements.txt
```

3. إنشاء ملف `.env` بالإعدادات المطلوبة:
```
# إعدادات API
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEFAULT_MODEL=deepseek-chat
MAX_TOKENS=1000
TEMPERATURE=0.7

# إعدادات فيسبوك
FB_PAGE_TOKEN=your_page_access_token_here
FB_VERIFY_TOKEN=omc_verify_token
FB_APP_SECRET=your_app_secret_here
FB_PAGE_ID=your_page_id_here

# إعدادات الويب سيرفر
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
WEBHOOK_ROUTE=/webhook
```

## طريقة التشغيل

### اختبار محلي

لاختبار الشات بوت محلياً بدون فيسبوك:

```
python test_local.py
```

### تشغيل الخادم

لتشغيل خادم الشات بوت الذي يتفاعل مع ويب هوك فيسبوك:

```
python server.py
```

## الرخصة

جميع الحقوق محفوظة &copy; 2025 مجمع عمال مصر