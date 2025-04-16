"""
اختبارات آلية لشات بوت مجمع عمال مصر
"""
import os
import pytest
import json
from unittest.mock import MagicMock, patch
from bot import ChatBot

class TestChatBot:
    """
    اختبارات آلية لشات بوت مجمع عمال مصر
    """
    
    @pytest.fixture
    def bot(self):
        """تهيئة شات بوت للاختبار"""
        # استخدام ملف بيانات الاختبار
        bot = ChatBot(data_file="data.json", api_key="test_api_key")
        return bot
    
    def test_initialization(self, bot):
        """اختبار تهيئة الشات بوت"""
        assert bot.bot_name == "محمد سلامة"
        assert bot.data_file == "data.json"
        assert len(bot.prompts) > 0
        assert bot.api.api_key == "test_api_key"
    
    def test_search_knowledge_base(self, bot):
        """اختبار البحث في قاعدة المعرفة"""
        # اختبار سؤال مطابق تماماً
        match, score = bot.search_knowledge_base("ما هو مجمع عمال مصر؟")
        assert match is not None
        assert score > 0.5
        assert "مجمع عمال مصر" in match["answer"]
        
        # اختبار سؤال مشابه
        match, score = bot.search_knowledge_base("عايز اعرف ايه هو مجمع عمال مصر")
        assert match is not None
        assert score > 0.2
        
        # اختبار سؤال غير مرتبط
        match, score = bot.search_knowledge_base("حالة الطقس غداً")
        # قد يجد تطابقاً ضعيفاً، لكن النتيجة ستكون منخفضة
        assert score < bot.similarity_threshold
    
    def test_detect_user_category(self, bot):
        """اختبار تحديد فئة المستخدم"""
        assert bot._detect_user_category("أبحث عن وظيفة") == "باحث عن عمل"
        assert bot._detect_user_category("لدي مشروع أريد استثماره") == "مستثمر"
        assert bot._detect_user_category("صحفي وأريد إجراء مقابلة") == "صحفي"
        assert bot._detect_user_category("شركتنا تبحث عن تعاون") == "شركة"
        assert bot._detect_user_category("مرحباً فقط") == ""
    
    def test_detect_service_request(self, bot):
        """اختبار تحديد طلب خدمة"""
        # طلب وظيفة
        job_service = bot._detect_service_request("أريد التقديم على وظيفة")
        assert job_service
        assert "jobs" in job_service.get("link", "")
        
        # طلب عمال
        workers_service = bot._detect_service_request("أحتاج عمال لمصنعي")
        assert workers_service
        assert "workers" in workers_service.get("link", "")
        
        # طلب غير مرتبط بخدمة
        unrelated = bot._detect_service_request("كيف حالك اليوم؟")
        assert not unrelated
    
    def test_is_continuation_message(self, bot):
        """اختبار تحديد رسائل الاستمرار"""
        assert bot._is_continuation_message("نعم")
        assert bot._is_continuation_message("أيوة أريد المزيد")
        assert bot._is_continuation_message("طبعا عايز اعرف")
        assert not bot._is_continuation_message("لا شكراً")
        assert not bot._is_continuation_message("خلاص كفاية")
    
    def test_extract_name(self, bot):
        """اختبار استخراج الاسم من رسالة المستخدم"""
        assert bot._extract_name("اسمي محمد") == "محمد"
        assert bot._extract_name("أنا أحمد علي") == "أحمد علي"
        assert bot._extract_name("الدكتور مصطفى كامل") == "مصطفى كامل"
        assert bot._extract_name("") == "صديقي العزيز"
    
    @patch("bot.DeepSeekAPI.generate_response")
    def test_generate_response_with_match(self, mock_api, bot):
        """اختبار توليد رد باستخدام قاعدة المعرفة"""
        # تعيين قيمة وهمية للتطابق
        bot.similarity_threshold = 0.01  # لضمان إيجاد تطابق
        
        # نصنع معرف مستخدم وهمي
        user_id = "test_user_123"
        
        # نضمن أن المستخدم ليس في حالة انتظار الاسم
        bot.conversation_state[user_id] = {"awaiting_name": False}
        
        # اختبار الرد على سؤال موجود في قاعدة المعرفة
        response = bot.generate_response("ما هو مجمع عمال مصر؟", user_id)
        
        # يجب أن يكون الرد ليس فارغاً
        assert response
        assert len(response) > 0
        
        # يجب أن يكون الرد يحتوي على معلومات من قاعدة المعرفة
        assert "مجمع عمال مصر" in response
        
        # يجب ألا يكون استدعي API لأن السؤال موجود في قاعدة المعرفة
        mock_api.assert_not_called()
    
    @patch("bot.DeepSeekAPI.generate_response")
    def test_generate_response_with_api(self, mock_api, bot):
        """اختبار توليد رد باستخدام DeepSeek API"""
        # تعيين قيمة عالية للتطابق لضمان استخدام API
        bot.similarity_threshold = 0.99
        
        # نصنع معرف مستخدم وهمي
        user_id = "test_user_456"
        
        # نضمن أن المستخدم ليس في حالة انتظار الاسم
        bot.conversation_state[user_id] = {"awaiting_name": False, "name_asked": True}
        
        # تعيين رد وهمي من API
        mock_api_response = {
            "choices": [
                {
                    "message": {
                        "content": "هذا رد من DeepSeek API الوهمي للاختبار"
                    }
                }
            ]
        }
        mock_api.return_value = mock_api_response
        
        # استدعاء الدالة مع سؤال غير موجود في قاعدة المعرفة
        response = bot.generate_response("سؤال غير موجود في قاعدة المعرفة", user_id)
        
        # التحقق من استدعاء API
        mock_api.assert_called_once()
        
        # يجب أن يكون الرد ليس فارغاً
        assert response
        assert len(response) > 0
    
    @patch("bot.DeepSeekAPI.generate_response")
    def test_generate_response_with_api_error(self, mock_api, bot):
        """اختبار آلية الاحتياط عند فشل API"""
        # تعيين قيمة عالية للتطابق لضمان استخدام API
        bot.similarity_threshold = 0.99
        
        # نصنع معرف مستخدم وهمي
        user_id = "test_user_789"
        
        # نضمن أن المستخدم ليس في حالة انتظار الاسم
        bot.conversation_state[user_id] = {"awaiting_name": False, "name_asked": True}
        
        # تعيين خطأ وهمي من API
        mock_api.side_effect = Exception("فشل وهمي في الاتصال بـ API")
        
        # استدعاء الدالة مع سؤال غير موجود في قاعدة المعرفة
        response = bot.generate_response("سؤال غير موجود في قاعدة المعرفة", user_id)
        
        # التحقق من استدعاء API
        mock_api.assert_called_once()
        
        # يجب أن يكون الرد ليس فارغاً (رد احتياطي)
        assert response
        assert len(response) > 0
        
        # يجب أن يحتوي الرد على معلومات التواصل
        assert "01100901200" in response or "info@omalmisr.com" in response
    
    def test_name_asking_flow(self, bot):
        """اختبار تدفق طلب الاسم من المستخدم"""
        # نصنع معرف مستخدم وهمي
        user_id = "test_user_name"
        
        # الرسالة الأولى يجب أن تكون طلب الاسم
        first_response = bot.generate_response("مرحباً", user_id)
        assert "ما هو اسمك" in first_response or "اسم حضرتك" in first_response
        
        # الرسالة الثانية (رد المستخدم باسمه) يجب أن تكون ترحيب
        second_response = bot.generate_response("أحمد محمد", user_id)
        assert "أحمد" in second_response
        assert bot.conversation_state[user_id]["awaiting_name"] == False
        assert bot.conversation_history[user_id]["user_name"] == "أحمد محمد"
        
        # التحقق من أن المستخدم لم يعد في مرحلة طلب الاسم
        third_response = bot.generate_response("ما هو مجمع عمال مصر؟", user_id)
        assert "ما هو اسمك" not in third_response
    
    def test_conversation_history(self, bot):
        """اختبار حفظ تاريخ المحادثة"""
        # نصنع معرف مستخدم وهمي
        user_id = "test_history"
        
        # تجاوز مرحلة طلب الاسم
        bot.conversation_state[user_id] = {"awaiting_name": False}
        bot.conversation_history[user_id] = {"user_name": "اختبار"}
        
        # إرسال عدة رسائل
        messages = [
            "مرحباً",
            "ما هو مجمع عمال مصر؟",
            "كيف يمكنني التقديم للوظائف؟"
        ]
        
        for message in messages:
            bot.generate_response(message, user_id)
        
        # التحقق من حفظ الرسائل في تاريخ المحادثة
        assert "messages" in bot.conversation_history[user_id]
        assert len(bot.conversation_history[user_id]["messages"]) == len(messages)
    
    def test_format_response(self, bot):
        """اختبار تنسيق الرد"""
        user_id = "test_format"
        bot.conversation_history[user_id] = {"user_name": "محمد"}
        
        simple_answer = "هذا رد بسيط للاختبار"
        formatted = bot._format_response(simple_answer, "سؤال اختبار", user_id)
        
        # التحقق من إضافة اسم المستخدم
        assert "محمد" in formatted
        
        # التحقق من إضافة روابط أو معلومات تواصل
        assert "https://" in formatted or "01100901200" in formatted
    
    def test_generate_contextual_question(self, bot):
        """اختبار توليد أسئلة سياقية"""
        job_question = bot._generate_contextual_question("أبحث عن وظيفة", "باحث عن عمل")
        assert "?" in job_question or "؟" in job_question
        assert len(job_question) > 10
        
        investor_question = bot._generate_contextual_question("أريد الاستثمار", "مستثمر")
        assert "?" in investor_question or "؟" in investor_question
        assert len(investor_question) > 10
        
        # التحقق من أن لكل فئة أسئلة مختلفة
        assert job_question != investor_question