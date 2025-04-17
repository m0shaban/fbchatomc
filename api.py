"""
واجهة API للتفاعل مع DeepSeek API وتوليد الردود
"""

import os
import json
import logging
import requests
import re
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
    واجهة للتفاعل مع DeepSeek API
    """
    
    def __init__(self, api_key: str = None):
        """
        تهيئة واجهة DeepSeek API
        
        :param api_key: مفتاح API (اختياري، سيتم استخدام القيمة من الإعدادات إذا لم يتم تحديدها)
        """
        self.api_key = api_key or API_SETTINGS.get("DEEPSEEK_API_KEY")
        self.api_url = API_SETTINGS.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
        self.default_model = API_SETTINGS.get("DEFAULT_MODEL", "deepseek-chat")
        self.max_tokens = API_SETTINGS.get("MAX_TOKENS", 1000)
        self.temperature = API_SETTINGS.get("TEMPERATURE", 0.7)
        
        logger.info(f"تم تهيئة واجهة DeepSeek API بنموذج افتراضي: {self.default_model}")
    
    def generate_response(self, prompt: str, system_message: str = None, 
                          user_category: str = "", context: str = None, 
                          human_expressions: Dict = None, contact_info: Dict = None) -> str:
        """
        توليد رد باستخدام DeepSeek API
        
        :param prompt: سؤال المستخدم
        :param system_message: رسالة النظام (اختياري)
        :param user_category: فئة المستخدم (اختياري)
        :param context: سياق المحادثة (اختياري)
        :param human_expressions: تعبيرات بشرية (اختياري)
        :param contact_info: معلومات الاتصال (اختياري)
        :return: النص المولد
        :raises: Exception في حالة وجود خطأ
        """
        if not self.api_key:
            raise Exception("مفتاح DeepSeek API غير متوفر")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        
        # إضافة السياق كرسالة نظام إذا كان موجودًا
        if system_message:
            messages.append({"role": "system", "content": system_message})
        elif context:
            messages.append({"role": "system", "content": context})
        
        # إضافة سؤال المستخدم
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.default_model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0].get("message", {}).get("content", "")
                return content
            else:
                error_message = f"خطأ في استجابة DeepSeek API: {response_data}"
                logger.error(error_message)
                raise Exception(error_message)
                
        except requests.exceptions.RequestException as e:
            error_message = f"خطأ في الاتصال بـ DeepSeek API: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)
    
    def extract_response_text(self, response: Any) -> str:
        """
        استخراج النص من استجابة API
        
        :param response: الاستجابة من DeepSeek API
        :return: النص المستخرج
        """
        if isinstance(response, str):
            return response
        
        if isinstance(response, dict):
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0].get("message", {}).get("content", "")
            elif "error" in response:
                logger.error(f"خطأ في استجابة API: {response['error']}")
                return f"حدث خطأ: {response.get('error', 'خطأ غير معروف')}"
        
        return str(response)
    
    def validate_connection(self) -> Dict[str, Any]:
        """
        التحقق من صحة الاتصال بـ API
        
        :return: قاموس يحتوي على حالة الاتصال
        """
        result = {
            "status": "غير متصل", 
            "error": None
        }
        
        # اختبار اتصال DeepSeek API
        if self.api_key:
            try:
                test_response = self.generate_response("مرحبا", "هذا اختبار اتصال. رد بكلمة 'متصل' فقط.")
                if "متصل" in test_response.lower():
                    result["status"] = "متصل"
                else:
                    result["error"] = "رد غير متوقع من API"
            except Exception as e:
                result["error"] = str(e)
        else:
            result["error"] = "مفتاح API غير متوفر"
        
        return result


class LLMAPI:
    """
    واجهة للتفاعل مع نماذج اللغة الكبيرة مثل DeepSeek أو OpenAI
    """
    
    def __init__(self):
        """
        تهيئة الواجهة
        """
        self.api_key = API_SETTINGS.get("DEEPSEEK_API_KEY")
        self.api_url = API_SETTINGS.get("DEEPSEEK_API_URL")
        self.default_model = API_SETTINGS.get("DEFAULT_MODEL", "deepseek-chat")
        self.max_tokens = API_SETTINGS.get("MAX_TOKENS", 1000)
        self.temperature = API_SETTINGS.get("TEMPERATURE", 0.7)
        
        # استخدام OpenAI كاحتياطي إذا كان مفتاح OpenAI موجودًا
        self.openai_api_key = API_SETTINGS.get("OPENAI_API_KEY")
        
        logger.info(f"تم تهيئة واجهة API بنموذج افتراضي: {self.default_model}")
    
    def generate_response(self, prompt: str, context: str = None, model: str = None) -> str:
        """
        توليد رد باستخدام DeepSeek API أو OpenAI API
        
        :param prompt: سؤال المستخدم
        :param context: سياق المحادثة (اختياري)
        :param model: اسم النموذج (اختياري)
        :return: النص المولد
        :raises: Exception في حالة وجود خطأ
        """
        # تحديد النموذج المستخدم
        model_name = model or self.default_model
        
        # تحديد ما إذا كان سيتم استخدام DeepSeek أو OpenAI
        if "deepseek" in model_name.lower() and self.api_key:
            return self._generate_with_deepseek(prompt, context, model_name)
        elif self.openai_api_key:
            return self._generate_with_openai(prompt, context, model_name)
        elif self.api_key:
            # استخدام DeepSeek بشكل افتراضي
            return self._generate_with_deepseek(prompt, context, model_name)
        else:
            raise Exception("لم يتم توفير مفتاح API صالح")
    
    def _generate_with_deepseek(self, prompt: str, context: str = None, model: str = None) -> str:
        """
        توليد رد باستخدام DeepSeek API
        
        :param prompt: سؤال المستخدم
        :param context: سياق المحادثة (اختياري)
        :param model: اسم النموذج (اختياري)
        :return: النص المولد
        :raises: Exception في حالة وجود خطأ
        """
        if not self.api_key:
            raise Exception("مفتاح DeepSeek API غير متوفر")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        
        # إضافة السياق كرسالة نظام إذا كان موجودًا
        if context:
            messages.append({"role": "system", "content": context})
        
        # إضافة سؤال المستخدم
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0].get("message", {}).get("content", "")
                return content
            else:
                error_message = f"خطأ في استجابة DeepSeek API: {response_data}"
                logger.error(error_message)
                raise Exception(error_message)
                
        except requests.exceptions.RequestException as e:
            error_message = f"خطأ في الاتصال بـ DeepSeek API: {str(e)}"
            logger.error(error_message)
            
            # محاولة استخدام OpenAI كاحتياطي إذا كان متاحًا
            if self.openai_api_key:
                logger.info("محاولة استخدام OpenAI API كاحتياطي")
                return self._generate_with_openai(prompt, context, "gpt-3.5-turbo")
            else:
                raise Exception(error_message)
    
    def _generate_with_openai(self, prompt: str, context: str = None, model: str = None) -> str:
        """
        توليد رد باستخدام OpenAI API
        
        :param prompt: سؤال المستخدم
        :param context: سياق المحادثة (اختياري)
        :param model: اسم النموذج (اختياري)
        :return: النص المولد
        :raises: Exception في حالة وجود خطأ
        """
        if not self.openai_api_key:
            raise Exception("مفتاح OpenAI API غير متوفر")
        
        import openai
        
        openai.api_key = self.openai_api_key
        
        messages = []
        
        # إضافة السياق كرسالة نظام إذا كان موجودًا
        if context:
            messages.append({"role": "system", "content": context})
        
        # إضافة سؤال المستخدم
        messages.append({"role": "user", "content": prompt})
        
        try:
            # استخدام النموذج المحدد أو النموذج الافتراضي
            openai_model = model if "gpt" in model.lower() else "gpt-3.5-turbo"
            
            response = openai.ChatCompletion.create(
                model=openai_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_message = f"خطأ في الاتصال بـ OpenAI API: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)
    
    def validate_connection(self) -> Dict[str, Any]:
        """
        التحقق من صحة الاتصال بـ API
        
        :return: قاموس يحتوي على حالة الاتصال
        """
        result = {
            "deepseek_api": {"status": "غير متصل", "error": None},
            "openai_api": {"status": "غير متصل", "error": None}
        }
        
        # اختبار اتصال DeepSeek API
        if self.api_key:
            try:
                test_response = self._generate_with_deepseek("مرحبا", "هذا اختبار اتصال. رد بكلمة 'متصل' فقط.")
                if "متصل" in test_response.lower():
                    result["deepseek_api"]["status"] = "متصل"
                else:
                    result["deepseek_api"]["error"] = "رد غير متوقع من API"
            except Exception as e:
                result["deepseek_api"]["error"] = str(e)
        else:
            result["deepseek_api"]["error"] = "مفتاح API غير متوفر"
        
        # اختبار اتصال OpenAI API
        if self.openai_api_key:
            try:
                test_response = self._generate_with_openai("مرحبا", "هذا اختبار اتصال. رد بكلمة 'متصل' فقط.")
                if "متصل" in test_response.lower():
                    result["openai_api"]["status"] = "متصل"
                else:
                    result["openai_api"]["error"] = "رد غير متوقع من API"
            except Exception as e:
                result["openai_api"]["error"] = str(e)
        else:
            result["openai_api"]["error"] = "مفتاح API غير متوفر"
        
        return result