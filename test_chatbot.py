"""
اختبارات آلية لشات بوت مجمع عمال مصر
"""

import unittest
import os
import json
import sys
from unittest.mock import patch, MagicMock

# التأكد من أن المجلد الحالي في مسار النظام
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from bot import ChatBot
from facebook_comments import FacebookCommentsHandler
from config import setup_log_directory, setup_conversations_directory


class TestChatBot(unittest.TestCase):
    """
    اختبارات الشات بوت الأساسية
    """
    
    def setUp(self):
        """
        الإعداد قبل كل اختبار
        """
        # إنشاء مجلدات السجلات والمحادثات للاختبار
        setup_log_directory()
        setup_conversations_directory()
        
        # إنشاء كائن الشات بوت للاختبار
        self.bot = ChatBot()
        
        # التأكد من وجود ملف البيانات
        self.assertTrue(os.path.exists(self.bot.data_file), "ملف البيانات غير موجود")
    
    def test_load_data(self):
        """
        اختبار تحميل البيانات من ملف JSON
        """
        # التحقق من تحميل البيانات بنجاح
        self.assertGreater(len(self.bot.prompts), 0, "لم يتم تحميل أي أسئلة وأجوبة")
        self.assertGreater(len(self.bot.human_expressions), 0, "لم يتم تحميل أي تعبيرات بشرية")
        self.assertGreater(len(self.bot.service_links), 0, "لم يتم تحميل أي روابط خدمات")
    
    def test_detect_user_category(self):
        """
        اختبار تحديد فئة المستخدم
        """
        # اختبار تحديد باحث عن عمل
        job_seeker_message = "أبحث عن وظيفة في مجال الصناعات الغذائية"
        self.assertEqual(self.bot._detect_user_category(job_seeker_message), "باحث عن عمل")
        
        # اختبار تحديد مستثمر
        investor_message = "أنا مستثمر وأرغب في معرفة فرص الاستثمار المتاحة"
        self.assertEqual(self.bot._detect_user_category(investor_message), "مستثمر")
        
        # اختبار تحديد صحفي
        media_message = "أنا صحفي وأرغب في عمل تقرير عن المجمع"
        self.assertEqual(self.bot._detect_user_category(media_message), "صحفي")
        
        # اختبار رسالة عامة
        general_message = "مرحباً، كيف حالكم؟"
        self.assertEqual(self.bot._detect_user_category(general_message), "")
    
    def test_detect_service_request(self):
        """
        اختبار تحديد طلب خدمة
        """
        # اختبار طلب التوظيف
        jobs_message = "كيف يمكنني التقديم للوظائف لديكم؟"
        service_info = self.bot._detect_service_request(jobs_message)
        self.assertIn("link", service_info)
        self.assertIn("jobs", service_info.get("link", ""))
        
        # اختبار طلب خدمات الشركات
        companies_message = "أريد معرفة الخدمات التي تقدمونها للشركات"
        service_info = self.bot._detect_service_request(companies_message)
        self.assertIn("link", service_info)
        self.assertIn("companies", service_info.get("link", ""))
    
    def test_search_knowledge_base(self):
        """
        اختبار البحث في قاعدة المعرفة
        """
        # اختبار البحث عن سؤال موجود
        question = "ما هو مجمع عمال مصر"
        best_match, score = self.bot.search_knowledge_base(question)
        self.assertIsNotNone(best_match)
        self.assertGreater(score, 0.3)
        
        # اختبار البحث عن سؤال قريب
        question = "أين يقع المجمع"
        best_match, score = self.bot.search_knowledge_base(question)
        self.assertIsNotNone(best_match)
        
        # اختبار البحث عن سؤال غير موجود
        question = "كم سعر البيتزا"
        best_match, score = self.bot.search_knowledge_base(question)
        self.assertLess(score, self.bot.similarity_threshold)
    
    @patch('bot.DeepSeekAPI')
    def test_generate_messenger_response(self, mock_api):
        """
        اختبار توليد رد للماسنجر
        """
        # إعداد الـ mock للـ API
        mock_api_instance = MagicMock()
        mock_api_instance.generate_response.return_value = {"choices": [{"message": {"content": "هذا رد اختباري"}}]}
        mock_api_instance.extract_response_text.return_value = "هذا رد اختباري"
        mock_api.return_value = mock_api_instance
        
        # إعادة تهيئة الشات بوت مع الـ mock
        self.bot.api = mock_api_instance
        
        # اختبار توليد رد للماسنجر
        message = "مرحباً، ما هي خدمات المجمع؟"
        response = self.bot.generate_messenger_response(message)
        
        # التحقق من استدعاء الـ API
        mock_api_instance.generate_response.assert_called_once()
        
        # التحقق من محتوى الرد
        self.assertTrue(response)
        self.assertIn("رد اختباري", response)
    
    @patch('bot.DeepSeekAPI')
    def test_generate_comment_response(self, mock_api):
        """
        اختبار توليد رد لتعليق فيسبوك
        """
        # إعداد الـ mock للـ API
        mock_api_instance = MagicMock()
        mock_api_instance.generate_response.return_value = {"choices": [{"message": {"content": "هذا رد اختباري لتعليق فيسبوك"}}]}
        mock_api_instance.extract_response_text.return_value = "هذا رد اختباري لتعليق فيسبوك"
        mock_api.return_value = mock_api_instance
        
        # إعادة تهيئة الشات بوت مع الـ mock
        self.bot.api = mock_api_instance
        
        # اختبار توليد رد لتعليق فيسبوك
        comment = "كيف يمكنني التقديم للوظائف؟"
        response = self.bot.generate_comment_response(comment)
        
        # التحقق من استدعاء الـ API
        mock_api_instance.generate_response.assert_called_once()
        
        # التحقق من محتوى الرد
        self.assertTrue(response)
        self.assertIn("رد اختباري", response)
    
    def test_save_conversation_history(self):
        """
        اختبار حفظ تاريخ المحادثة
        """
        # إضافة بعض الرسائل إلى تاريخ المحادثة
        self.bot.conversation_history = [
            {"role": "user", "message": "مرحباً"},
            {"role": "bot", "message": "مرحباً بك، كيف يمكنني مساعدتك؟"},
            {"role": "user", "message": "ما هي خدماتكم؟"},
            {"role": "bot", "message": "نقدم العديد من الخدمات..."}
        ]
        
        # حفظ تاريخ المحادثة في ملف مؤقت
        temp_file = "temp_conversation.json"
        result = self.bot.save_conversation_history(temp_file)
        
        # التحقق من نجاح الحفظ
        self.assertTrue(result)
        self.assertTrue(os.path.exists(temp_file))
        
        # التحقق من محتوى الملف
        with open(temp_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data), 4)
        
        # حذف الملف المؤقت
        if os.path.exists(temp_file):
            os.remove(temp_file)


class TestFacebookCommentsHandler(unittest.TestCase):
    """
    اختبارات معالج تعليقات الفيسبوك
    """
    
    def setUp(self):
        """
        الإعداد قبل كل اختبار
        """
        # إنشاء مجلدات السجلات والمحادثات للاختبار
        setup_log_directory()
        setup_conversations_directory()
        
        # إنشاء كائن الشات بوت للاختبار
        self.bot = ChatBot()
        
        # إنشاء كائن معالج تعليقات الفيسبوك للاختبار
        self.comments_handler = FacebookCommentsHandler(self.bot)
    
    def test_should_respond_to_comment(self):
        """
        اختبار تحديد ما إذا كان التعليق يستحق الرد
        """
        # تعليق يستحق الرد
        valid_comment = "كيف يمكنني التقديم للوظائف لديكم؟"
        self.assertTrue(self.comments_handler.should_respond_to_comment(valid_comment))
        
        # تعليق إشادة لا يستحق الرد
        praise_comment = "رائع جداً"
        self.assertFalse(self.comments_handler.should_respond_to_comment(praise_comment))
        
        # تعليق غير مرغوب فيه
        unwanted_comment = "هذا فاشل جداً"
        self.assertFalse(self.comments_handler.should_respond_to_comment(unwanted_comment))
        
        # تعليق قصير جداً
        short_comment = "هـ"
        self.assertFalse(self.comments_handler.should_respond_to_comment(short_comment))
    
    def test_get_comment_category(self):
        """
        اختبار تحديد فئة التعليق
        """
        # تعليق من فئة باحث عن عمل
        job_comment = "كيف يمكنني التقديم للوظائف؟"
        self.assertEqual(self.comments_handler.get_comment_category(job_comment), "باحث عن عمل")
        
        # تعليق من فئة مستثمر
        investor_comment = "أرغب في معرفة فرص الاستثمار المتاحة"
        self.assertEqual(self.comments_handler.get_comment_category(investor_comment), "مستثمر")
        
        # تعليق من فئة صحفي
        media_comment = "أريد عقد مقابلة صحفية"
        self.assertEqual(self.comments_handler.get_comment_category(media_comment), "صحفي")
        
        # تعليق عام
        general_comment = "هل يمكنني زيارة المجمع؟"
        self.assertEqual(self.comments_handler.get_comment_category(general_comment), "")
    
    @patch('facebook_comments.ChatBot')
    def test_generate_comment_response(self, mock_bot):
        """
        اختبار توليد رد على تعليق
        """
        # إعداد الـ mock للشات بوت
        mock_bot_instance = MagicMock()
        mock_bot_instance.generate_response.return_value = "هذا رد اختباري على تعليق فيسبوك"
        mock_bot.return_value = mock_bot_instance
        
        # إعادة تهيئة معالج التعليقات مع الـ mock
        self.comments_handler.chatbot = mock_bot_instance
        
        # اختبار توليد رد على تعليق صالح
        valid_comment = "كيف يمكنني التقديم للوظائف؟"
        response = self.comments_handler.generate_comment_response(valid_comment)
        
        # التحقق من استدعاء الشات بوت
        mock_bot_instance.generate_response.assert_called_once()
        
        # التحقق من محتوى الرد
        self.assertTrue(response)
        self.assertIn("رد اختباري", response)
        
        # اختبار عدم توليد رد على تعليق غير صالح
        mock_bot_instance.generate_response.reset_mock()
        invalid_comment = "رائع"
        response = self.comments_handler.generate_comment_response(invalid_comment)
        
        # التحقق من عدم استدعاء الشات بوت
        mock_bot_instance.generate_response.assert_not_called()
        
        # التحقق من محتوى الرد
        self.assertEqual(response, "")
    
    def test_sanitize_response(self):
        """
        اختبار تنقية الرد من أي إشارات إلى الذكاء الاصطناعي
        """
        # رد يحتوي على إشارات إلى الذكاء الاصطناعي
        ai_response = "أنا ذكاء اصطناعي مدرب لمساعدتك. يمكنني كـ chatbot توفير معلومات."
        
        # تنقية الرد
        sanitized = self.comments_handler._sanitize_response(ai_response)
        
        # التحقق من نتيجة التنقية
        self.assertNotIn("ذكاء اصطناعي", sanitized)
        self.assertNotIn("chatbot", sanitized)
        self.assertIn("المساعد الرسمي لمجمع عمال مصر", sanitized)


if __name__ == "__main__":
    # تشغيل جميع الاختبارات
    unittest.main()