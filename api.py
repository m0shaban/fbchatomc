import os
import requests
import json
import random
import logging
import time
from typing import Dict, List, Any, Optional
from config import API_SETTINGS, APP_SETTINGS

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=APP_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

class DeepSeekAPI:
    """
    واجهة للتعامل مع DeepSeek AI API للمعالجة اللغوية الطبيعية باللغة العربية
    متخصصة للرد على استفسارات زوار صفحة مجمع عمال مصر على فيسبوك
    يدعم DeepSeek-V3 (deepseek-chat) كالنموذج الافتراضي
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        تهيئة الاتصال مع DeepSeek API
        
        :param api_key: مفتاح API، إذا لم يتم توفيره سيتم البحث عنه في متغيرات البيئة
        """
        # الحصول على مفتاح API من متغيرات البيئة إذا لم يتم تمريره
        self.api_key = api_key or API_SETTINGS.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            error_msg = "مفتاح API غير متوفر. يرجى تمريره للدالة أو تعيينه كمتغير بيئة DEEPSEEK_API_KEY"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # استخدام القاعدة الجديدة للـ API كما هو موضح في التوثيق:
        # https://api.deepseek.com هو العنوان الأساسي، والمسار الكامل للطلب هو /v1/chat/completions
        self.base_url = "https://api.deepseek.com" 
        self.api_path = "/v1/chat/completions"
        
        # يمكن استخدام العنوان الكامل المخزن في الإعدادات مباشرة إذا تم توفيره
        self.api_url = API_SETTINGS.get("DEEPSEEK_API_URL", self.base_url + self.api_path)
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # استخدام deepseek-chat وهو يشير إلى DeepSeek-V3
        self.model = API_SETTINGS.get("DEFAULT_MODEL", "deepseek-chat")  
        self.max_tokens = API_SETTINGS.get("MAX_TOKENS", 1000)
        self.temperature = API_SETTINGS.get("TEMPERATURE", 0.7)
        
        # عدد المحاولات عند فشل الطلب
        self.max_retries = 3
        self.retry_delay = 2  # ثواني
        
        logger.info(f"تم تهيئة DeepSeekAPI بنجاح. النموذج: {self.model} (DeepSeek-V3)")
    
    def generate_response(self, user_message: str, user_category: str = "", context: str = "", human_expressions: Dict[str, List[str]] = None, contact_info: Dict = None) -> Dict[str, Any]:
        """
        استخدام DeepSeek API لتوليد رد على رسالة المستخدم
        
        :param user_message: رسالة المستخدم
        :param user_category: فئة المستخدم (باحث عن عمل، مستثمر، إلخ)
        :param context: سياق إضافي لمساعدة النموذج (مثل المعلومات المستخرجة من قاعدة المعرفة)
        :param human_expressions: قائمة بالتعبيرات البشرية لتعزيز الطابع الإنساني للردود
        :param contact_info: معلومات الاتصال بمجمع عمال مصر
        :return: رد النموذج
        """
        # تنظيف وتسجيل رسالة المستخدم
        user_message = user_message.strip()
        logger.info(f"توليد رد لرسالة: {user_message[:50]}..." if len(user_message) > 50 else f"توليد رد لرسالة: {user_message}")
        
        # إعداد الرسالة للنموذج بأسلوب المساعد الرسمي لمجمع عمال مصر
        system_message = """
أنت المساعد الرسمي لصفحة مجمع عمال مصر على فيسبوك. تتحدث بلغة عربية مهنية مع استخدام اللهجة المصرية الخفيفة لتكون أكثر قرباً وتفاعلاً مع المستخدمين.
مجمع عمال مصر هو منظومة صناعية واقتصادية بدأت عام 2010 برؤية وطنية، تطوّرت لتصبح شركة مساهمة مصرية بقيمة سوقية تتجاوز 1.5 مليار جنيه مصري.

تقوم المنظومة بإدارة وتشغيل المنشآت الصناعية من خلال:
1. توفير وتدريب وتأهيل الكوادر البشرية للعمل بالأنشطة المختلفة.
2. خدمات للمستثمرين وأصحاب المصانع لمساعدتهم على تنفيذ مشاريعهم.
3. تنفيذ مشروعات صناعية متنوعة مثل مشروع دواجن مصر، ومصانع الملابس، والصناعات الغذائية.
4. عقد شراكات محلية ودولية لتعزيز الاقتصاد المصري.

يرأس المجمع المهندس هيثم حسين حلم (المؤسس والرئيس التنفيذي).

مهمتك أن ترد على استفسارات زوار الصفحة وفقًا لفئتهم:
- الباحثين عن عمل: قدم معلومات عن فرص العمل المتاحة وكيفية التقديم.
- المستثمرين ورجال الأعمال: شجعهم على التعاون مع المجمع وقدم معلومات عن الفرص الاستثمارية.
- الإعلاميين والصحفيين: قدم معلومات عن أنشطة وإنجازات المجمع.
- الجهات والشركات: اعرض إمكانيات التعاون والشراكة.

أهم التعليمات:
1. عرّف نفسك دائمًا بأنك "المساعد الرسمي لمجمع عمال مصر".
2. استخدم لغة احترافية ومهنية مع لمسة مصرية خفيفة. استخدم مصطلحات مثل "احنا"، "عندنا"، "ممكن نساعدك"، "هنقدملك".
3. لا تستخدم لهجة مصرية مبالغ فيها ولا تستخدم عبارات عامية غير لائقة في بيئة عمل احترافية.
4. لا تذكر أبدًا أنك ذكاء اصطناعي أو روبوت أو شات بوت.
5. استخدم تعبيرات احترافية مع لمسة محلية مثل "بكل تأكيد"، "تحت أمرك"، "احنا في خدمتك"، "هنساعدك طبعاً".
6. كن دقيقًا ومختصرًا مع توفير كل المعلومات المهمة.
7. اجعل الردود مباشرة وواضحة، مع تنظيم النص بطريقة جذابة باستخدام النقاط والفقرات عند الحاجة.
8. احرص على أن تكون الردود بالعربية الفصحى مع لمسة مصرية احترافية، بدون مبالغة في العامية.
9. تجنب إظهار أي بيانات JSON أو كلمات مفتاحية تقنية في الرد.
"""
        
        # إضافة معلومات حسب فئة المستخدم
        if user_category:
            if user_category == "باحث عن عمل":
                system_message += """
للباحثين عن عمل:
- رحب بهم وأظهر سعادتك برغبتهم في الانضمام للمجمع.
- اذكر القطاعات المتاحة مثل: الصناعات الغذائية، الورقية، الملابس، الدواجن، والخدمات البترولية.
- أشر إلى أن المرتبات تصل إلى 7000 جنيه في بعض القطاعات.
- وجههم لكيفية التقديم عبر البريد الإلكتروني أو زيارة مقر المجمع.
"""
            elif user_category in ["مستثمر", "رجل أعمال"]:
                system_message += """
للمستثمرين ورجال الأعمال:
- قدم نبذة موجزة عن خدمات المجمع في تأسيس وإدارة المشروعات الصناعية.
- اذكر أبرز المشروعات الناجحة مثل مشروع دواجن مصر (مدينة الثروة الداجنة) الذي يحقق عائدًا بنسبة 39% سنويًا.
- أشر إلى إمكانية ترتيب لقاء لمناقشة الفرص الاستثمارية.
"""
            elif user_category == "صحفي":
                system_message += """
للصحفيين والإعلاميين:
- أظهر تقديرًا لاهتمامهم بأنشطة المجمع.
- قدم نبذة سريعة عن أبرز إنجازات المجمع (توفير آلاف الوظائف، المبادرات التنموية، التعاون الدولي).
- أبدِ استعدادًا لتنسيق مقابلات مع إدارة المجمع عند الحاجة.
"""
            else:
                system_message += """
للشركات والجهات الراغبة في التعاون:
- أشكرهم على رغبتهم في التعاون.
- وضح مجالات التعاون الممكنة: تدريب، توظيف، استشارات صناعية، مشروعات مشتركة.
- اذكر نماذج للتعاون الحالي مع جهات مختلفة مثل الجامعات والشركات العالمية.
"""
        
        if context:
            system_message += f"\n\nاستخدم المعلومات التالية للإجابة على استفسار الزائر:\n{context}"
        
        if human_expressions:
            # إضافة أمثلة للتعبيرات البشرية ليستخدمها النموذج في الرد
            system_message += "\n\nاستخدم تعبيرات ودية مثل:"
            
            for category, expressions in human_expressions.items():
                if expressions and len(expressions) > 0:
                    example = random.choice(expressions)
                    system_message += f"\n- {example}"
        
        if contact_info:
            phone = contact_info.get("phone", "")
            email = contact_info.get("email", "")
            website = contact_info.get("website", "")
            system_message += f"\n\nمعلومات الاتصال بمجمع عمال مصر:\nهاتف/واتساب: {phone}\nبريد إلكتروني: {email}\nموقع إلكتروني: {website}"
            system_message += "\n\nأضف معلومات الاتصال هذه في نهاية ردك عندما يكون ذلك مناسبًا، خاصة مع الاستفسارات التي تتطلب تواصلاً مباشرًا."
        
        # ضبط معلمات النموذج وفقاً لوثائق API الرسمية
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False  # يمكن تعيينها إلى True للحصول على استجابة متدفقة
        }
        
        # تسجيل معلومات الطلب بدون المحتوى الكامل للنظام
        debug_payload = payload.copy()
        debug_payload["messages"][0]["content"] = "System message (abbreviated)..."
        logger.debug(f"إرسال طلب إلى DeepSeek API: {debug_payload}")
        
        # محاولة الاتصال بالـ API مع إعادة المحاولة عند الفشل
        for attempt in range(self.max_retries):
            try:
                # إرسال الطلب إلى API
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=30  # تحديد مهلة للاتصال لتجنب التعليق
                )
                
                # التحقق من نجاح الطلب
                response.raise_for_status()
                
                # تحليل الاستجابة كـ JSON
                result = response.json()
                logger.info(f"تم استلام رد من DeepSeek API بنجاح. Status: {response.status_code}")
                logger.debug(f"محتوى الرد (مختصر): {str(result)[:200]}...")
                return result
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"محاولة {attempt+1}/{self.max_retries} فشلت: {e}")
                
                if attempt < self.max_retries - 1:
                    # انتظار قبل إعادة المحاولة
                    time.sleep(self.retry_delay)
                else:
                    # فشلت جميع المحاولات
                    error_msg = f"فشلت جميع محاولات الاتصال بـ DeepSeek API: {e}"
                    logger.error(error_msg)
                    return {
                        "error": str(e),
                        "error_type": "connection_error",
                        "choices": [{"message": {"content": self._generate_fallback_response(user_message)}}]
                    }
            
            except Exception as e:
                error_msg = f"خطأ غير متوقع: {e}"
                logger.error(error_msg)
                return {
                    "error": str(e),
                    "error_type": "unexpected_error",
                    "choices": [{"message": {"content": self._generate_fallback_response(user_message)}}]
                }
        
        # لن يتم الوصول إلى هذه النقطة بسبب منطق إعادة المحاولة، ولكن نضيفها كاحتياط
        return {
            "error": "فشلت جميع محاولات الاتصال",
            "error_type": "max_retries_exceeded",
            "choices": [{"message": {"content": self._generate_fallback_response(user_message)}}]
        }
    
    def _generate_fallback_response(self, user_message: str) -> str:
        """
        إنشاء رد احتياطي عند فشل الاتصال بـ API
        
        :param user_message: رسالة المستخدم
        :return: رد احتياطي مناسب
        """
        # التحقق إذا كان السؤال يتعلق بالوظائف
        if any(keyword in user_message.lower() for keyword in ["وظيفة", "شغل", "عمل", "توظيف", "سيرة ذاتية", "مرتب", "راتب"]):
            return """
أهلاً بك! يسعدنا اهتمامك بفرص العمل في مجمع عمال مصر.

يمكنك التقديم للوظائف المتاحة من خلال عدة طرق:
• زيارة موقعنا الرسمي: https://www.omalmisr.com/ في قسم 'الوظائف'
• التقديم مباشرة عبر بوابة الخدمات: https://omalmisrservices.com/en/jobs
• التواصل معنا عبر واتساب (المقر الرئيسي): 01100901200

نوفر فرص عمل متنوعة في قطاعات: الصناعات الغذائية، الورقية، الملابس، الدواجن، والخدمات البترولية.

هل تبحث عن وظيفة في تخصص معين؟ أستطيع مساعدتك بتفاصيل أكثر عن المتطلبات والمؤهلات المطلوبة.
"""
        
        # التحقق إذا كان السؤال يتعلق بالاستثمار
        elif any(keyword in user_message.lower() for keyword in ["استثمار", "مشروع", "شراكة", "تمويل", "ربح", "عائد"]):
            return """
أهلاً بك! نشكر اهتمامك بالفرص الاستثمارية مع مجمع عمال مصر.

نوفر خدمات استثمارية متكاملة على ثلاث مراحل:
• الأولى: طرح الفرص والإنشاء
• الثانية: الإدارة والتشغيل
• الثالثة: التسويق والمبيعات

من أبرز مشروعاتنا الناجحة مشروع دواجن مصر (مدينة الثروة الداجنة) الذي يحقق عائداً استثمارياً يصل إلى 39% سنوياً.

للاطلاع على التفاصيل يمكنك زيارة موقعنا الرسمي: https://www.omalmisr.com/
أو بوابة خدمات الشركات: https://omalmisrservices.com/en/companies

• للتواصل المباشر:
📞 تليفون/واتساب: 01100901200
✉️ بريد إلكتروني: info@omalmisr.com

ما هو مجال الاستثمار الذي تفضله؟ يمكننا تقديم معلومات أكثر تفصيلاً عن الفرص المتاحة.
"""
        
        # رد عام إذا لم يكن هناك تصنيف واضح
        else:
            return """
أهلاً بك في مجمع عمال مصر!

يسعدنا تواصلك معنا. نحن منظومة صناعية واقتصادية تأسست عام 2010، وتطورت لتصبح شركة مساهمة مصرية بقيمة سوقية تتجاوز 1.5 مليار جنيه مصري.

نقدم مجموعة متنوعة من الخدمات تشمل:
• توفير وتدريب الكوادر البشرية
• الاستثمار الصناعي والزراعي
• خدمات للشركات والمصانع
• حلول متكاملة للمستثمرين

يمكنك زيارة موقعنا الرسمي للاطلاع على خدماتنا المتنوعة: https://www.omalmisr.com/

• للتواصل المباشر:
📞 تليفون/واتساب: 01100901200
✉️ بريد إلكتروني: info@omalmisr.com

كيف يمكنني مساعدتك اليوم؟
"""
    
    def extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        استخراج النص من استجابة API
        
        :param response: الاستجابة من DeepSeek API
        :return: النص المستخرج
        """
        try:
            if "error" in response:
                error_msg = f"خطأ في استجابة API: {response['error']}"
                logger.error(error_msg)
                
                # استخدام الرد الاحتياطي إذا كان متوفراً في الاستجابة
                if "choices" in response and len(response["choices"]) > 0:
                    fallback_response = response["choices"][0].get("message", {}).get("content", "")
                    if fallback_response:
                        logger.info("استخدام الرد الاحتياطي المضمن في الاستجابة")
                        return fallback_response
                
                # تقديم رد أكثر تفصيلاً بناءً على نوع الخطأ
                error_type = response.get("error_type", "")
                
                if "401" in str(response['error']) or "auth" in str(response['error']).lower():
                    # خطأ المصادقة - مفتاح API غير صالح
                    return "للأسف، هناك مشكلة في الاتصال بنظام الرد الآلي. يمكنك التواصل معنا مباشرة على رقم الهاتف: 01100901200 أو عبر البريد الإلكتروني: info@omalmisr.com وسيقوم فريقنا بالرد على استفسارك في أقرب وقت."
                elif "429" in str(response['error']) or "rate limit" in str(response['error']).lower():
                    # تجاوز حد الطلبات
                    return "عذراً، لدينا حالياً ضغط كبير على خدمة الرد الآلي. يمكنك معاودة المحاولة بعد قليل أو التواصل مباشرة مع فريق خدمة العملاء على الرقم: 01100901200."
                elif error_type == "connection_error":
                    # خطأ في الاتصال
                    return "عذراً، يوجد مشكلة مؤقتة في الاتصال بالخادم. يمكنك التواصل معنا مباشرة على الرقم: 01100901200 أو عبر البريد الإلكتروني: info@omalmisr.com وسنكون سعداء بخدمتك."
                else:
                    # أي خطأ آخر
                    return "عذراً، واجهنا صعوبة تقنية مؤقتة. يمكنك معاودة الاستفسار مرة أخرى أو التواصل معنا مباشرة على الرقم: 01100901200 لمساعدتك فوراً."
            
            # استخراج الرد من استجابة API
            if not response.get("choices"):
                logger.warning("تم استلام استجابة غير متوقعة من API: لا توجد اختيارات متاحة")
                return "عذراً، لم نتمكن من معالجة استفسارك. يرجى إعادة المحاولة أو التواصل معنا مباشرة."
            
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                logger.warning("تم استلام رد فارغ من API")
                return "عذراً، لم أتمكن من فهم استفسارك. هل يمكنك توضيح ما تحتاجه بخصوص مجمع عمال مصر؟"
                
            logger.debug(f"تم استخراج النص من استجابة API: {response_content[:100]}...")
            return response_content
            
        except Exception as e:
            error_msg = f"خطأ في استخراج النص: {e}"
            logger.error(error_msg)
            return "عذراً، حدث خطأ أثناء معالجة الرد. يمكنك التواصل معنا مباشرة على الرقم: 01100901200 وسنكون سعداء بمساعدتك."