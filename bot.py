"""
الشات بوت الرسمي لمجمع عمال مصر - محمد سلامة
يقوم بالرد على استفسارات زوار صفحة مجمع عمال مصر على فيسبوك
سواء عبر الماسنجر أو تعليقات المنشورات
"""

import json
import re
import os
import random
import logging
import datetime
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
        self.bot_name = "محمد سلامة"  # اسم الشات بوت
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
        
        # تاريخ المحادثات السابقة يتضمن الآن أسماء المستخدمين
        self.conversation_history = {}
        
        # حالة المحادثة الحالية
        self.conversation_state = {}
        
        # تعيين مصدر المحادثة الحالي
        self.conversation_source = "messenger"  # messenger أو facebook_comment

        # إعدادات الاستمرارية في المحادثة
        self.continue_conversation = BOT_SETTINGS.get("CONTINUE_CONVERSATION", True)
        self.continue_phrases = [
            "هل تحتاج مزيداً من المعلومات؟",
            "هل لديك أسئلة أخرى؟",
            "هل ترغب في معرفة المزيد؟",
            "هل تريد الاستمرار في المحادثة؟",
            "هل أستطيع مساعدتك في شيء آخر؟"
        ]
        
        # أسئلة للحصول على اسم المستخدم
        self.name_questions = [
            "مرحباً! أنا محمد سلامة، المساعد الرسمي لمجمع عمال مصر. ما هو اسمك الكريم؟",
            "أهلاً وسهلاً! أنا محمد سلامة من مجمع عمال مصر. قبل أن نبدأ، ممكن أعرف اسم حضرتك؟",
            "السلام عليكم! معك محمد سلامة من مجمع عمال مصر. يشرفني التعرف على اسمك الكريم.",
            "مرحباً بك في مجمع عمال مصر! أنا محمد سلامة مساعدك الشخصي. ما هو اسمك؟"
        ]
        
        logger.info(f"تم تهيئة ChatBot بنجاح. اسم الشات بوت: {self.bot_name}، ملف البيانات: {self.data_file}")
    
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
    
    def _is_continuation_message(self, message: str) -> bool:
        """
        تحديد ما إذا كانت الرسالة استجابة للاستمرار في المحادثة
        
        :param message: رسالة المستخدم
        :return: True إذا كانت الرسالة تشير إلى الاستمرار، False إذا كانت تشير إلى الإنهاء
        """
        # كلمات مفتاحية تشير إلى الاستمرار
        continue_keywords = [
            "نعم", "أيوة", "اه", "أكيد", "استمر", "أكمل", "طبعا", "بالتأكيد", "حابب", "عايز", 
            "أيوه", "حاضر", "تمام", "موافق", "ممكن", "مزيد", "المزيد"
        ]
        
        # كلمات مفتاحية تشير إلى الإنهاء
        end_keywords = [
            "لا", "شكرا", "خلاص", "كفاية", "متشكر", "ممنون", "إنهاء", "انهاء", "كفى", 
            "كده تمام", "هذا كل شيء", "مش عايز"
        ]
        
        message = message.strip().lower()
        
        # التحقق من كلمات الاستمرار
        for keyword in continue_keywords:
            if keyword in message:
                logger.debug(f"تم تحديد رسالة استمرار: {message}")
                return True
        
        # التحقق من كلمات الإنهاء
        for keyword in end_keywords:
            if keyword in message:
                logger.debug(f"تم تحديد رسالة إنهاء: {message}")
                return False
        
        # إذا لم يتم تحديد النية بوضوح، افترض أنها استمرار (الرسالة تحتوي على سؤال جديد)
        logger.debug(f"لم يتم تحديد نية الاستمرار بوضوح، اعتبارها سؤال جديد: {message}")
        return True
    
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
        return len(common_words) / len(words1.union(words2))
    
    def _is_asking_for_name(self, user_id: str) -> bool:
        """
        التحقق مما إذا كنا في مرحلة سؤال المستخدم عن اسمه
        
        :param user_id: معرف المستخدم
        :return: True إذا كنا في مرحلة طلب الاسم
        """
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {"awaiting_name": True}
            return True
        
        return self.conversation_state.get(user_id, {}).get("awaiting_name", False)
    
    def _save_user_name(self, user_id: str, user_message: str) -> str:
        """
        حفظ اسم المستخدم وإعادة رد ترحيبي
        
        :param user_id: معرف المستخدم
        :param user_message: رسالة المستخدم (اسمه)
        :return: رد ترحيبي
        """
        # استخراج الاسم من الرسالة
        name = self._extract_name(user_message)
        
        # حفظ الاسم في تاريخ المحادثة
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {}
        
        self.conversation_history[user_id]["user_name"] = name
        
        # تحديث حالة المحادثة
        self.conversation_state[user_id]["awaiting_name"] = False
        
        logger.info(f"تم حفظ اسم المستخدم {user_id}: {name}")
        
        # إنشاء رد ترحيبي يتضمن اسم المستخدم بأسلوب موظف حقيقي
        greetings = [
            f"أهلاً بك {name}! أنا من فريق العمل في مجمع عمال مصر. كيف يمكنني مساعدتك اليوم؟",
            f"مرحباً {name}! سعيد بالتحدث معك. أنا أعمل في مجمع عمال مصر وجاهز لمساعدتك في أي استفسار.",
            f"أهلاً وسهلاً {name}! شكراً لتواصلك مع مجمع عمال مصر. أخبرني كيف يمكنني خدمتك؟",
            f"مرحباً {name}! أنا من فريق خدمة العملاء بمجمع عمال مصر. تحت أمرك في أي استفسار."
        ]
        
        return random.choice(greetings)
    
    def _extract_name(self, message: str) -> str:
        """
        استخراج الاسم من رسالة المستخدم
        
        :param message: رسالة المستخدم
        :return: الاسم المستخرج
        """
        # تنظيف الرسالة من كلمات المجاملة المعتادة
        words_to_remove = [
            "انا", "أنا", "اسمي", "إسمي", "اسم", "إسم", "يا", 
            "سيد", "سيدة", "دكتور", "مهندس", "استاذ", "أستاذ"
        ]
        
        message = message.strip()
        
        # حذف علامات الترقيم الشائعة
        message = re.sub(r'[.!?,;:"\'،]', ' ', message)
        
        # استبدال الكلمات التي تريد حذفها بمسافة
        for word in words_to_remove:
            message = re.sub(r'\b' + re.escape(word) + r'\b', ' ', message, flags=re.IGNORECASE)
        
        # تنظيف المسافات المتعددة
        message = re.sub(r'\s+', ' ', message).strip()
        
        # إذا كانت الرسالة فارغة بعد التنظيف
        if not message:
            return "صديقي العزيز"
        
        # إذا كانت الرسالة تحتوي على عدة كلمات، خذ أول كلمتين كحد أقصى
        words = message.split()
        if len(words) > 2:
            return " ".join(words[:2])
        
        return message
    
    def _get_user_name(self, user_id: str) -> str:
        """
        الحصول على اسم المستخدم من تاريخ المحادثة
        
        :param user_id: معرف المستخدم
        :return: اسم المستخدم أو نص فارغ إذا لم يكن متوفرًا
        """
        return self.conversation_history.get(user_id, {}).get("user_name", "")
    
    def _enhance_formatting(self, text: str) -> str:
        """
        تحسين تنسيق النص بإضافة رموز وتنسيقات
        
        :param text: النص المراد تحسينه
        :return: النص بعد التنسيق
        """
        # تنسيق العناوين (استبدال ### بتنسيق أفضل)
        text = re.sub(r'(^|\n)###\s*(.*?)(\s*:)?\s*###', r'\1• *\2*:', text)
        text = re.sub(r'(^|\n)###\s*(.*?)(\s*:)?(\s*)', r'\1• *\2*:', text)
        
        # تنسيق العناوين العادية
        text = re.sub(r'(^|\n)([^:\n]+):(\s*\n)', r'\1• *\2*:\3', text)
        
        # إضافة رموز للنقاط
        text = re.sub(r'(\n|^)(\d+)[.)] ', r'\1\2️⃣ ', text)
        
        # إضافة رموز للمزايا والخدمات
        text = re.sub(r'(\n|^)[-*] ', r'\1✅ ', text)
        
        # تمييز الكلمات المهمة (بدون تكرار تمييز كلمات ممزة بالفعل)
        important_words = [
            "مجمع عمال مصر", "خدمات", "استثمار", "فرص عمل", "تسجيل", 
            "مشروع", "دراسة جدوى", "توظيف", "شراكة", "عائد"
        ]
        
        # إنشاء نسخة من النص للعمل عليها
        formatted_text = text
        
        for word in important_words:
            # التأكد من عدم تمييز كلمة ممزة بالفعل
            # البحث عن الكلمة غير الممزة بشرط أن لا تكون محاطة بعلامات التمييز
            pattern = r'(?<!\*)({}+)(?!\*)'.format(re.escape(word))
            formatted_text = re.sub(pattern, r'*\1*', formatted_text)
        
        # إضافة رموز للمعلومات التي لم يتم إضافة رموز لها
        contact_patterns = [
            (r'(?<!📞)(\s|^)(تليفون|هاتف|موبايل)(\s*[:]\s*)(\d+)', r'\1📞 *\2*\3\4'),
            (r'(?<!📱)(\s|^)(واتساب|واتس اب|واتس)(\s*[:]\s*)(\d+)', r'\1📱 *\2*\3\4'),
            (r'(?<!✉️)(\s|^)(ايميل|إيميل|بريد الكتروني|بريد إلكتروني)(\s*[:]\s*)([^\s]+@[^\s]+)', r'\1✉️ *\2*\3\4'),
            (r'(?<!🌐)(\s|^)(موقعنا|موقع|الموقع الرسمي)(\s*[:]\s*)([^\s]+)', r'\1🌐 *\2*\3\4'),
            (r'(?<!📍)(\s|^)(العنوان|المقر|الفرع)(\s*[:]\s*)([^\n]+)', r'\1📍 *\2*\3\4')
        ]
        
        for pattern, replacement in contact_patterns:
            formatted_text = re.sub(pattern, replacement, formatted_text, flags=re.IGNORECASE)
        
        # إصلاح أي تمييز مكرر للكلمات
        formatted_text = re.sub(r'\*\*+', '*', formatted_text)
        
        # تنظيف النص من تكرار معلومات الاتصال
        if "للتواصل المباشر" in formatted_text and formatted_text.count("📞") > 2:
            # العثور على موقع آخر قسم "للتواصل المباشر"
            last_contact_section = formatted_text.rfind("للتواصل المباشر")
            if last_contact_section > 0:
                # البحث عن نهاية القسم (علامة فاصلة كبيرة)
                section_end = formatted_text.find("\n\n", last_contact_section)
                if section_end > 0:
                    # حذف القسم المكرر
                    formatted_text = formatted_text[:last_contact_section] + formatted_text[section_end:]
        
        return formatted_text

    def _add_relevant_links(self, text: str, user_message: str) -> str:
        """
        إضافة روابط مباشرة ذات صلة بسياق المحادثة
        
        :param text: النص الأصلي
        :param user_message: رسالة المستخدم
        :return: النص مع إضافة الروابط
        """
        # تحديد الكلمات المفتاحية في رسالة المستخدم
        message_lower = user_message.lower()
        
        # روابط للتوظيف
        job_keywords = ["وظيفة", "شغل", "عمل", "تسجيل", "توظيف", "سيرة ذاتية", "تقديم"]
        
        # روابط للاستثمار
        investor_keywords = ["استثمار", "شراكة", "مشروع", "فرصة", "عائد", "دراسة جدوى"]
        
        # روابط للعمال والموارد البشرية
        worker_keywords = ["عمال", "موظفين", "توفير", "تشغيل", "عمالة", "فنيين"]
        
        # فحص نوع الروابط التي يجب إضافتها
        links_to_add = []
        
        if any(keyword in message_lower for keyword in job_keywords):
            links_to_add.append({
                "title": "رابط التسجيل للوظائف",
                "url": "https://omalmisrservices.com/en/jobs",
                "description": "سجل الآن مباشرة للتقدم للوظائف المتاحة"
            })
        
        if any(keyword in message_lower for keyword in investor_keywords):
            links_to_add.append({
                "title": "خدمات المستثمرين",
                "url": "https://omalmisrservices.com/en/companies",
                "description": "تعرف على الفرص الاستثمارية وخدمات الشركات"
            })
        
        if any(keyword in message_lower for keyword in worker_keywords):
            links_to_add.append({
                "title": "توفير العمالة",
                "url": "https://omalmisrservices.com/en/workers",
                "description": "ابحث عن العمالة المدربة لمشروعك"
            })
        
        # إضافة الروابط إذا كانت مناسبة وإذا لم تكن موجودة بالفعل
        if links_to_add and "روابط سريعة" not in text:
            text += "\n\n• *روابط سريعة قد تهمك*:\n"
            for link in links_to_add:
                text += f"🔗 [{link['title']}]({link['url']}) - {link['description']}\n"
        
        # إضافة معلومات التواصل إذا لم تكن موجودة
        if "📞" not in text and "✉️" not in text:
            contact_info = "\n\n• *للتواصل المباشر*:\n"
            contact_info += "📞 تليفون/واتساب: 01100901200\n"
            contact_info += "✉️ بريد إلكتروني: info@omalmisr.com\n"
            contact_info += "🌐 الموقع الرسمي: [www.omalmisr.com](https://www.omalmisr.com)\n"
            text += contact_info
        
        return text
        
    def _format_response(self, answer: str, user_message: str = "", user_id: str = "") -> str:
        """
        تنسيق الرد ليبدو أكثر شخصية وتفاعلية كموظف حقيقي
        
        :param answer: الرد الأساسي
        :param user_message: رسالة المستخدم
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المنسق
        """
        formatted_response = answer
        user_name = self._get_user_name(user_id)
        
        # تحقق مما إذا كان النص يبدأ بالترحيب أو فيه ترحيب متكرر
        greeting_phrases = ["أهلاً", "مرحباً", "السلام عليكم", "يا هلا", "تفضل"]
        has_greeting = any(phrase in formatted_response[:50] for phrase in greeting_phrases)
        
        # إضافة تعبير ترحيبي فقط إذا لم يكن هناك ترحيب بالفعل
        if not has_greeting and random.random() < 0.3:  # 30% فرصة لإضافة تعبير ترحيبي
            greeting = self._get_random_expression("greetings")
            if greeting:
                formatted_response = f"{greeting}\n\n{formatted_response}"
        
        # إضافة اسم المستخدم فقط مرة واحدة وفي بداية الرسالة إذا كان متاحًا
        if user_name and user_name not in formatted_response[:100]:
            # إذا كانت الرسالة لا تبدأ بتعبير ترحيبي، أضف ترحيبًا بسيطًا
            if not has_greeting:
                greetings = [
                    f"أهلاً {user_name}،\n\n",
                    f"مرحبًا {user_name}،\n\n",
                    f"مساء الخير {user_name}،\n\n",
                    f"صباح الخير {user_name}،\n\n"
                ]
                formatted_response = random.choice(greetings) + formatted_response
            # إذا كانت الرسالة تبدأ بتعبير ترحيبي، أضف الاسم بعده
            else:
                for phrase in greeting_phrases:
                    if phrase in formatted_response[:50]:
                        formatted_position = formatted_response.find(phrase) + len(phrase)
                        formatted_response = formatted_response[:formatted_position] + f" {user_name}،" + formatted_response[formatted_position:]
                        break
        
        # تحسين التنسيق بإضافة الرموز والأنماط
        formatted_response = self._enhance_formatting(formatted_response)
        
        # إضافة روابط التسجيل المناسبة حسب سياق المحادثة
        formatted_response = self._add_relevant_links(formatted_response, user_message)
        
        # إضافة تأكيد في النهاية أحياناً بشكل طبيعي
        if random.random() < 0.3 and "أستطيع مساعدتك" not in formatted_response:  # 30% فرصة لإضافة تأكيد
            assurances = [
                "أنا هنا لمساعدتك في أي استفسار آخر.",
                "أتمنى أن أكون قد أجبت على استفسارك بشكل واضح.",
                "سعيد بمساعدتك دائماً!",
                "أتطلع لمساعدتك في أي استفسارات أخرى."
            ]
            formatted_response = f"{formatted_response}\n\n{random.choice(assurances)}"
        
        # إضافة سؤال محدد في النهاية بدلاً من الأسئلة العامة
        conclusion = self._generate_contextual_question(user_message, self._detect_user_category(user_message))
        
        # تجنب وضع السؤال إذا كان هناك سؤال بالفعل في نهاية الرسالة
        if not any(formatted_response.strip().endswith(q) for q in ["؟", "?"]) and "؟" not in formatted_response[-50:]:
            formatted_response = f"{formatted_response}\n\n{conclusion}"
        
        # إزالة توقيع الشات بوت لجعله يبدو كموظف حقيقي
        # تم حذف التوقيع للتركيز على دور الموظف الحقيقي
        
        # إزالة أي تكرار في الرد النهائي
        formatted_response = self._remove_redundancies(formatted_response)
        
        return formatted_response
    
    def _remove_redundancies(self, text: str) -> str:
        """
        إزالة التكرارات في النص لجعله أكثر طبيعية
        
        :param text: النص المراد تنظيفه
        :return: النص بعد إزالة التكرارات
        """
        # تحديد التكرارات الشائعة للأسماء
        name_patterns = []
        for user_id, data in self.conversation_history.items():
            if "user_name" in data:
                user_name = data["user_name"]
                if len(user_name) > 2:  # تجنب الأسماء القصيرة جدًا
                    name_patterns.append(user_name)
        
        # إزالة تكرار الأسماء المتتالية
        for name in name_patterns:
            # تحديد نمط الاسم المتكرر مثل "يا محمد! يا محمد!" أو "محمد، محمد"
            text = re.sub(fr'(يا\s*{re.escape(name)}[!,،]*\s*){{2,}}', r'\1', text)
            text = re.sub(fr'({re.escape(name)}[!,،]*\s*){{2,}}', r'\1', text)
        
        # إزالة معلومات الاتصال المكررة
        contact_sections = ["للتواصل المباشر", "للاتصال", "معلومات الاتصال", "للتواصل معنا", "للاستفسارات المباشرة"]
        
        # عد معلومات الاتصال
        contact_count = sum(text.count(section) for section in contact_sections)
        
        # إذا كان هناك أكثر من قسم اتصال، احتفظ فقط بالأخير
        if contact_count > 1:
            # تحديد موقع آخر قسم اتصال
            last_section_pos = -1
            last_section_name = ""
            
            for section in contact_sections:
                pos = text.rfind(section)
                if pos > last_section_pos:
                    last_section_pos = pos
                    last_section_name = section
            
            # إزالة جميع أقسام الاتصال السابقة
            if last_section_pos > 0:
                for section in contact_sections:
                    if section != last_section_name:
                        # العثور على جميع مرات ظهور هذا القسم
                        section_pos = text.find(section)
                        while section_pos >= 0 and section_pos < last_section_pos:
                            # تحديد نهاية القسم
                            section_end = text.find("\n\n", section_pos)
                            if section_end < 0:
                                section_end = text.find("\n", section_pos)
                            
                            if section_end > 0:
                                # حذف القسم
                                text = text[:section_pos] + text[section_end:]
                            else:
                                break
                            
                            # البحث عن القسم التالي
                            section_pos = text.find(section, section_pos)
        
        # إزالة تكرار الروابط
        links_section_pos = text.find("روابط سريعة")
        if links_section_pos >= 0 and text.count("https://") > 3:
            # عدد مرات تكرار الروابط
            link_count = text.count("https://")
            
            # الاحتفاظ فقط بقسم الروابط السريعة إذا كان هناك تكرار
            text_before = text[:links_section_pos]
            text_after = text[links_section_pos:]
            
            # إزالة روابط من النص قبل قسم الروابط السريعة
            text_before = re.sub(r'https://[^\s\n]+', '', text_before)
            
            # إعادة بناء النص
            text = text_before + text_after
        
        # تنظيف أي أسطر فارغة متكررة
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
        
    def _generate_contextual_question(self, user_message: str, user_category: str = "") -> str:
        """
        توليد سؤال سياقي مناسب للمحادثة بأسلوب موظف حقيقي
        
        :param user_message: رسالة المستخدم
        :param user_category: فئة المستخدم
        :return: سؤال مخصص
        """
        message_lower = user_message.lower()
        
        # أسئلة للباحثين عن وظائف بصيغة موظف حقيقي
        job_questions = [
            "هل تبحث عن وظيفة في تخصص معين؟ أستطيع مساعدتك.",
            "هل تحتاج مساعدة في تجهيز السيرة الذاتية للتقديم؟",
            "هل ترغب في معرفة المزيد عن متطلبات الوظائف المتاحة حالياً؟",
            "ما هي خبراتك السابقة؟ سأحاول إيجاد الوظيفة المناسبة لك.",
            "هل تفضل العمل في أي من فروعنا المحددة؟"
        ]
        
        # أسئلة للمستثمرين
        investor_questions = [
            "هل لديك اهتمام باستثمار محدد؟ يمكنني تقديم تفاصيل أكثر.",
            "هل ترغب في ترتيب اجتماع مع فريق الاستثمار لدينا؟",
            "ما هو حجم الاستثمار الذي تفكر فيه؟ سأساعدك بتحديد الفرص المناسبة.",
            "هل أنت مهتم بالحصول على دراسة جدوى لأحد مشاريعنا الاستثمارية؟",
            "ما هي قطاعات الاستثمار التي تهمك تحديداً؟"
        ]
        
        # أسئلة للشركات
        company_questions = [
            "هل تبحث عن كفاءات في تخصص معين؟ لدينا قاعدة بيانات كبيرة من المتقدمين المؤهلين.",
            "ما هي احتياجات شركتك من العمالة؟ يسعدني مساعدتك.",
            "هل ترغب بمعرفة خدمات الدعم الفني والاستشاري التي نقدمها للشركات؟",
            "هل تحتاج إلى عمالة بشكل عاجل؟ يمكننا توفير موظفين مؤهلين خلال فترة قصيرة.",
            "هل تريد التعرف على عروضنا الخاصة للشركات؟"
        ]
        
        # أسئلة عامة بصيغة موظف وليس بوت
        general_questions = [
            "هل لديك أي استفسار آخر؟ أنا هنا للمساعدة.",
            "هل تحتاج لمزيد من المعلومات؟ سأكون سعيداً بتوضيح أي نقطة.",
            "هل أستطيع مساعدتك في شيء آخر اليوم؟",
            "هل لديك سؤال آخر عن خدماتنا؟",
            "هل يمكنني تقديم أي مساعدة إضافية؟"
        ]
        
        # اختيار السؤال المناسب
        if user_category == "باحث عن عمل" or any(keyword in message_lower for keyword in ["وظيفة", "شغل", "عمل", "توظيف"]):
            return random.choice(job_questions)
        elif user_category == "مستثمر" or any(keyword in message_lower for keyword in ["استثمار", "مشروع", "فرصة"]):
            return random.choice(investor_questions)
        elif user_category == "شركة" or any(keyword in message_lower for keyword in ["شركة", "مصنع", "عمال"]):
            return random.choice(company_questions)
        else:
            return random.choice(general_questions)
    
    def generate_response(self, user_message: str, user_id: str = "") -> str:
        """
        توليد رد على رسالة المستخدم
        
        :param user_message: رسالة المستخدم
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المولد
        """
        logger.info(f"معالجة رسالة من المستخدم {user_id}: {user_message[:30]}...")
        
        # تأكد من وجود سجل للمستخدم
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {"messages": []}
            
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {"awaiting_name": True}
        
        # التحقق مما إذا كنا نسأل المستخدم عن اسمه لأول مرة
        if self.conversation_state[user_id].get("awaiting_name", True):
            # إذا كانت الرسالة الأولى ولم نسأل عن الاسم بعد
            if not self.conversation_state[user_id].get("name_asked", False):
                logger.info(f"طلب اسم المستخدم {user_id} لأول مرة")
                self.conversation_state[user_id]["name_asked"] = True
                
                # حفظ الرسالة في تاريخ المحادثة
                current_time = datetime.datetime.now().isoformat()
                name_question = random.choice(self.name_questions)
                
                if "messages" not in self.conversation_history[user_id]:
                    self.conversation_history[user_id]["messages"] = []
                    
                self.conversation_history[user_id]["messages"].append({
                    "timestamp": current_time,
                    "message": user_message,
                    "response": name_question
                })
                
                return name_question
            else:
                # إذا سألنا عن الاسم وهذه إجابة المستخدم
                welcome_response = self._save_user_name(user_id, user_message)
                logger.info(f"تم تخزين اسم المستخدم {user_id} والترحيب به")
                self.conversation_state[user_id]["awaiting_name"] = False
                
                # حفظ الرسالة في تاريخ المحادثة
                current_time = datetime.datetime.now().isoformat()
                if "messages" not in self.conversation_history[user_id]:
                    self.conversation_history[user_id]["messages"] = []
                    
                self.conversation_history[user_id]["messages"].append({
                    "timestamp": current_time,
                    "message": user_message,
                    "response": welcome_response
                })
                
                return welcome_response
        
        # التحقق مما إذا كان هذا سؤالًا جديدًا أو استمرارًا للمحادثة
        if "awaiting_continuation" in self.conversation_state.get(user_id, {}):
            previous_state = self.conversation_state[user_id]
            
            # إذا كانت المحادثة السابقة في انتظار استجابة الاستمرار
            if previous_state.get("awaiting_continuation", False):
                # تحديد ما إذا كان المستخدم يريد الاستمرار أم لا
                if self._is_continuation_message(user_message):
                    # إعادة تعيين حالة الانتظار
                    self.conversation_state[user_id]["awaiting_continuation"] = False
                    # معالجة الرسالة كسؤال جديد
                    logger.info(f"المستخدم {user_id} اختار الاستمرار في المحادثة")
                else:
                    # إنهاء المحادثة
                    logger.info(f"المستخدم {user_id} اختار إنهاء المحادثة")
                    user_name = self._get_user_name(user_id)
                    farewell = f"شكراً لتواصلك معنا{'  يا ' + user_name if user_name else ''}! نتطلع إلى خدمتك مرة أخرى."
                    
                    # حفظ الرسالة في تاريخ المحادثة
                    current_time = datetime.datetime.now().isoformat()
                    if "messages" not in self.conversation_history[user_id]:
                        self.conversation_history[user_id]["messages"] = []
                        
                    self.conversation_history[user_id]["messages"].append({
                        "timestamp": current_time,
                        "message": user_message,
                        "response": farewell
                    })
                    
                    return farewell
        
        # التحقق مما إذا كانت الرسالة تطلب رابطاً لخدمة معينة
        service_info = self._detect_service_request(user_message)
        if service_info and "link" in service_info:
            logger.info(f"تم إعادة توجيه المستخدم {user_id} إلى خدمة: {service_info.get('title', 'غير محدد')}")
            user_name = self._get_user_name(user_id)
            name_prefix = f" يا {user_name}" if user_name else ""
            response = f"{self._get_random_expression('positive_responses')}{name_prefix}! {service_info.get('description', '')}\n\n{service_info.get('link', '')}"
            
            # حفظ حالة المحادثة
            if self.continue_conversation:
                self.conversation_state[user_id]["awaiting_continuation"] = True
            
            formatted_response = self._format_response(response, user_message, user_id)
            
            # حفظ الرسالة في تاريخ المحادثة
            current_time = datetime.datetime.now().isoformat()
            if "messages" not in self.conversation_history[user_id]:
                self.conversation_history[user_id]["messages"] = []
                
            self.conversation_history[user_id]["messages"].append({
                "timestamp": current_time,
                "message": user_message,
                "response": formatted_response
            })
            
            return formatted_response
        
        # البحث في قاعدة المعرفة
        best_match, confidence = self.search_knowledge_base(user_message)
        
        if best_match and confidence >= self.similarity_threshold:
            # إذا وجد تطابق جيد، عد الجواب المطابق
            logger.info(f"تم العثور على إجابة للمستخدم {user_id} بثقة {confidence:.2f}")
            
            # حفظ حالة المحادثة
            if self.continue_conversation:
                self.conversation_state[user_id]["awaiting_continuation"] = True
                self.conversation_state[user_id]["last_question_id"] = best_match["id"]
            
            formatted_response = self._format_response(best_match["answer"], user_message, user_id)
            
            # حفظ الرسالة في تاريخ المحادثة
            current_time = datetime.datetime.now().isoformat()
            if "messages" not in self.conversation_history[user_id]:
                self.conversation_history[user_id]["messages"] = []
                
            self.conversation_history[user_id]["messages"].append({
                "timestamp": current_time,
                "message": user_message,
                "response": formatted_response
            })
            
            return formatted_response
        else:
            # إذا لم يجد تطابقاً جيداً، استخدم API لتوليد إجابة إبداعية
            try:
                logger.info(f"استخدام API لتوليد إجابة للمستخدم {user_id}")
                
                # تخصيص الاستعلام ليتضمن اسم المستخدم إذا كان متوفرًا
                user_name = self._get_user_name(user_id)
                context = f"المستخدم اسمه: {user_name}. " if user_name else ""
                context += f"الرسالة: {user_message}"
                
                # محاولة استخدام API للحصول على إجابة
                response_text = ""
                try:
                    api_response = self.api.generate_response(
                        user_message, 
                        user_category=self._detect_user_category(user_message),
                        context=context,
                        human_expressions=self.human_expressions,
                        contact_info=self.contact_info
                    )
                    
                    # استخراج نص الرد من استجابة API
                    response_text = self.api.extract_response_text(api_response)
                    
                    # التحقق من وجود رسالة خطأ في الاستجابة
                    if "error" in api_response or ("عذراً" in response_text and "مشكلة في الاتصال" in response_text):
                        # استخدام آلية الاحتياط إذا فشل الاتصال بـ API
                        logger.warning("فشل اتصال API - استخدام آلية احتياطية")
                        raise Exception("فشل في الاتصال بـ API")
                        
                except Exception as api_error:
                    logger.warning(f"فشل استدعاء API: {api_error} - استخدام قاعدة المعرفة المحلية")
                    # البحث عن إجابة مناسبة في قاعدة البيانات المحلية بمعيار أقل صرامة
                    fallback_match, _ = self.search_knowledge_base(user_message)
                    
                    if fallback_match:
                        response_text = fallback_match["answer"]
                        logger.info("تم استخدام إجابة من قاعدة المعرفة المحلية كآلية احتياطية")
                    else:
                        # استخدام إجابة من قائمة الردود الافتراضية في حالة فشل كل شيء
                        default_responses = [
                            f"مرحباً{' ' + user_name if user_name else ''}!\n\nنحن سعداء بالتواصل معك في مجمع عمال مصر. نوفر فرص عمل متنوعة في قطاعات مختلفة، وخدمات للمستثمرين والشركات.\n\nيمكنك الاطلاع على الخدمات المتاحة عبر موقعنا الرسمي: https://www.omalmisr.com/\n\n• *للتواصل المباشر*:\n📞 تليفون/واتساب: 01100901200\n✉️ بريد إلكتروني: info@omalmisr.com",
                            f"أهلاً بك{' ' + user_name if user_name else ''}!\n\nيسعدنا استفسارك عن مجمع عمال مصر. نوفر خدمات متكاملة في مجالات التوظيف والاستثمار الصناعي والزراعي.\n\nيمكنك التقديم للوظائف من خلال: https://omalmisrservices.com/en/jobs\n\n• *للتواصل المباشر*:\n📞 تليفون/واتساب: 01100901200\n✉️ بريد إلكتروني: info@omalmisr.com",
                            f"شكراً لتواصلك معنا{' يا ' + user_name if user_name else ''}!\n\nنعتذر عن التأخير في الرد. يمكنك الاطلاع على خدماتنا عبر موقعنا الرسمي أو التواصل المباشر معنا.\n\n• *للتواصل المباشر*:\n📞 تليفون/واتساب: 01100901200\n✉️ بريد إلكتروني: info@omalmisr.com\n🌐 الموقع الرسمي: https://www.omalmisr.com/"
                        ]
                        response_text = random.choice(default_responses)
                        logger.info("تم استخدام رد افتراضي من القائمة المحددة مسبقاً")
                
                # حفظ حالة المحادثة
                if self.continue_conversation:
                    self.conversation_state[user_id]["awaiting_continuation"] = True
                
                formatted_response = self._format_response(response_text, user_message, user_id)
                
                # حفظ الرسالة في تاريخ المحادثة
                current_time = datetime.datetime.now().isoformat()
                if "messages" not in self.conversation_history[user_id]:
                    self.conversation_history[user_id]["messages"] = []
                    
                self.conversation_history[user_id]["messages"].append({
                    "timestamp": current_time,
                    "message": user_message,
                    "response": formatted_response
                })
                
                return formatted_response
                
            except Exception as e:
                logger.error(f"خطأ في توليد الإجابة: {e}")
                
                # إذا فشل كل شيء، استخدم رد افتراضي بسيط
                user_name = self._get_user_name(user_id)
                name_prefix = f" يا {user_name}" if user_name else ""
                default_response = f"أهلاً{name_prefix}!\n\nيسعدنا تواصلك مع مجمع عمال مصر. يمكنك زيارة موقعنا الرسمي للاطلاع على خدماتنا المتنوعة في مجالات التوظيف والاستثمار.\n\n• *للتواصل المباشر*:\n📞 تليفون/واتساب: 01100901200\n✉️ بريد إلكتروني: info@omalmisr.com\n🌐 الموقع الرسمي: https://www.omalmisr.com/\n\nهل يمكنني مساعدتك في شيء محدد؟"
                
                formatted_response = self._format_response(default_response, user_message, user_id)
                
                # حفظ الرسالة في تاريخ المحادثة
                current_time = datetime.datetime.now().isoformat()
                if "messages" not in self.conversation_history[user_id]:
                    self.conversation_history[user_id]["messages"] = []
                    
                self.conversation_history[user_id]["messages"].append({
                    "timestamp": current_time,
                    "message": user_message,
                    "response": formatted_response
                })
                
                return formatted_response
    
    def generate_messenger_response(self, user_message: str, user_id: str = "") -> str:
        """
        توليد رد على رسالة المستخدم في ماسنجر
        
        :param user_message: رسالة المستخدم
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المولد
        """
        logger.info(f"توليد رد لماسنجر للمستخدم: {user_id}")
        self.set_conversation_source("messenger")
        
        # استدعاء الدالة الرئيسية لتوليد الرد
        return self.generate_response(user_message, user_id)
    
    def generate_comment_response(self, user_message: str, user_id: str = "") -> str:
        """
        توليد رد على تعليق فيسبوك
        
        :param user_message: نص التعليق
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المولد
        """
        logger.info(f"توليد رد لتعليق فيسبوك للمستخدم: {user_id}")
        self.set_conversation_source("facebook_comment")
        
        # استدعاء الدالة الرئيسية لتوليد الرد، لكن بدون سؤال الاسم في التعليقات العامة
        # نحدد أولاً ما إذا كنا سنتخطى مرحلة سؤال الاسم
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {"awaiting_name": False}
        
        return self.generate_response(user_message, user_id)
    
    def save_conversation_history(self, filename: str) -> bool:
        """
        حفظ تاريخ المحادثة في ملف
        
        :param filename: مسار الملف لحفظ المحادثة فيه
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