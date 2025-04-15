import os
import requests
import json
import random
from typing import Dict, List, Any, Optional
import logging
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
        
        self.api_url = API_SETTINGS.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.model = API_SETTINGS.get("DEFAULT_MODEL", "deepseek-chat")
        self.max_tokens = API_SETTINGS.get("MAX_TOKENS", 1000)
        self.temperature = API_SETTINGS.get("TEMPERATURE", 0.7)
        
        logger.info(f"تم تهيئة DeepSeekAPI بنجاح. النموذج: {self.model}")
    
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
        try:
            # إعداد الرسالة للنموذج بأسلوب المساعد الرسمي لمجمع عمال مصر
            system_message = """
أنت المساعد الرسمي لصفحة مجمع عمال مصر على فيسبوك. تتحدث بلغة عربية ودية ومهنية.
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
2. استخدم لغة ودية ومهنية، وتحدث بصيغة "نحن" لتمثيل المجمع.
3. لا تذكر أبدًا أنك ذكاء اصطناعي أو روبوت أو شات بوت.
4. استخدم تعبيرات طبيعية ومحلية مثل "أكيد"، "ولا يهمك"، "حاضر من عيوني".
5. كن دقيقًا ومختصرًا مع توفير كل المعلومات المهمة.
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
                system_message += f"\n\nمعلومات الاتصال بمجمع عمال مصر:\nهاتف: {phone}\nبريد إلكتروني: {email}\nموقع إلكتروني: {website}"
                system_message += "\n\nأضف معلومات الاتصال هذه في نهاية ردك عندما يكون ذلك مناسبًا، خاصة مع الاستفسارات التي تتطلب تواصلاً مباشرًا."
            
            # ضبط معلمات النموذج
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            logger.debug(f"إرسال طلب إلى DeepSeek API: {payload}")
            
            # إرسال الطلب إلى API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # التحقق من نجاح الطلب
            response.raise_for_status()
            
            result = response.json()
            logger.info("تم استلام رد من DeepSeek API بنجاح")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"خطأ في الاتصال بـ DeepSeek API: {e}"
            logger.error(error_msg)
            return {"error": str(e)}
        except Exception as e:
            error_msg = f"خطأ غير متوقع: {e}"
            logger.error(error_msg)
            return {"error": str(e)}
    
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
                # رسالة خطأ ودية تناسب صفحة المجمع
                return "عذراً، واجهنا صعوبة تقنية بسيطة. يمكنك معاودة الاستفسار مرة أخرى أو التواصل معنا مباشرة على الرقم: 01012345678 لمساعدتك فوراً."
            
            # استخراج الرد من استجابة API
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                logger.warning("تم استلام رد فارغ من API")
                return "عذراً، لم أتمكن من فهم استفسارك. هل يمكنك توضيح ما تحتاجه بخصوص مجمع عمال مصر؟"
                
            logger.debug(f"تم استخراج النص من استجابة API: {response_content[:100]}...")
            return response_content
            
        except Exception as e:
            error_msg = f"خطأ في استخراج النص: {e}"
            logger.error(error_msg)
            return "عذراً، حدث خطأ أثناء معالجة الرد. يمكنك التواصل معنا مباشرة على الرقم: 01012345678 وسنكون سعداء بمساعدتك."


# نموذج بديل باستخدام OpenAI كمثال (معلق حاليًا)
"""
class OpenAIAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or API_SETTINGS.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("مفتاح API غير متوفر. يرجى تمريره للدالة أو تعيينه كمتغير بيئة OPENAI_API_KEY")
        
        # تهيئة مكتبة OpenAI
        import openai
        openai.api_key = self.api_key
        self.client = openai.OpenAI()
    
    def generate_response(self, user_message, user_category="", context="", human_expressions=None, contact_info=None):
        system_message = "أنت المساعد الرسمي لصفحة مجمع عمال مصر على فيسبوك. تتحدث بلغة عربية ودية ومهنية."
        
        # إضافة معلومات حسب فئة المستخدم والسياق
        # (مشابه للكود الأصلي)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response
        except Exception as e:
            print(f"خطأ في الاتصال بـ OpenAI API: {e}")
            return {"error": str(e)}
    
    def extract_response_text(self, response):
        # (مشابه للكود الأصلي)
"""