"""
وحدة توفر واجهات بديلة لدمج DeepSeek API
تتضمن تنفيذاً بديلاً باستخدام مكتبة OpenAI
"""

import logging
from typing import Dict, List, Any, Optional
from config import API_SETTINGS, APP_SETTINGS

# إعداد التسجيل
logger = logging.getLogger(__name__)

class OpenAIClientAPI:
    """
    صنف يستخدم مكتبة OpenAI للاتصال بـ DeepSeek API
    يمكن استخدامه كبديل للتنفيذ الأساسي في api.py
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        تهيئة الاتصال مع DeepSeek API باستخدام مكتبة OpenAI
        
        :param api_key: مفتاح API، إذا لم يتم توفيره سيتم البحث عنه في متغيرات البيئة
        """
        self.api_key = api_key or API_SETTINGS.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("مفتاح API غير متوفر. يرجى تمريره للدالة أو تعيينه كمتغير بيئة.")
        
        try:
            # استخدام مكتبة OpenAI لاستدعاء DeepSeek API
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key, 
                base_url="https://api.deepseek.com"  # عنوان API الأساسي
            )
            logger.info("تم تهيئة OpenAI Client للتواصل مع DeepSeek API")
        except ImportError:
            logger.error("فشل في استيراد مكتبة OpenAI. يرجى تثبيتها باستخدام pip install openai")
            raise
    
    def generate_response(self, user_message: str, system_message: str = None, 
                          user_category: str = "", context: str = "", 
                          human_expressions: Dict[str, List[str]] = None,
                          contact_info: Dict = None) -> Dict[str, Any]:
        """
        استخدام OpenAI Client للاتصال بـ DeepSeek API وتوليد رد
        
        :param user_message: رسالة المستخدم
        :param system_message: رسالة النظام، إذا لم يتم توفيرها فسيتم استخدام رسالة افتراضية
        :param user_category: فئة المستخدم (لأغراض التوافق مع الواجهة الأصلية)
        :param context: سياق إضافي (لأغراض التوافق مع الواجهة الأصلية)
        :param human_expressions: قائمة بالتعبيرات البشرية (لأغراض التوافق مع الواجهة الأصلية)
        :param contact_info: معلومات الاتصال (لأغراض التوافق مع الواجهة الأصلية)
        :return: رد النموذج بتنسيق يتوافق مع التنفيذ الأصلي
        """
        try:
            if system_message is None:
                system_message = "أنت المساعد الرسمي لمجمع عمال مصر. تتحدث بلغة عربية مهنية."
            
            # تسجيل الطلب
            logger.info(f"إرسال طلب إلى DeepSeek API عبر OpenAI Client: {user_message[:50]}..." 
                      if len(user_message) > 50 else f"إرسال طلب إلى DeepSeek API: {user_message}")
            
            # الاتصال بـ API
            response = self.client.chat.completions.create(
                model="deepseek-chat",  # استخدام DeepSeek-V3
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=float(API_SETTINGS.get("TEMPERATURE", 0.7)),
                max_tokens=int(API_SETTINGS.get("MAX_TOKENS", 1000)),
                stream=False  # يمكن تعيينها إلى True للحصول على استجابة متدفقة
            )
            
            # تحويل الاستجابة إلى تنسيق متوافق مع التنفيذ الأصلي
            logger.info(f"تم استلام رد من DeepSeek API عبر OpenAI Client بنجاح")
            return {
                "choices": [
                    {
                        "message": {
                            "content": response.choices[0].message.content
                        }
                    }
                ]
            }
        except Exception as e:
            logger.error(f"خطأ في استدعاء DeepSeek API عبر مكتبة OpenAI: {e}")
            # إعادة تنسيق الخطأ ليكون متوافقاً مع التنفيذ الأصلي
            return {
                "error": str(e),
                "error_type": "openai_client_error",
                "choices": [
                    {
                        "message": {
                            "content": "عذراً، حدث خطأ أثناء الاتصال بالخادم. يمكنك التواصل معنا مباشرة على الرقم: 01100901200"
                        }
                    }
                ]
            }
    
    def extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        استخراج النص من استجابة API
        
        :param response: الاستجابة من DeepSeek API
        :return: النص المستخرج
        """
        try:
            if "error" in response:
                logger.error(f"خطأ في استجابة API: {response['error']}")
                # إرجاع الرد الاحتياطي إذا كان متوفراً
                if "choices" in response and len(response["choices"]) > 0:
                    return response["choices"][0]["message"]["content"]
                return "عذراً، حدث خطأ أثناء معالجة الرد. يمكنك التواصل معنا مباشرة."
            
            # استخراج النص من استجابة API
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                logger.debug(f"تم استخراج النص من استجابة API: {content[:100]}...")
                return content
            
            # في حال لم يتم العثور على محتوى
            logger.warning("لم يتم العثور على محتوى في استجابة API")
            return "عذراً، لم نتمكن من معالجة استفسارك. يرجى المحاولة مرة أخرى."
            
        except Exception as e:
            logger.error(f"خطأ في استخراج النص: {e}")
            return "عذراً، حدث خطأ أثناء معالجة الرد. يمكنك التواصل معنا مباشرة على الرقم: 01100901200."


def get_api_client(implementation: str = "default", api_key: Optional[str] = None):
    """
    وظيفة المساعدة للحصول على المنفذ المناسب لـ API
    
    :param implementation: نوع التنفيذ المطلوب ("default" أو "openai")
    :param api_key: مفتاح API اختياري
    :return: كائن API
    """
    if implementation.lower() == "openai":
        try:
            return OpenAIClientAPI(api_key)
        except ImportError:
            logger.warning("فشل في استخدام OpenAI Client، العودة إلى التنفيذ الافتراضي")
    
    # العودة إلى التنفيذ الافتراضي
    from api import DeepSeekAPI
    return DeepSeekAPI(api_key)