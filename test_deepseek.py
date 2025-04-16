import unittest
import pytest
import json
from unittest.mock import MagicMock, patch
from bot import ChatBot

class TestDeepSeekIntegration:
    """اختبارات التكامل مع DeepSeek API"""
    
    @pytest.fixture
    def bot(self):
        """تهيئة شات بوت للاختبار"""
        bot = ChatBot(data_file="data.json", api_key="test_api_key")
        return bot
    
    @patch("api.requests.post")
    def test_api_connection(self, mock_post, bot):
        """اختبار الاتصال الأساسي بـ DeepSeek API"""
        # تهيئة استجابة وهمية
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "مرحباً، أنا المساعد الرسمي لمجمع عمال مصر. كيف يمكنني مساعدتك؟"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # استدعاء الدالة
        response = bot.api.generate_response("مرحباً")
        
        # التحقق من النتائج
        assert mock_post.called
        assert "choices" in response
        assert response["choices"][0]["message"]["content"]
        
        # التحقق من استخراج النص
        extracted_text = bot.api.extract_response_text(response)
        assert extracted_text == "مرحباً، أنا المساعد الرسمي لمجمع عمال مصر. كيف يمكنني مساعدتك؟"
    
    @patch("api.requests.post")
    def test_api_error_handling(self, mock_post, bot):
        """اختبار معالجة أخطاء API"""
        # محاكاة خطأ في الاستجابة
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API error")
        mock_post.return_value = mock_response
        
        # استدعاء الدالة
        response = bot.api.generate_response("مرحباً")
        
        # التحقق من النتائج
        assert "error" in response
        assert "error_type" in response
        
        # التحقق من استخراج النص بالرغم من الخطأ
        extracted_text = bot.api.extract_response_text(response)
        assert extracted_text  # يجب أن يعيد نصاً احتياطياً
    
    def test_format_system_message(self, bot):
        """اختبار تنسيق رسالة النظام حسب فئة المستخدم"""
        # استخراج رسالة النظام المنسقة اعتماداً على فئة المستخدم
        for user_category in ["باحث عن عمل", "مستثمر", "صحفي"]:
            user_message = "مرحباً"
            context = f"المستخدم اسمه: محمد. الرسالة: {user_message}"
            
            # استخدام ميزة الوصول المباشر إلى المتغيرات الخاصة للاختبار
            with patch("api.requests.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"choices": [{"message": {"content": "مرحباً"}}]}
                mock_post.return_value = mock_response
                
                bot.api.generate_response(
                    user_message, 
                    user_category=user_category,
                    context=context
                )
                
                # الحصول على رسالة النظام من معلمات الطلب
                call_args = mock_post.call_args[1]
                payload = json.loads(call_args["data"])
                system_message = payload["messages"][0]["content"]
                
                # التحقق من أن الرسالة تحتوي على معلومات خاصة بفئة المستخدم
                assert user_category in system_message