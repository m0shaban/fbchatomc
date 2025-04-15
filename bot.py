"""
الشات بوت الرسمي لمجمع عمال مصر
يقوم بالرد على استفسارات زوار صفحة مجمع عمال مصر على فيسبوك
سواء عبر الماسنجر أو تعليقات المنشورات
"""

import json
import re
import os
import random
import logging
from typing import Dict, List, Tuple, Optional, Any
from api import DeepSeekAPI
from config import BOT_SETTINGS, APP_SETTINGS

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=BOT_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

class ChatBot:
    """
    شات بوت ذكي للرد على استفسارات زوار صفحة مجمع عمال مصر على فيسبوك
    سواء عبر الماسنجر أو التعليقات
    """
    
    def __init__(self, data_file: str = None, api_key: Optional[str] = None):
        """
        تهيئة الشات بوت وتحميل البيانات من ملف JSON
        
        :param data_file: مسار ملف البيانات بصيغة JSON
        :param api_key: مفتاح API لخدمة DeepSeek (اختياري)
        """
        self.data_file = data_file or BOT_SETTINGS.get("DATA_FILE", "data.json")
        self.prompts = []
        self.human_expressions = {}
        self.contact_info = {}
        self.requires_human_contact = []
        self.user_categories = []
        self.job_sectors = []
        self.personalize_response = BOT_SETTINGS.get("PERSONALIZE_RESPONSE", True)
        self.similarity_threshold = BOT_SETTINGS.get("SIMILARITY_THRESHOLD", 0.4)
        
        # بيانات الخدمات والروابط
        self.service_links = {}
        self.service_categories = {}
        
        # تحميل البيانات من ملف JSON
        self.load_data()
        
        # تهيئة واجهة API
        self.api = DeepSeekAPI(api_key)
        
        # تاريخ المحادثات السابقة (يمكن تطويره لحفظ سجل المحادثات)
        self.conversation_history = []
        
        # تعيين مصدر المحادثة الحالي
        self.conversation_source = "messenger"  # messenger أو facebook_comment
        
        logger.info(f"تم تهيئة ChatBot بنجاح. ملف البيانات: {self.data_file}")
    
    def load_data(self) -> None:
        """
        تحميل البيانات من ملف JSON
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.prompts = data.get("prompts", [])
                self.human_expressions = data.get("human_expressions", {})
                self.contact_info = data.get("contact_info", {})
                self.requires_human_contact = data.get("requires_human_contact", [])
                self.user_categories = data.get("user_categories", [])
                self.job_sectors = data.get("job_sectors", [])
                self.personalize_response = data.get("personalize_response", self.personalize_response)
                
                # تحميل بيانات الخدمات والروابط
                self.service_links = data.get("service_links", {})
                self.service_categories = data.get("service_categories", {})
                
            logger.info(f"تم تحميل {len(self.prompts)} سؤال وجواب من قاعدة البيانات")
            
            if self.human_expressions:
                logger.info(f"تم تحميل تعبيرات بشرية لـ {len(self.human_expressions)} فئة مختلفة")
            
            if self.user_categories:
                logger.info(f"تم تحميل {len(self.user_categories)} فئة من المستخدمين")
            
            if self.service_links:
                logger.info(f"تم تحميل {len(self.service_links)} رابط لخدمات المجمع")
            
        except FileNotFoundError:
            error_msg = f"خطأ: لم يتم العثور على ملف البيانات '{self.data_file}'"
            logger.error(error_msg)
            print(error_msg)
        except json.JSONDecodeError:
            error_msg = f"خطأ: ملف البيانات '{self.data_file}' ليس بصيغة JSON صالحة"
            logger.error(error_msg)
            print(error_msg)
        except Exception as e:
            error_msg = f"خطأ غير متوقع أثناء تحميل البيانات: {e}"
            logger.error(error_msg)
            print(error_msg)
    
    def set_conversation_source(self, source: str) -> None:
        """
        تعيين مصدر المحادثة (ماسنجر أو تعليق فيسبوك)
        
        :param source: مصدر المحادثة ("messenger" أو "facebook_comment")
        """
        if source in ["messenger", "facebook_comment"]:
            self.conversation_source = source
            logger.debug(f"تم تعيين مصدر المحادثة: {source}")
        else:
            logger.warning(f"مصدر محادثة غير صالح: {source}. استخدام الافتراضي: messenger")
            self.conversation_source = "messenger"
    
    def _get_random_expression(self, category: str) -> str:
        """
        الحصول على تعبير عشوائي من فئة معينة
        
        :param category: فئة التعبير (greetings, positive_responses, إلخ)
        :return: تعبير عشوائي أو نص فارغ إذا لم تكن الفئة موجودة
        """
        expressions = self.human_expressions.get(category, [])
        
        if expressions and len(expressions) > 0:
            return random.choice(expressions)
        
        return ""
    
    def _detect_user_category(self, message: str) -> str:
        """
        محاولة تحديد فئة المستخدم من رسالته
        
        :param message: رسالة المستخدم
        :return: فئة المستخدم المحتملة
        """
        message = message.lower()
        
        # كلمات مفتاحية للباحثين عن عمل
        job_seekers_keywords = [
            "وظيفة", "عمل", "توظيف", "شغل", "مرتب", "راتب", "تقديم", "سيرة ذاتية", 
            "خبرة", "خريج", "تدريب", "تعيين", "مؤهل", "cv", "فرصة"
        ]
        
        # كلمات مفتاحية للمستثمرين
        investors_keywords = [
            "استثمار", "مشروع", "تمويل", "شراكة", "رأس مال", "ربح", "عائد", "فرصة استثمارية",
            "تعاون", "رجل أعمال", "مستثمر", "مشروع"
        ]
        
        # كلمات مفتاحية للصحفيين
        media_keywords = [
            "صحفي", "إعلام", "مقابلة", "تصريح", "خبر", "تقرير", "مجلة", "جريدة", "تلفزيون", 
            "راديو", "إذاعة", "تغطية", "صحافة", "نشر", "مقال"
        ]
        
        # كلمات مفتاحية للشركات والجهات
        companies_keywords = [
            "شركة", "مؤسسة", "جهة", "مصنع", "تعاون", "شراكة", "تفاهم", "بروتوكول", 
            "اتفاقية", "مذكرة", "تنسيق", "جامعة", "معهد", "مدرسة"
        ]
        
        # البحث عن الكلمات المفتاحية في الرسالة
        for keyword in job_seekers_keywords:
            if keyword in message:
                logger.debug(f"تم تصنيف المستخدم كـ 'باحث عن عمل' بناءً على الكلمة المفتاحية: {keyword}")
                return "باحث عن عمل"
        
        for keyword in investors_keywords:
            if keyword in message:
                logger.debug(f"تم تصنيف المستخدم كـ 'مستثمر' بناءً على الكلمة المفتاحية: {keyword}")
                return "مستثمر"
        
        for keyword in media_keywords:
            if keyword in message:
                logger.debug(f"تم تصنيف المستخدم كـ 'صحفي' بناءً على الكلمة المفتاحية: {keyword}")
                return "صحفي"
        
        for keyword in companies_keywords:
            if keyword in message:
                logger.debug(f"تم تصنيف المستخدم كـ 'شركة' بناءً على الكلمة المفتاحية: {keyword}")
                return "شركة"
        
        # إذا لم يتم تحديد الفئة، أعد فئة افتراضية
        logger.debug("لم يتم تحديد فئة محددة للمستخدم")
        return ""
    
    def _detect_service_request(self, message: str) -> Dict:
        """
        تحديد إذا كان المستخدم يطلب خدمة معينة ويحتاج رابط
        
        :param message: رسالة المستخدم
        :return: معلومات الخدمة المطلوبة (العنوان، الوصف، الرابط) إن وجدت
        """
        message = message.lower()
        
        # كلمات مفتاحية للبحث عن وظيفة أو تقديم السيرة الذاتية
        job_keywords = [
            "وظيفة", "عمل", "توظيف", "شغل", "سيرة ذاتية", "cv", "تقديم طلب", "تقديم",
            "التوظيف", "التقديم للوظائف", "البحث عن وظيفة", "فرص عمل"
        ]
        
        # كلمات مفتاحية للبحث عن عمال (للشركات)
        workers_keywords = [
            "عمال", "توفير عمال", "موظفين", "توظيف عمالة", "أحتاج عمال", "عمالة مؤهلة",
            "باحث عن عمال", "طلب عمالة", "فنيين", "موارد بشرية", "توفير موظفين"
        ]
        
        # كلمات مفتاحية لخدمات الشركات
        companies_keywords = [
            "خدمات شركات", "خدمات للشركات", "استثمار", "تأسيس شركة", "تأسيس مصنع",
            "استشارات", "دراسة جدوى", "فرص استثمارية", "تسويق منتجات", "مواد خام"
        ]
        
        # كلمات مفتاحية لخدمة فض المنازعات
        dispute_keywords = [
            "شكوى", "منازعة", "خلاف", "مشكلة قانونية", "نزاع", "فض منازعات", "تسوية",
            "مشكلة مع شركة", "قضية", "خلاف عمالي", "شكوى عمالية"
        ]
        
        # البحث عن الخدمة المطلوبة
        if any(keyword in message for keyword in job_keywords):
            logger.debug("تم تحديد طلب خدمة: تقديم السيرة الذاتية")
            if "service_categories" in self.__dict__ and "job_submission" in self.service_categories:
                return self.service_categories["job_submission"]
            elif "service_links" in self.__dict__ and "jobs" in self.service_links:
                return {
                    "title": "تقديم السيرة الذاتية",
                    "description": "تقديم طلبات التوظيف والسير الذاتية للمتقدمين",
                    "link": self.service_links["jobs"]
                }
        
        if any(keyword in message for keyword in workers_keywords):
            logger.debug("تم تحديد طلب خدمة: البحث عن عمال")
            if "service_categories" in self.__dict__ and "workforce" in self.service_categories:
                return self.service_categories["workforce"]
            elif "service_links" in self.__dict__ and "workers" in self.service_links:
                return {
                    "title": "البحث عن عمال",
                    "description": "خدمة للشركات للبحث عن عمال مؤهلين",
                    "link": self.service_links["workers"]
                }
        
        if any(keyword in message for keyword in companies_keywords):
            logger.debug("تم تحديد طلب خدمة: خدمات الشركات")
            if "service_categories" in self.__dict__ and "company_services" in self.service_categories:
                return self.service_categories["company_services"]
            elif "service_links" in self.__dict__ and "companies" in self.service_links:
                return {
                    "title": "خدمات الشركات",
                    "description": "خدمات متكاملة للشركات والمستثمرين",
                    "link": self.service_links["companies"]
                }
        
        if any(keyword in message for keyword in dispute_keywords):
            logger.debug("تم تحديد طلب خدمة: فض المنازعات")
            if "service_categories" in self.__dict__ and "dispute_resolution" in self.service_categories:
                return self.service_categories["dispute_resolution"]
            elif "service_links" in self.__dict__ and "dispute" in self.service_links:
                return {
                    "title": "بوابة فض المنازعات",
                    "description": "بوابة إلكترونية لحل وتسوية المنازعات بين المنشآت والعاملين",
                    "link": self.service_links["dispute"]
                }
        
        # إذا لم يتم تحديد خدمة محددة
        logger.debug("لم يتم تحديد طلب خدمة محدد")
        return {}
    
    def search_knowledge_base(self, user_message: str) -> Tuple[Optional[Dict], float]:
        """
        البحث في قاعدة المعرفة عن أقرب سؤال للرسالة المستلمة
        
        :param user_message: رسالة المستخدم
        :return: أقرب سؤال وجواب ونسبة التطابق
        """
        best_match = None
        best_score = 0.0
        
        # تنظيف رسالة المستخدم
        user_message = user_message.strip().lower()
        
        for prompt in self.prompts:
            # حساب نسبة التطابق البسيطة (يمكن تحسينها باستخدام خوارزميات أكثر تعقيدًا)
            score = self._calculate_similarity(user_message, prompt["question"].lower())
            
            if score > best_score:
                best_score = score
                best_match = prompt
        
        logger.debug(f"أفضل تطابق: {best_match['id'] if best_match else None} بنسبة: {best_score:.2f}")
        return best_match, best_score
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        حساب نسبة التشابه بين نصين باستخدام خوارزمية بسيطة
        
        :param text1: النص الأول
        :param text2: النص الثاني
        :return: نسبة التشابه (0.0 - 1.0)
        """
        # تقسيم النصوص إلى كلمات
        words1 = set(re.findall(r'\w+', text1))
        words2 = set(re.findall(r'\w+', text2))
        
        # حساب عدد الكلمات المشتركة
        common_words = words1.intersection(words2)
        
        # إذا لم تكن هناك كلمات مشتركة، عُد 0
        if not words1 or not words2:
            return 0.0
        
        # حساب معامل جاكارد: عدد الكلمات المشتركة / مجموع الكلمات الفريدة
        similarity = len(common_words) / len(words1.union(words2))
        
        return similarity
    
    def needs_human_contact(self, message: str) -> bool:
        """
        تحديد ما إذا كانت الرسالة تتطلب تواصل بشري
        
        :param message: رسالة المستخدم
        :return: True إذا كانت الرسالة تتطلب تواصل بشري
        """
        message = message.lower()
        
        # التحقق من وجود أي من الكلمات المفتاحية التي تتطلب تواصل بشري
        for keyword in self.requires_human_contact:
            if keyword.lower() in message:
                logger.info(f"تم تحديد حاجة للتواصل البشري بناءً على الكلمة المفتاحية: {keyword}")
                return True
        
        return False
    
    def get_human_contact_message(self) -> str:
        """
        إنشاء رسالة للتواصل البشري بأسلوب ودي
        
        :return: رسالة التواصل البشري
        """
        phone = self.contact_info.get("phone", "01012345678")
        
        # قائمة من الرسائل المختلفة للتواصل البشري
        contact_messages = [
            f"للتواصل معنا مباشرة، يُرجى الاتصال على الرقم: {phone}",
            f"إذا حابب تتواصل مباشرة مع أحد ممثلينا، راسلنا أو اتصل على: {phone}",
            f"تقدر تتواصل مباشرة مع فريقنا على الرقم: {phone}",
            f"للتواصل المباشر مع أحد مستشارينا الآن، اتصل على: {phone}",
            f"حابب تحكي مع شخص من فريقنا؟ تواصل معنا على: {phone}"
        ]
        
        # اختيار رسالة عشوائية
        contact_message = f"\n\n{random.choice(contact_messages)}"
        logger.debug(f"تم إنشاء رسالة التواصل البشري: {contact_message}")
        return contact_message
    
    def generate_service_link_message(self, service_info: Dict) -> str:
        """
        إنشاء رسالة تحتوي على رابط الخدمة المطلوبة
        
        :param service_info: معلومات الخدمة المطلوبة
        :return: رسالة مع رابط الخدمة
        """
        if not service_info:
            return ""
        
        title = service_info.get("title", "")
        description = service_info.get("description", "")
        link = service_info.get("link", "")
        
        if not link:
            return ""
        
        # اختيار تعبير عشوائي مناسب
        intro = self._get_random_expression("positive_responses") or "بكل تأكيد!"
        
        # إنشاء رسالة مخصصة حسب نوع الخدمة
        if "تقديم السيرة الذاتية" in title or "jobs" in link:
            response = f"{intro} يمكنك تقديم السيرة الذاتية والتقدم للوظائف عبر الرابط التالي:\n{link}\n\nهذه المنصة تتيح لك تسجيل بياناتك ومؤهلاتك وخبراتك، وستتلقى إشعاراً عند توفر وظائف تناسب مهاراتك."
        
        elif "البحث عن عمال" in title or "workers" in link:
            response = f"{intro} إذا كنت تبحث عن عمال مؤهلين لمنشأتك، يمكنك الاستفادة من خدمة توفير العمالة المدربة عبر الرابط التالي:\n{link}\n\nيمكنك تحديد احتياجاتك من العمالة والمهارات المطلوبة، وسيقوم فريقنا بتوفير الكوادر المناسبة."
        
        elif "خدمات الشركات" in title or "companies" in link:
            response = f"{intro} يمكنك الاطلاع على الخدمات المتكاملة التي نقدمها للشركات والمستثمرين عبر الرابط التالي:\n{link}\n\nنقدم خدمات الاستثمار الصناعي والزراعي، دراسات الجدوى الاقتصادية، الشراكات الاستراتيجية، العقارات الصناعية، والعديد من الخدمات الأخرى."
        
        elif "فض المنازعات" in title or "dispute" in link:
            response = f"{intro} يمكنك الاستفادة من بوابة فض المنازعات الإلكترونية عبر الرابط التالي:\n{link}\n\nهذه البوابة متخصصة في حل وتسوية المنازعات الناشئة بين المنشآت أو بين المنشآت والعاملين بها، من خلال خبراء ومستشارين قانونيين دون اللجوء للجهات القضائية."
        
        else:
            response = f"{intro} يمكنك زيارة الرابط التالي للاطلاع على {title}:\n{link}\n\n{description}"
        
        logger.debug(f"تم إنشاء رسالة رابط الخدمة: {title}")
        return response
    
    def format_greeting_by_source(self) -> str:
        """
        إنشاء تحية مناسبة بناءً على مصدر المحادثة (ماسنجر أو تعليق فيسبوك)
        
        :return: رسالة التحية المناسبة
        """
        greeting = ""
        
        if self.conversation_source == "messenger":
            # تحية بداية محادثة ماسنجر
            messenger_greeting = self._get_random_expression("greetings") or "مرحباً بك في الصفحة الرسمية لمجمع عمال مصر!"
            greeting = f"{messenger_greeting} أنا المساعد الرسمي للمجمع. كيف يمكنني خدمتك اليوم؟"
        else:
            # تحية أقصر لتعليقات الفيسبوك
            comment_greeting = "مرحباً، أنا المساعد الرسمي لمجمع عمال مصر."
            greeting = comment_greeting
        
        return greeting
    
    def sanitize_response(self, response: str) -> str:
        """
        تنقية الرد من أي إشارات للذكاء الاصطناعي
        
        :param response: الرد الأصلي
        :return: الرد بعد التنقية
        """
        # قائمة بالعبارات التي يجب استبدالها
        ai_terms = [
            "ذكاء اصطناعي", "روبوت", "بوت", "AI", "bot", "شات بوت", "chatbot", 
            "نموذج لغوي", "language model", "assistant", "مساعد آلي"
        ]
        
        sanitized_response = response
        
        # استبدال أي إشارة للذكاء الاصطناعي
        for term in ai_terms:
            sanitized_response = re.sub(
                r'\b' + re.escape(term) + r'\b', 
                "المساعد الرسمي لمجمع عمال مصر", 
                sanitized_response, 
                flags=re.IGNORECASE
            )
        
        return sanitized_response
    
    def generate_messenger_response(self, user_message: str) -> str:
        """
        توليد رد لرسالة ماسنجر
        
        :param user_message: رسالة المستخدم
        :return: الرد المُولد
        """
        # تعيين مصدر المحادثة كماسنجر
        self.conversation_source = "messenger"
        
        # توليد الرد العام
        response = self.generate_response(user_message)
        
        # تخصيص الرد للماسنجر
        # إضافة تحية ترحيبية إذا كانت أول رسالة في المحادثة
        if len(self.conversation_history) <= 2:  # الرسالة الأولى + الرد عليها
            greeting = self.format_greeting_by_source()
            if not response.startswith(greeting) and not any(expr in response for expr in self.human_expressions.get("greetings", [])):
                response = f"{greeting}\n\n{response}"
        
        return response
    
    def generate_comment_response(self, comment_text: str) -> str:
        """
        توليد رد لتعليق فيسبوك
        
        :param comment_text: نص التعليق
        :return: الرد المُولد
        """
        # تعيين مصدر المحادثة كتعليق فيسبوك
        self.conversation_source = "facebook_comment"
        
        # توليد الرد العام
        response = self.generate_response(comment_text)
        
        # تخصيص الرد لتعليقات الفيسبوك (أكثر اختصاراً)
        # إضافة تحية قصيرة في بداية الرد
        greeting = self.format_greeting_by_source()
        if not response.startswith(greeting) and not any(expr in response for expr in self.human_expressions.get("greetings", [])):
            response = f"{greeting}\n\n{response}"
        
        # التأكد من أن الرد لا يشير إلى أنه ذكاء اصطناعي
        response = self.sanitize_response(response)
        
        return response
    
    def generate_response(self, user_message: str) -> str:
        """
        توليد رد على رسالة المستخدم بأسلوب المساعد الرسمي لمجمع عمال مصر
        
        :param user_message: رسالة المستخدم
        :return: الرد المُولد
        """
        # إضافة رسالة المستخدم إلى تاريخ المحادثة
        self.conversation_history.append({"role": "user", "message": user_message})
        logger.info(f"استلام رسالة من المستخدم ({self.conversation_source}): {user_message[:50]}...")
        
        # محاولة تحديد فئة المستخدم
        user_category = self._detect_user_category(user_message)
        
        # البحث عن طلب خدمة محددة تحتاج لرابط
        service_info = self._detect_service_request(user_message)
        
        # إذا كان المستخدم يطلب خدمة محددة، قم بإرجاع رابط الخدمة مباشرة
        if service_info and "link" in service_info:
            service_link_message = self.generate_service_link_message(service_info)
            if service_link_message:
                # إضافة رسالة التواصل البشري إذا لزم الأمر
                if self.needs_human_contact(user_message):
                    service_link_message += self.get_human_contact_message()
                
                # إضافة رد البوت إلى تاريخ المحادثة
                self.conversation_history.append({"role": "bot", "message": service_link_message})
                logger.info(f"إرسال رد خدمة مباشر: {service_info.get('title', '')}")
                return service_link_message
        
        # البحث في قاعدة المعرفة
        best_match, score = self.search_knowledge_base(user_message)
        
        # حفظ السياق للنموذج اللغوي
        context = ""
        final_response = ""
        
        # اختيار تعبير ترحيبي مناسب لفئة المستخدم
        greeting = ""
        if user_category == "باحث عن عمل":
            greeting = self._get_random_expression("job_seekers_response") or ""
        elif user_category == "مستثمر":
            greeting = self._get_random_expression("investors_response") or ""
        else:
            # إذا لم يتم تحديد فئة، استخدم تعبير ترحيبي عام
            if random.random() < 0.5:  # 50% فرصة لإضافة تعبير ترحيبي
                greeting = self._get_random_expression("greetings") or ""
        
        # تحديد نوع الرد بناءً على نسبة التطابق
        if best_match and score > self.similarity_threshold:
            # إضافة أفضل تطابق للسياق
            context = f"سؤال مشابه: {best_match['question']}\nإجابة نموذجية: {best_match['answer']}"
            logger.debug(f"تم العثور على تطابق جيد (نسبة: {score:.2f}). السؤال: {best_match['question'][:50]}...")
            
            # إضافة معلومات الخدمة المطلوبة إلى السياق إن وجدت
            if service_info:
                context += f"\n\nالمستخدم قد يحتاج معلومات عن: {service_info.get('title', '')}"
                if 'description' in service_info:
                    context += f"\nوصف الخدمة: {service_info['description']}"
                if 'link' in service_info:
                    context += f"\nرابط الخدمة: {service_info['link']}"
            
            # إضافة معلومات عن مصدر المحادثة
            context += f"\n\nمصدر المحادثة: {self.conversation_source}"
            
            # استخدام النموذج اللغوي مع السياق المناسب
            api_response = self.api.generate_response(
                user_message,
                user_category,
                context,
                self.human_expressions,
                self.contact_info
            )
            final_response = self.api.extract_response_text(api_response)
        else:
            logger.debug(f"لم يتم العثور على تطابق جيد (أفضل نسبة: {score:.2f})")
            # إذا لم يكن هناك تطابق جيد، استخدم فقط النموذج اللغوي
            # ولكن أضف بعض المعلومات العامة من قاعدة البيانات كسياق
            sample_info = ""
            if self.prompts and len(self.prompts) > 2:
                # اختيار ثلاثة أسئلة عشوائية من قاعدة المعرفة لتوفير معلومات عامة عن المجمع
                random_samples = random.sample(self.prompts, min(3, len(self.prompts)))
                for sample in random_samples:
                    sample_info += f"معلومة: {sample['question']} - {sample['answer']}\n"
                
                context = f"معلومات عامة عن مجمع عمال مصر يمكن الاستفادة منها:\n{sample_info}"
                
                # إضافة معلومات الخدمة المطلوبة إلى السياق إن وجدت
                if service_info:
                    context += f"\n\nالمستخدم قد يحتاج معلومات عن: {service_info.get('title', '')}"
                    if 'description' in service_info:
                        context += f"\nوصف الخدمة: {service_info['description']}"
                    if 'link' in service_info:
                        context += f"\nرابط الخدمة: {service_info['link']}"
                
                # إضافة معلومات عن مصدر المحادثة
                context += f"\n\nمصدر المحادثة: {self.conversation_source}"
            
            # استخدام النموذج اللغوي لتوليد رد
            api_response = self.api.generate_response(
                user_message,
                user_category,
                context,
                self.human_expressions,
                self.contact_info
            )
            final_response = self.api.extract_response_text(api_response)
        
        # إذا كان الرد لا يحتوي على الرابط المطلوب، أضفه للرد
        if service_info and 'link' in service_info and service_info['link'] not in final_response:
            additional_info = f"\n\nيمكنك زيارة الرابط التالي للمزيد من المعلومات: {service_info['link']}"
            final_response += additional_info
            logger.debug(f"تمت إضافة الرابط المفقود: {service_info['link']}")
        
        # إضافة رسالة التواصل البشري إذا لزم الأمر
        if self.needs_human_contact(user_message) and "اتصل على" not in final_response and "تواصل" not in final_response:
            final_response += self.get_human_contact_message()
            logger.debug("تمت إضافة معلومات التواصل البشري للرد")
        
        # التأكد من أن الرد لا يشير إلى أن المجيب هو ذكاء اصطناعي
        final_response = self.sanitize_response(final_response)
        
        # إضافة رد البوت إلى تاريخ المحادثة
        self.conversation_history.append({"role": "bot", "message": final_response})
        logger.info(f"تم إرسال رد بطول: {len(final_response)} حرف")
        
        return final_response
    
    def save_conversation_history(self, filename: str = "conversations.json") -> bool:
        """
        حفظ تاريخ المحادثة في ملف JSON
        
        :param filename: اسم الملف
        :return: True إذا تم الحفظ بنجاح
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=4)
            logger.info(f"تم حفظ تاريخ المحادثة بنجاح في الملف: {filename}")
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ تاريخ المحادثة: {e}")
            return False


# نموذج لاستخدام المساعد الرسمي لمجمع عمال مصر
def main():
    """
    دالة رئيسية تعرض كيفية استخدام المساعد الرسمي لمجمع عمال مصر
    """
    print("جاري تهيئة المساعد الرسمي لمجمع عمال مصر...")
    
    # إنشاء كائن من المساعد الرسمي
    bot = ChatBot()
    
    # طلب نوع الخدمة: ماسنجر أو تعليقات
    service_type = input("اختر نوع الخدمة (1: ماسنجر، 2: تعليقات فيسبوك): ")
    
    if service_type == "2":
        bot.set_conversation_source("facebook_comment")
        print("\nوضع معالجة تعليقات الفيسبوك")
    else:
        bot.set_conversation_source("messenger")
        print("\nوضع الماسنجر")
    
    # استخدام تعبير ترحيبي مناسب
    greeting = bot.format_greeting_by_source()
    print(f"\n{greeting}")
    
    if bot.conversation_source == "messenger":
        print("كيف يمكنني خدمتك اليوم؟")
    
    print("(اكتب 'خروج' للخروج)")
    
    while True:
        # استقبال رسالة المستخدم
        user_input = input("\nأنت: ")
        
        # التحقق من الخروج
        if user_input.lower() in ['خروج', 'exit', 'quit']:
            conclusion = bot._get_random_expression("conclusions") or "شكرًا لتواصلك مع مجمع عمال مصر. نتشرف بخدمتك دائماً!"
            print(f"\nالمساعد الرسمي: {conclusion}")
            
            # حفظ تاريخ المحادثة قبل الخروج
            bot.save_conversation_history()
            break
        
        # توليد الرد حسب نوع الخدمة
        if bot.conversation_source == "messenger":
            response = bot.generate_messenger_response(user_input)
        else:
            response = bot.generate_comment_response(user_input)
        
        # عرض الرد
        print(f"\nالمساعد الرسمي: {response}")


if __name__ == "__main__":
    main()