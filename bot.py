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
        self.conversation_history = {}
        
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
    
    def _format_response(self, answer: str, user_message: str = "", user_id: str = "") -> str:
        """
        تنسيق الرد ليبدو أكثر شخصية وتفاعلية
        
        :param answer: الرد الأساسي
        :param user_message: رسالة المستخدم
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المنسق
        """
        formatted_response = answer
        
        # إضافة تعبير ترحيبي أحياناً
        if random.random() < 0.3:  # 30% فرصة لإضافة تعبير ترحيبي
            greeting = self._get_random_expression("greetings")
            if greeting:
                formatted_response = f"{greeting}\n\n{formatted_response}"
        
        # إضافة تعبير إيجابي أحياناً
        if random.random() < 0.3:  # 30% فرصة لإضافة تعبير إيجابي
            positive = self._get_random_expression("positive_responses")
            if positive:
                formatted_response = f"{positive} {formatted_response}"
        
        # محاولة تحديد فئة المستخدم وتخصيص الرد
        if user_message:
            user_category = self._detect_user_category(user_message)
            
            if user_category == "باحث عن عمل" and random.random() < 0.5:
                job_response = self._get_random_expression("job_seekers_response")
                if job_response:
                    formatted_response = f"{job_response}\n\n{formatted_response}"
            
            if user_category == "مستثمر" and random.random() < 0.5:
                investor_response = self._get_random_expression("investors_response")
                if investor_response:
                    formatted_response = f"{investor_response}\n\n{formatted_response}"
        
        # إضافة تأكيد في النهاية أحياناً
        if random.random() < 0.3:  # 30% فرصة لإضافة تأكيد
            assurance = self._get_random_expression("assurances")
            if assurance:
                formatted_response = f"{formatted_response}\n\n{assurance}"
        
        # إضافة خاتمة أحياناً
        if not self.continue_conversation and random.random() < 0.5:  # 50% فرصة لإضافة خاتمة إذا لم يكن هناك سؤال للاستمرار
            conclusion = self._get_random_expression("conclusions")
            if conclusion:
                formatted_response = f"{formatted_response}\n\n{conclusion}"
        
        # إضافة سؤال الاستمرار إذا كانت الميزة مفعلة
        if self.continue_conversation:
            continue_phrase = random.choice(self.continue_phrases)
            formatted_response = f"{formatted_response}\n\n{continue_phrase}"
        
        return formatted_response
    
    def generate_response(self, user_message: str, user_id: str = "") -> str:
        """
        توليد رد على رسالة المستخدم
        
        :param user_message: رسالة المستخدم
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المولد
        """
        # التحقق مما إذا كان هذا سؤالًا جديدًا أو استمرارًا للمحادثة
        if user_id in self.conversation_history:
            previous_state = self.conversation_history[user_id]
            
            # إذا كانت المحادثة السابقة في انتظار استجابة الاستمرار
            if previous_state.get("awaiting_continuation", False):
                # تحديد ما إذا كان المستخدم يريد الاستمرار أم لا
                if self._is_continuation_message(user_message):
                    # إعادة تعيين حالة الانتظار
                    self.conversation_history[user_id]["awaiting_continuation"] = False
                    # معالجة الرسالة كسؤال جديد
                    logger.info(f"المستخدم {user_id} اختار الاستمرار في المحادثة")
                else:
                    # إنهاء المحادثة
                    logger.info(f"المستخدم {user_id} اختار إنهاء المحادثة")
                    self.conversation_history.pop(user_id, None)
                    return "شكراً لتواصلك معنا! نتطلع إلى خدمتك مرة أخرى."
        
        # التحقق مما إذا كانت الرسالة تطلب رابطاً لخدمة معينة
        service_info = self._detect_service_request(user_message)
        if service_info and "link" in service_info:
            logger.info(f"تم إعادة توجيه المستخدم {user_id} إلى خدمة: {service_info.get('title', 'غير محدد')}")
            response = f"{self._get_random_expression('positive_responses')} {service_info.get('description', '')}\n\n{service_info.get('link', '')}"
            
            # حفظ حالة المحادثة
            if self.continue_conversation:
                if user_id not in self.conversation_history:
                    self.conversation_history[user_id] = {}
                self.conversation_history[user_id]["awaiting_continuation"] = True
            
            return self._format_response(response, user_message, user_id)
        
        # البحث في قاعدة المعرفة
        best_match, confidence = self.search_knowledge_base(user_message)
        
        if best_match and confidence >= self.similarity_threshold:
            # إذا وجد تطابق جيد، عد الجواب المطابق
            logger.info(f"تم العثور على إجابة للمستخدم {user_id} بثقة {confidence:.2f}")
            
            # حفظ حالة المحادثة
            if self.continue_conversation:
                if user_id not in self.conversation_history:
                    self.conversation_history[user_id] = {}
                self.conversation_history[user_id]["awaiting_continuation"] = True
                self.conversation_history[user_id]["last_question_id"] = best_match["id"]
            
            return self._format_response(best_match["answer"], user_message, user_id)
        else:
            # إذا لم يجد تطابقاً جيداً، استخدم API لتوليد إجابة إبداعية
            try:
                logger.info(f"استخدام API لتوليد إجابة للمستخدم {user_id}")
                api_response = self.api.generate_response(user_message)
                
                # استخراج نص الرد من استجابة API
                response_text = self.api.extract_response_text(api_response)
                
                # حفظ حالة المحادثة
                if self.continue_conversation:
                    if user_id not in self.conversation_history:
                        self.conversation_history[user_id] = {}
                    self.conversation_history[user_id]["awaiting_continuation"] = True
                
                return self._format_response(response_text, user_message, user_id)
            except Exception as e:
                logger.error(f"خطأ في توليد الإجابة باستخدام API: {e}")
                
                # إذا فشل استخدام API، استخدم رد افتراضي
                default_response = "عذراً، لم أتمكن من فهم سؤالك بشكل كامل. هل يمكنك إعادة صياغته أو توضيح ما تبحث عنه بالتحديد؟ أو يمكنك التواصل مباشرة معنا عبر معلومات الاتصال الموجودة في صفحتنا الرسمية."
                
                return self._format_response(default_response, user_message, user_id)
    
    def get_related_questions(self, question_id: int, count: int = 3) -> List[Dict]:
        """
        الحصول على أسئلة مشابهة اعتماداً على رقم السؤال
        
        :param question_id: رقم السؤال
        :param count: عدد الأسئلة المراد الحصول عليها
        :return: قائمة بالأسئلة المشابهة
        """
        # البحث عن السؤال الأصلي
        original_question = None
        for prompt in self.prompts:
            if prompt["id"] == question_id:
                original_question = prompt
                break
        
        if not original_question:
            logger.warning(f"لم يتم العثور على سؤال برقم {question_id}")
            return []
        
        # قائمة لتخزين الأسئلة المشابهة مع درجة التشابه
        related_with_score = []
        
        # البحث عن أسئلة مشابهة
        for prompt in self.prompts:
            if prompt["id"] != question_id:  # تخطي السؤال نفسه
                score = self._calculate_similarity(original_question["question"], prompt["question"])
                related_with_score.append((prompt, score))
        
        # ترتيب الأسئلة حسب درجة التشابه (تنازلياً)
        related_with_score.sort(key=lambda x: x[1], reverse=True)
        
        # إعادة الأسئلة الأكثر تشابهاً
        return [question for question, _ in related_with_score[:count]]
    
    def clear_conversation_history(self, user_id: str = None) -> None:
        """
        مسح تاريخ المحادثات لمستخدم معين أو لجميع المستخدمين
        
        :param user_id: معرف المستخدم (اختياري)
        """
        if user_id:
            if user_id in self.conversation_history:
                self.conversation_history.pop(user_id)
                logger.info(f"تم مسح تاريخ المحادثة للمستخدم {user_id}")
        else:
            self.conversation_history.clear()
            logger.info("تم مسح تاريخ المحادثة لجميع المستخدمين")
    
    def generate_messenger_response(self, user_message: str, user_id: str = "") -> str:
        """
        توليد رد على رسالة المستخدم في ماسنجر
        
        :param user_message: رسالة المستخدم
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المولد
        """
        logger.info(f"توليد رد لماسنجر للمستخدم: {user_id}")
        self.set_conversation_source("messenger")
        
        # البحث في قاعدة المعرفة
        best_match, confidence = self.search_knowledge_base(user_message)
        
        if best_match and confidence >= self.similarity_threshold:
            # إذا وجد تطابق جيد، عد الجواب المطابق
            logger.info(f"تم العثور على إجابة للمستخدم {user_id} بثقة {confidence:.2f}")
            return self._format_response(best_match["answer"], user_message, user_id)
        else:
            # استخدام API لتوليد إجابة إبداعية
            try:
                # استدعاء API مباشرة هنا للتأكد من أن الاختبارات تكتشف ذلك
                api_response = self.api.generate_response(user_message)
                response_text = self.api.extract_response_text(api_response)
                return self._format_response(response_text, user_message, user_id)
            except Exception as e:
                logger.error(f"خطأ في توليد الإجابة باستخدام API: {e}")
                default_response = "عذراً، لم أتمكن من فهم سؤالك بشكل كامل. هل يمكنك إعادة صياغته؟"
                return self._format_response(default_response, user_message, user_id)
    
    def generate_comment_response(self, user_message: str, user_id: str = "") -> str:
        """
        توليد رد على تعليق فيسبوك
        
        :param user_message: نص التعليق
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المولد
        """
        logger.info(f"توليد رد لتعليق فيسبوك للمستخدم: {user_id}")
        self.set_conversation_source("facebook_comment")
        
        # البحث في قاعدة المعرفة
        best_match, confidence = self.search_knowledge_base(user_message)
        
        if best_match and confidence >= self.similarity_threshold:
            # إذا وجد تطابق جيد، عد الجواب المطابق
            logger.info(f"تم العثور على إجابة للمستخدم {user_id} بثقة {confidence:.2f}")
            return self._format_response(best_match["answer"], user_message, user_id)
        else:
            # استخدام API لتوليد إجابة إبداعية
            try:
                # استدعاء API مباشرة هنا للتأكد من أن الاختبارات تكتشف ذلك
                api_response = self.api.generate_response(user_message)
                response_text = self.api.extract_response_text(api_response)
                return self._format_response(response_text, user_message, user_id)
            except Exception as e:
                logger.error(f"خطأ في توليد الإجابة باستخدام API: {e}")
                default_response = "عذراً، لم أتمكن من فهم استفسارك بشكل كامل. هل يمكنك توضيح ما تحتاجه بخصوص مجمع عمال مصر؟"
                return self._format_response(default_response, user_message, user_id)
    
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