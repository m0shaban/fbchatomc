# شات بوت مجمع عمال مصر - محمد سلامة

هذا المشروع عبارة عن شات بوت ذكي لمجمع عمال مصر، يعمل على منصة فيسبوك ماسنجر ويوفر خدمات معلوماتية وتفاعلية للمستخدمين. يستخدم الشات بوت نماذج الذكاء الاصطناعي من DeepSeek لتوفير تجربة محادثة طبيعية وسلسة باللغة العربية.

<div align="center">
    <img src="https://i.imgur.com/example-image.png" alt="شات بوت مجمع عمال مصر" width="300"/>
</div>

## 🌟 الميزات الرئيسية

- ✅ **دعم كامل للغة العربية**: مصمم خصيصاً للتعامل مع اللغة العربية بطلاقة
- ✅ **واجهة ماسنجر فيسبوك تفاعلية**: أزرار وقوائم ديناميكية تسهل على المستخدم التنقل والتفاعل
- ✅ **معالجة الذكاء الاصطناعي**: استخدام نماذج DeepSeek للردود الذكية على استفسارات المستخدمين
- ✅ **قاعدة معرفة شاملة**: قاعدة بيانات غنية بالمعلومات عن خدمات المجمع
- ✅ **قائمة خدمات تفاعلية**: عرض خدمات المجمع بطريقة منظمة وسهلة الوصول
- ✅ **آلية احتياطية للردود**: ضمان استمرارية الخدمة حتى عند فشل الاتصال بواجهة الذكاء الاصطناعي
- ✅ **واجهة اختبار محلية**: إمكانية تجربة الشات بوت محلياً قبل النشر
- ✅ **تخصيص الردود**: إضافة طابع شخصي للمحادثات باستخدام اسم المستخدم
- ✅ **لوحة تحكم للمطور**: ميزات خاصة للمطور لمراقبة الأداء وتعديل الإعدادات
- ✅ **تحليلات المحادثات**: إحصائيات وتقارير شاملة عن استخدام الشات بوت
- ✅ **مرونة في الإعدادات**: تعديل سلوك الشات بوت بسهولة من خلال ملفات الإعدادات

## 📋 محتويات المشروع

- **bot.py**: الملف الرئيسي لمنطق الشات بوت ومعالجة الرسائل
- **api.py**: واجهة الاتصال مع DeepSeek API
- **server.py**: خادم الويب للتفاعل مع webhook فيسبوك
- **test_local.py**: واجهة اختبار محلية للشات بوت
- **messenger_utils.py**: أدوات للتفاعل مع واجهة ماسنجر فيسبوك
- **facebook_comments.py**: معالجة التعليقات على منشورات الفيسبوك
- **config.py**: ملف الإعدادات والتكوين
- **data.json**: قاعدة المعرفة للشات بوت
- **services_data.py**: بيانات الخدمات التي يقدمها المجمع
- **api_alternatives.py**: بدائل للواجهة البرمجية في حالة فشل الاتصال الأساسي

## 🔧 متطلبات التشغيل

- Python 3.8 أو أحدث
- مفتاح API من DeepSeek أو بديل (OpenAI)
- حساب فيسبوك وصفحة فيسبوك للأعمال
- توكن وصول للصفحة من فيسبوك
- خادم ويب يمكن الوصول إليه من الإنترنت (للاستخدام مع webhook فيسبوك)
- المكتبات المذكورة في ملف requirements.txt

## 📥 طريقة التثبيت

### 1. استنساخ المستودع:
```bash
git clone https://github.com/yourusername/fbchatomc.git
cd fbchatomc
```

### 2. إنشاء بيئة افتراضية (اختياري لكن موصى به):
```bash
python -m venv venv
# تفعيل البيئة الافتراضية في ويندوز
venv\Scripts\activate
# تفعيل البيئة الافتراضية في Linux/Mac
source venv/bin/activate
```

### 3. تثبيت المكتبات المطلوبة:
```bash
pip install -r requirements.txt
```

### 4. إنشاء ملف `.env` بالإعدادات المطلوبة:

يمكنك نسخ النموذج التالي وتعديله حسب احتياجاتك:

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
FB_VERIFY_TOKEN=omc_verify_token
FB_APP_SECRET=your_app_secret_here
FB_PAGE_ID=your_page_id_here

# إعدادات الويب سيرفر
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
WEBHOOK_ROUTE=/webhook
APP_ENVIRONMENT=development  # development أو production
```

### 5. إنشاء المجلدات اللازمة:
```bash
mkdir -p logs conversations
```

## ▶️ طريقة التشغيل

### اختبار محلي

لاختبار الشات بوت محلياً بدون الحاجة إلى فيسبوك:

```bash
python test_local.py
```

هذا يتيح لك محادثة الشات بوت مباشرة من خلال واجهة سطر الأوامر، مما يسمح باختبار وظائف الشات بوت قبل ربطه بفيسبوك.

### تشغيل الخادم

لتشغيل خادم الشات بوت الذي يتفاعل مع webhook فيسبوك:

```bash
python server.py
```

ستظهر رسالة تفيد بدء تشغيل الخادم على المنفذ المحدد في الإعدادات (5000 افتراضياً).

### تشغيل سريع (باستخدام ملف الدفعة)

يمكنك استخدام ملف الدفعة المرفق لتشغيل الشات بوت:

```bash
run_chatbot.bat
```

## 🔄 إعداد webhook فيسبوك

1. انتقل إلى [صفحة مطوري فيسبوك](https://developers.facebook.com/)
2. أنشئ تطبيق جديد من نوع "Business"
3. أضف منتج "Messenger" إلى تطبيقك
4. ربط التطبيق بصفحة الفيسبوك الخاصة بك والحصول على توكن الوصول
5. قم بإعداد webhook باستخدام:
   - عنوان URL: `https://your-server-address/webhook`
   - رمز التحقق: القيمة التي حددتها في `FB_VERIFY_TOKEN`
   - اشترك في أحداث: `messages`, `messaging_postbacks`

## 💡 ميزات متقدمة

### واجهة المطور

للوصول إلى واجهة المطور، أرسل كلمة السر "افتح يا سمسم انا محمد شعبان" في محادثة مع الشات بوت.

تتيح واجهة المطور:

- عرض إحصائيات المحادثات
- تعديل إعدادات الشات بوت
- عرض المميزات الفنية للشات بوت
- إجراء اختبارات للأداء

### أوامر المطور المتاحة

بعد تسجيل الدخول كمطور، يمكنك استخدام الأوامر التالية:

- `عرض الإحصائيات`: لعرض إحصائيات استخدام الشات بوت
- `عرض المميزات`: لعرض المميزات الفنية للشات بوت
- `فتح الإعدادات`: لفتح قائمة تعديل الإعدادات
- `تفعيل الاستمرارية`: لتفعيل ميزة استمرارية المحادثة
- `تعطيل الاستمرارية`: لتعطيل ميزة استمرارية المحادثة
- `تفعيل الشخصنة`: لتفعيل تخصيص الردود حسب اسم المستخدم
- `تعطيل الشخصنة`: لتعطيل تخصيص الردود
- `تعيين التشابه x.x`: لتعيين حد التشابه للبحث في قاعدة المعرفة (قيمة بين 0.1 و 0.9)
- `العودة`: للعودة إلى وضع المحادثة العادي

## 📂 هيكل قاعدة البيانات

ملف `data.json` يحتوي على:

- الأسئلة والأجوبة الشائعة
- روابط الخدمات المختلفة
- التعبيرات البشرية للرد
- معلومات التواصل
- فئات المستخدمين
- بيانات القوائم والأزرار

## 🚀 النشر على خدمات الاستضافة

### النشر على Render

يمكن استخدام ملف `render.yaml` للنشر على منصة Render:

1. قم بربط حساب Render بمستودع GitHub الخاص بك
2. استخدم خيار "Blueprint" واختر الملف `render.yaml`
3. أضف المتغيرات البيئية المطلوبة

### النشر على Railway

يمكن استخدام ملف `railway.json` للنشر على منصة Railway:

1. قم بتثبيت CLI الخاص بـ Railway
2. استخدم الأمر `railway login`
3. استخدم الأمر `railway up` لنشر المشروع

## ⚠️ استكشاف الأخطاء وإصلاحها

### مشاكل الاتصال بـ API

إذا واجهت مشاكل في الاتصال بواجهة DeepSeek API:

1. تحقق من صحة مفتاح API في ملف `.env`
2. تأكد من الاتصال بالإنترنت
3. قم بتشغيل `test_api_connection.py` للتحقق من الاتصال:
   ```bash
   python test_api_connection.py
   ```

### مشاكل في webhook فيسبوك

1. تأكد من إمكانية الوصول إلى الخادم من الإنترنت
2. تحقق من توافق الرمز السري للتحقق
3. تحقق من سجلات الخطأ في `logs/chatbot.log`

## 🛠️ تطوير وتحسين الشات بوت

### إضافة أسئلة وأجوبة جديدة

يمكنك إضافة أسئلة وأجوبة جديدة عن طريق تحرير ملف `data.json`:

```json
{
  "prompts": [
    {
      "id": NEXT_ID,
      "question": "السؤال الجديد",
      "answer": "الإجابة الجديدة"
    },
    ...
  ]
}
```

### تعديل قائمة الخدمات

يمكن تعديل قائمة الخدمات في ملف `data.json` أو `services_data.py`.

## 📞 التواصل والدعم

للاستفسارات والدعم الفني، يرجى التواصل مع:

- البريد الإلكتروني: eng.mohamed0shaban@gmail.com
- هاتف: 01121891913

## 📄 الرخصة

جميع الحقوق محفوظة &copy; 2025 مجمع عمال مصر

---

طُوّر بواسطة: محمد شعبان | للإسهام في تطوير الشات بوت، يرجى التواصل معنا.