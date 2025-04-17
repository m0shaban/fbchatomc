"""
وحدة شات بوت مجمع عمال مصر
تحتوي على الصنف الرئيسي للشات بوت وجميع الوظائف الخاصة به
"""

import os
import re
import json
import random
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from config import BOT_SETTINGS, API_SETTINGS, APP_SETTINGS, FACEBOOK_SETTINGS
import api
import api_alternatives
from api_alternatives import handle_local_response

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=BOT_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

class ChatBot:
    """
    فئة الشات بوت الرئيسية
    تتولى معالجة الرسائل وتوليد الردود
    """
    
    def __init__(self, data_file: str = None, api_client = None, use_local_responses: bool = True):
        """
        تهيئة الشات بوت
        
        :param data_file: مسار ملف البيانات (data.json)
        :param api_client: واجهة API (اختياري)
        :param use_local_responses: استخدام الردود المحلية بدون API عندما يكون ذلك ممكناً
        """
        # ملف البيانات
        self.data_file = data_file or BOT_SETTINGS.get("DATA_FILE", "data.json")
        
        # واجهة API
        if api_client is None:
            try:
                # إعداد واجهة API بشكل افتراضي
                self.api_client = api.DeepSeekAPI()
            except Exception as e:
                logger.warning(f"فشل في تهيئة DeepSeekAPI الأساسي: {e}")
                logger.warning("محاولة استخدام واجهة بديلة...")
                try:
                    # استخدام واجهة بديلة
                    self.api_client = api_alternatives.OpenAIClientAPI()
                except Exception as e2:
                    logger.error(f"فشل في تهيئة الواجهة البديلة: {e2}")
                    self.api_client = None
        else:
            self.api_client = api_client
        
        # إعدادات المحادثة
        self.similarity_threshold = float(BOT_SETTINGS.get("SIMILARITY_THRESHOLD", 0.4))
        self.personalize_response = BOT_SETTINGS.get("PERSONALIZE_RESPONSE", True)
        self.save_conversations = BOT_SETTINGS.get("SAVE_CONVERSATIONS", True)
        self.conversations_dir = BOT_SETTINGS.get("CONVERSATIONS_DIR", "conversations")
        self.use_local_responses = use_local_responses
        
        # إعدادات الردود
        self.max_response_length = 150  # الحد الأقصى لعدد الكلمات في الرد
        
        # حالة المحادثة لكل مستخدم
        self.conversation_state = {}
        
        # تحميل البيانات
        self.data = self._load_data()
        self.prompts = self.data.get("prompts", [])
        self.human_expressions = self.data.get("human_expressions", {})
        self.contact_info = self.data.get("contact_info", {})
        self.service_links = self.data.get("service_links", {})
        self.user_categories = self.data.get("user_categories", [])
        self.requires_human_contact = self.data.get("requires_human_contact", [])
        
        logger.info(f"تم تهيئة الشات بوت بنجاح. تم تحميل {len(self.prompts)} سؤال من ملف البيانات.")
    
    def _load_data(self) -> Dict:
        """
        تحميل البيانات من ملف البيانات (data.json)
        
        :return: البيانات المحملة
        :raises: Exception في حالة وجود خطأ
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"خطأ في تحميل ملف البيانات: {e}")
            raise Exception(f"فشل في تحميل ملف البيانات: {e}")

    def generate_response(self, user_message: str, user_id: str = "anonymous", user_name: str = None) -> str:
        """
        توليد رد على رسالة المستخدم
        
        :param user_message: رسالة المستخدم
        :param user_id: معرف المستخدم
        :param user_name: اسم المستخدم (اختياري)
        :return: رد الشات بوت
        """
        # تنظيف رسالة المستخدم
        user_message = user_message.strip()
        
        # تحديث حالة المحادثة
        self._update_conversation_state(user_id, user_message, user_name)
        
        # محاولة معالجة الرسالة محلياً (بدون API) إذا كان ذلك ممكناً
        if self.use_local_responses:
            local_response, is_local = handle_local_response(user_message, self.data_file)
            if is_local:
                logger.info(f"تم توليد رد محلي لـ {user_id} على: '{user_message[:50]}...'")
                return local_response
        
        # تحقق من الأسئلة الشائعة
        for prompt in self.prompts:
            similarity = self._calculate_similarity(user_message, prompt.get("question", ""))
            if similarity >= self.similarity_threshold:
                answer = prompt.get("answer", "")
                logger.info(f"تطابق وجد بنسبة {similarity:.2f} للسؤال: {prompt.get('question')}")
                
                # تنسيق الرد للمستخدم (إضافة تحية، تقصير، إلخ)
                formatted_answer = self._format_response_for_user(answer, user_id)
                
                return formatted_answer
        
        # تحقق مما إذا كان السؤال يتطلب تدخلًا بشريًا
        if self._requires_human_follow_up(user_message):
            logger.info(f"تحديد أن الرسالة تتطلب متابعة بشرية: '{user_message[:50]}...'")
            return (
                "شكراً لتواصلك مع مجمع عمال مصر. يبدو أن استفسارك يتطلب اهتماماً خاصاً من أحد ممثلي خدمة العملاء. "
                "يرجى التواصل معنا مباشرة عبر واتساب: 01100901200، أو زيارة موقعنا الرسمي: https://www.omalmisr.com"
            )
        
        # إذا لم يتم العثور على تطابق، استخدم API
        if self.api_client is None:
            logger.error("لا يمكن توليد رد عبر API: لم يتم تهيئة واجهة API")
            return (
                "عذراً، لا يمكن معالجة استفسارك حالياً نظراً لمشكلة فنية. "
                "يرجى التواصل معنا مباشرة عبر واتساب: 01100901200، أو زيارة موقعنا الرسمي: https://www.omalmisr.com"
            )
        
        try:
            # بناء سياق للنموذج
            context = self._build_model_context(user_id)
            
            # توليد رد باستخدام API
            logger.info(f"توليد رد عبر API لـ {user_id} على: '{user_message[:50]}...'")
            
            # البنية الجديدة لإضافة معلومات أكثر للسياق
            user_category = self._get_user_category(user_id)
            
            # إضافة سياق إضافي للنموذج
            full_context = context
            if user_category:
                full_context += f"\nفئة المستخدم: {user_category}"
            
            # إضافة قائمة الخدمات للسياق
            service_links_text = "روابط الخدمات المتاحة:\n"
            for name, link in self.service_links.items():
                service_links_text += f"- {name}: {link}\n"
            
            full_context += f"\n{service_links_text}"
            
            start_time = time.time()
            api_response = self.api_client.generate_response(
                user_message,
                system_message=full_context,
                user_category=user_category,
                context=full_context,
                human_expressions=self.human_expressions,
                contact_info=self.contact_info
            )
            response_time = time.time() - start_time
            
            # استخراج نص الرد
            if hasattr(self.api_client, "extract_response_text"):
                response_text = self.api_client.extract_response_text(api_response)
            elif isinstance(api_response, dict) and "choices" in api_response:
                response_text = api_response["choices"][0]["message"]["content"]
            else:
                response_text = str(api_response)
            
            logger.info(f"تم الحصول على رد عبر API في {response_time:.2f} ثانية")
            
            # تنسيق الرد للمستخدم (إضافة تحية، تقصير، إلخ)
            formatted_response = self._format_response_for_user(response_text, user_id)
            
            # حفظ المحادثة إذا كان التسجيل مفعلاً
            if self.save_conversations:
                self._save_conversation(user_id, user_message, formatted_response)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"خطأ في توليد رد عبر API: {e}")
            return (
                "عذراً، أواجه بعض المشكلات في معالجة استفسارك حالياً. "
                "يمكنك التواصل معنا مباشرة عبر واتساب: 01100901200، أو زيارة موقعنا الرسمي: https://www.omalmisr.com"
            )
    
    def _update_conversation_state(self, user_id: str, message: str, user_name: str = None) -> None:
        """
        تحديث حالة المحادثة للمستخدم
        
        :param user_id: معرف المستخدم
        :param message: رسالة المستخدم
        :param user_name: اسم المستخدم (اختياري)
        """
        # تحديث بيانات المستخدم
        if user_id not in self.conversation_state:
            # إنشاء سجل جديد للمستخدم
            self.conversation_state[user_id] = {
                "messages": [],
                "last_activity": datetime.now().isoformat(),
                "user_name": user_name if user_name else None,
                "user_category": None
            }
        
        # تحديث اسم المستخدم إذا تم توفيره
        if user_name and not self.conversation_state[user_id].get("user_name"):
            # تنظيف اسم المستخدم
            clean_name = self._clean_user_name(user_name)
            self.conversation_state[user_id]["user_name"] = clean_name
        
        # إضافة رسالة جديدة
        self.conversation_state[user_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # تحديث وقت النشاط
        self.conversation_state[user_id]["last_activity"] = datetime.now().isoformat()
        
        # محاولة تحديد فئة المستخدم من الرسالة
        self._update_user_category(user_id, message)
    
    def _update_user_category(self, user_id: str, message: str) -> None:
        """
        تحديث فئة المستخدم بناءً على محتوى الرسالة
        
        :param user_id: معرف المستخدم
        :param message: رسالة المستخدم
        """
        # فئة المستخدم الحالية
        current_category = self.conversation_state[user_id].get("user_category")
        
        # إذا كانت الفئة محددة بالفعل، لا حاجة للتحديث
        if current_category:
            return
            
        # تحديد فئة المستخدم
        message_lower = message.lower()
        
        job_keywords = ["وظيفة", "عمل", "توظيف", "وظائف", "وظيفه", "فرصه", "فرصة"]
        if any(keyword in message_lower for keyword in job_keywords):
            self.conversation_state[user_id]["user_category"] = "باحث عن عمل"
            return
            
        investor_keywords = ["استثمار", "مشروع", "مستثمر", "استثمر", "تمويل", "شراكة"]
        if any(keyword in message_lower for keyword in investor_keywords):
            self.conversation_state[user_id]["user_category"] = "مستثمر"
            return
            
        # يمكن إضافة المزيد من الفئات هنا
    
    def _get_user_category(self, user_id: str) -> str:
        """
        الحصول على فئة المستخدم
        
        :param user_id: معرف المستخدم
        :return: فئة المستخدم أو فارغة إذا لم تكن محددة
        """
        if user_id in self.conversation_state:
            return self.conversation_state[user_id].get("user_category", "")
        return ""
    
    def _build_model_context(self, user_id: str) -> str:
        """
        بناء سياق للنموذج اللغوي
        
        :param user_id: معرف المستخدم
        :return: السياق المبني
        """
        context = (
            "أنت المساعد الآلي الرسمي لمجمع عمال مصر، شركة مساهمة مصرية رائدة في مجال الخدمات الصناعية. "
            "مهمتك الرئيسية هي تقديم معلومات دقيقة عن مجمع عمال مصر وخدماته، والإجابة على استفسارات المستخدمين. "
            "يجب أن تكون إجاباتك مختصرة ومباشرة وباللغة العربية الفصحى بأسلوب محترف."
        )
        
        # إضافة معلومات عن الخدمات
        context += (
            "\n\nخدمات مجمع عمال مصر تشمل: توظيف الكوادر البشرية، الاستثمار الصناعي والزراعي، "
            "التدريب والتأهيل، دراسات الجدوى الاقتصادية، الشراكات الاستراتيجية، "
            "العقارات الصناعية، التسويق المحلي والدولي، وفض المنازعات."
        )
        
        # إضافة معلومات التواصل
        context += (
            f"\n\nبيانات التواصل: "
            f"واتساب المقر الرئيسي: {self.contact_info.get('whatsapp', {}).get('main_office', '01100901200')}, "
            f"البريد الإلكتروني: {self.contact_info.get('email', 'info@omalmisr.com')}, "
            f"الموقع الإلكتروني: {self.contact_info.get('website', 'https://www.omalmisr.com')}"
        )
        
        # إضافة معلومات عن المستخدم إذا كانت متوفرة
        if user_id in self.conversation_state:
            user_name = self.conversation_state[user_id].get("user_name", "")
            user_category = self.conversation_state[user_id].get("user_category", "")
            
            if user_name:
                context += f"\n\nاسم المستخدم: {user_name}"
            
            if user_category:
                context += f"\nفئة المستخدم: {user_category}"
        
        # إضافة توجيهات للرد
        context += (
            "\n\nتوجيهات هامة:"
            "\n1. قدم إجابات دقيقة ومختصرة وعملية."
            "\n2. استخدم لغة رسمية ومهنية."
            "\n3. تجنب التكرار غير المبرر والجمل الإنشائية."
            "\n4. وجّه المستخدم إلى روابط الخدمات المناسبة عند الإمكان."
            "\n5. إذا كان السؤال خارج مجال خدمات مجمع عمال مصر، وجّه المستخدم للتواصل معنا عبر القنوات الرسمية."
        )
        
        return context
    
    def _requires_human_follow_up(self, message: str) -> bool:
        """
        التحقق مما إذا كانت الرسالة تتطلب متابعة بشرية
        
        :param message: رسالة المستخدم
        :return: True إذا كانت الرسالة تتطلب متابعة بشرية، False خلاف ذلك
        """
        message_lower = message.lower()
        
        # قائمة الكلمات التي تشير إلى الحاجة لتدخل بشري
        human_contact_words = [word.lower() for word in self.requires_human_contact]
        
        # التحقق من وجود أي من الكلمات في الرسالة
        return any(word in message_lower for word in human_contact_words)
    
    def _calculate_similarity(self, message: str, question: str) -> float:
        """
        حساب درجة التشابه بين رسالة المستخدم وسؤال معروف
        
        :param message: رسالة المستخدم
        :param question: سؤال معروف
        :return: درجة التشابه (0-1)
        """
        # تنظيف النصوص وتحويلها إلى حروف صغيرة
        message = message.lower().strip()
        question = question.lower().strip()
        
        # قائمة الكلمات المهملة
        stopwords = ['و', 'من', 'في', 'على', 'أن', 'عن', 'إلى', 'هذا', 'هذه', 'هل', 'كيف', 'متى', 'ما', 'الذي', 'التي']
        
        # تقسيم النصوص إلى كلمات وإزالة الكلمات المهملة
        message_words = [word for word in message.split() if word not in stopwords]
        question_words = [word for word in question.split() if word not in stopwords]
        
        # إذا كانت إحدى القوائم فارغة، أعد 0
        if not message_words or not question_words:
            return 0
        
        # حساب مجموعة الكلمات المشتركة والاتحاد
        message_set = set(message_words)
        question_set = set(question_words)
        
        # حساب تشابه جاكارد
        intersection = len(message_set.intersection(question_set))
        union = len(message_set.union(question_set))
        
        # إذا كان هناك تطابق كامل للكلمات، أعد 1
        if message == question:
            return 1.0
        
        # حساب درجة التشابه
        similarity = intersection / union if union > 0 else 0
        
        # تعزيز درجة التشابه إذا كانت هناك كلمات مشتركة متتالية
        if intersection > 0:
            max_common_sequence = self._longest_common_sequence(message_words, question_words)
            if max_common_sequence > 1:  # إذا كان هناك تسلسل مشترك من كلمتين على الأقل
                similarity += 0.1 * max_common_sequence
                similarity = min(similarity, 1.0)  # التأكد من أن القيمة لا تتجاوز 1
        
        return similarity
    
    def _longest_common_sequence(self, list1: List[str], list2: List[str]) -> int:
        """
        حساب أطول تسلسل مشترك بين قائمتين
        
        :param list1: القائمة الأولى
        :param list2: القائمة الثانية
        :return: طول أطول تسلسل مشترك
        """
        m = len(list1)
        n = len(list2)
        
        # جدول حساب أطول تسلسل مشترك
        dp = [[0 for _ in range(n+1)] for _ in range(m+1)]
        
        for i in range(1, m+1):
            for j in range(1, n+1):
                if list1[i-1] == list2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _save_conversation(self, user_id: str, message: str, response: str) -> None:
        """
        حفظ المحادثة في ملف
        
        :param user_id: معرف المستخدم
        :param message: رسالة المستخدم
        :param response: رد الشات بوت
        """
        if not self.save_conversations:
            return
            
        # إنشاء مجلد المحادثات إذا لم يكن موجوداً
        os.makedirs(self.conversations_dir, exist_ok=True)
        
        # اسم ملف المحادثة
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"local_chat_{timestamp}.json"
        
        if "messenger" in user_id:
            filename = f"messenger_{user_id}_{timestamp}.json"
        
        filepath = os.path.join(self.conversations_dir, filename)
        
        # إنشاء سجل المحادثة
        conversation_log = [
            {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "response": response
            }
        ]
        
        try:
            # كتابة الملف
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_log, f, ensure_ascii=False, indent=2)
            
            logger.info(f"تم حفظ المحادثة في: {filepath}")
        except Exception as e:
            logger.error(f"خطأ في حفظ المحادثة: {e}")
    
    def _add_to_conversation_log(self, user_id: str, response: str) -> None:
        """
        إضافة رد الشات بوت إلى سجل المحادثة
        
        :param user_id: معرف المستخدم
        :param response: رد الشات بوت
        """
        if user_id in self.conversation_state:
            self.conversation_state[user_id]["messages"].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
    
    def generate_messenger_response(self, message: str, sender_id: str, sender_name: str = None) -> str:
        """
        توليد رد لرسالة ماسنجر
        
        :param message: رسالة المستخدم
        :param sender_id: معرف المرسل
        :param sender_name: اسم المرسل (اختياري)
        :return: رد الشات بوت
        """
        # معرف فريد للمستخدم
        user_id = f"messenger_{sender_id}"
        
        # توليد الرد
        response = self.generate_response(message, user_id, sender_name)
        
        # إضافة الرد إلى سجل المحادثة
        self._add_to_conversation_log(user_id, response)
        
        return response
    
    def generate_facebook_comment_response(self, comment: str, user_id: str, user_name: str = None, post_id: str = None) -> str:
        """
        توليد رد على تعليق فيسبوك
        
        :param comment: نص التعليق
        :param user_id: معرف المستخدم
        :param user_name: اسم المستخدم (اختياري)
        :param post_id: معرف المنشور (اختياري)
        :return: رد الشات بوت
        """
        # معرف فريد للمستخدم
        comment_user_id = f"fb_comment_{user_id}"
        
        # تجاهل التعليقات القصيرة إذا كان مفعلاً في الإعدادات
        if FACEBOOK_SETTINGS.get("IGNORE_PRAISE_COMMENTS", True):
            # الحد الأدنى لطول التعليق
            comment_length_threshold = int(FACEBOOK_SETTINGS.get("COMMENT_LENGTH_THRESHOLD", 3))
            
            if len(comment.split()) <= comment_length_threshold:
                logger.info(f"تجاهل تعليق قصير من {user_name}: '{comment}'")
                return ""  # لا رد
            
            # تجاهل تعليقات المديح والإعجاب
            praise_words = ["شكراً", "شكرا", "رائع", "جميل", "ممتاز", "احسنت", "أحسنت", 
                            "برافو", "👍", "❤️", "🙏", "🔥", "تمام", "100%", "جزاك الله"]
            
            if any(word in comment for word in praise_words):
                logger.info(f"تجاهل تعليق مديح من {user_name}: '{comment}'")
                return ""  # لا رد
        
        # توليد الرد
        response = self.generate_response(comment, comment_user_id, user_name)
        
        # إضافة الرد إلى سجل المحادثة
        self._add_to_conversation_log(comment_user_id, response)
        
        # حفظ تعليق الفيسبوك في ملف منفصل
        if self.save_conversations:
            os.makedirs(self.conversations_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facebook_comment_{user_id}_{timestamp}.json"
            filepath = os.path.join(self.conversations_dir, filename)
            
            try:
                facebook_comment_log = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "post_id": post_id,
                    "comment": comment,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(facebook_comment_log, f, ensure_ascii=False, indent=2)
                
                logger.info(f"تم حفظ تعليق الفيسبوك في: {filepath}")
            except Exception as e:
                logger.error(f"خطأ في حفظ تعليق الفيسبوك: {e}")
        
        return response