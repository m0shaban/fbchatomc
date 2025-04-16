"""
وحدة توفر واجهات بديلة لدمج DeepSeek API
تتضمن تنفيذاً بديلاً باستخدام مكتبة OpenAI
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from config import API_SETTINGS, APP_SETTINGS
import re
import random
import json
import os

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


def load_data_file(data_file: str = "data.json") -> Dict:
    """
    تحميل بيانات من ملف JSON
    
    :param data_file: مسار ملف البيانات
    :return: البيانات المحملة كقاموس
    """
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"خطأ في تحميل ملف البيانات: {e}")
        return {}


def get_company_info(data_file: str = "data.json") -> str:
    """
    الحصول على معلومات شاملة عن مجمع عمال مصر
    
    :param data_file: مسار ملف البيانات
    :return: نص المعلومات
    """
    data = load_data_file(data_file)
    
    # البحث عن الأسئلة المتعلقة بالمعلومات عن المجمع
    about_company = ""
    leadership = ""
    projects = ""
    goals = ""
    locations = ""
    
    for prompt in data.get("prompts", []):
        # ما هو مجمع عمال مصر؟
        if prompt.get("id") == 1 or "ما هو مجمع عمال مصر" in prompt.get("question", ""):
            about_company = prompt.get("answer", "")
        # من يدير المجمع؟
        elif prompt.get("id") == 2 or "من يدير المجمع" in prompt.get("question", ""):
            leadership = prompt.get("answer", "")
        # ما هي أبرز مشروعات المجمع؟
        elif prompt.get("id") == 3 or "مشروعات المجمع" in prompt.get("question", ""):
            projects = prompt.get("answer", "")
        # ما هي أهداف المجمع؟
        elif prompt.get("id") == 4 or "أهداف المجمع" in prompt.get("question", ""):
            goals = prompt.get("answer", "")
        # أين مقر الشركة؟
        elif "مقر" in prompt.get("question", "").lower() or "عنوان" in prompt.get("question", "").lower():
            locations = prompt.get("answer", "")
    
    # إذا لم نجد المعلومات، نقدم رد افتراضي
    if not about_company:
        about_company = "مجمع عمال مصر هو مؤسسة وطنية تعمل على توفير خدمات متكاملة للعمال والشركات، بهدف تعزيز بيئة العمل وزيادة الإنتاجية والمساهمة في التنمية الاقتصادية."
    
    if not leadership:
        leadership = "يدير المجمع مجلس إدارة يضم نخبة من الكفاءات المصرية المتخصصة في مجالات العمل والصناعة."
    
    if not locations:
        locations = "المقر الرئيسي للمجمع يقع في القاهرة، بالإضافة إلى فروع في المحافظات الكبرى."
    
    # تجميع المعلومات في رد شامل
    response = f"""معلومات عن مجمع عمال مصر:

• *نبذة عن المجمع*:
{about_company}

• *قيادة المجمع*:
{leadership}
"""

    # إضافة أهداف المجمع إذا كانت متوفرة
    if goals:
        response += f"""
• *أهداف المجمع*:
{goals}
"""

    # إضافة مشروعات المجمع إذا كانت متوفرة
    if projects:
        response += f"""
• *أبرز المشروعات*:
{projects}
"""

    # إضافة مقرات المجمع إذا كانت متوفرة
    if locations:
        response += f"""
• *مقرات المجمع*:
{locations}
"""

    # إضافة معلومات التواصل
    response += f"""
• *للتواصل معنا*:
📞 تليفون/واتساب: {data.get("contact_info", {}).get("whatsapp", {}).get("main_office", "01100901200")}
✉️ البريد الإلكتروني: {data.get("contact_info", {}).get("email", "info@omalmisr.com")}
🌐 الموقع الرسمي: {data.get("contact_info", {}).get("website", "https://www.omalmisr.com/")}
"""

    return response


def handle_local_response(user_message: str, data_file: str = "data.json") -> Tuple[str, bool]:
    """
    تحقق مما إذا كان بإمكاننا معالجة رسالة المستخدم محلياً دون الحاجة إلى API
    
    :param user_message: رسالة المستخدم
    :param data_file: مسار ملف البيانات (data.json)
    :return: الرد المناسب ومؤشر على ما إذا تم العثور على رد
    """
    try:
        # تحميل البيانات
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # تنظيف رسالة المستخدم
        user_message = user_message.strip().lower()
        
        # التحقق من الأسئلة المتعلقة بمعلومات الشركة أو المجمع
        company_info_patterns = [
            r'معلومات عن (الشركة|الشركه|المجمع|المنظمة|المنظومة|مجمع العمال|مجمع عمال مصر)',
            r'(ما هي|ما هو|ماهي|ماهو) (الشركة|الشركه|المجمع|المنظمة|المنظومة|مجمع العمال|مجمع عمال مصر)',
            r'(عايز|أريد|اريد) (اعرف|أعرف) (عن|حول|المزيد) (الشركة|الشركه|المجمع|المنظمة|المنظومة|مجمع العمال)',
            r'(عرفني|اعطني|اعطيني) (معلومات|نبذة) عن (الشركة|الشركه|المجمع|المنظمة|المنظومة|مجمع العمال)',
            r'(نبذة|لمحة) عن (الشركة|الشركه|المجمع|المنظمة|المنظومة|مجمع العمال)',
            r'من (انتم|أنتم|هم)',
            r'(شركة|شركه|مجمع) (عمال مصر|ايه|إيه)'
        ]
        
        # التحقق من وجود نمط يتعلق بمعلومات الشركة
        company_info_match = any(re.search(pattern, user_message) for pattern in company_info_patterns)
        
        if company_info_match or "معلومات عن الشركة" in user_message:
            # استخدام وظيفة get_company_info لتجميع معلومات شاملة عن المجمع
            company_info = get_company_info(data_file)
            
            # إضافة تعبيرات بشرية لتحسين الرد
            greeting = random.choice(data.get("human_expressions", {}).get("greetings", ["أهلاً بك!"]))
            response = f"{greeting}\n\n{company_info}"
            
            # إضافة سؤال استمرارية في نهاية الرد
            conclusion = random.choice(data.get("human_expressions", {}).get("conclusions", ["هل لديك أي استفسار آخر؟"]))
            response += f"\n\n{conclusion}"
            
            return response, True
        
        # يمكن إضافة المزيد من الأنماط هنا للتعامل مع استفسارات أخرى
        
        # لم يتم العثور على تطابق
        return "", False
        
    except Exception as e:
        logger.error(f"خطأ في معالجة الاستجابة المحلية: {e}")
        return "", False


def match_keyword(message: str, keywords: List[str]) -> bool:
    """
    تحقق مما إذا كانت أي من الكلمات المفتاحية موجودة في الرسالة
    
    :param message: الرسالة المراد فحصها
    :param keywords: قائمة الكلمات المفتاحية
    :return: True إذا تم العثور على تطابق
    """
    return any(keyword in message.lower() for keyword in keywords)


if __name__ == "__main__":
    # اختبار الوظائف
    test_queries = [
        "معلومات عن الشركة",
        "عايز أعرف معلومات عن المجمع",
        "مين رئيس المجمع؟",
        "ما هي مشاريع الشركة؟",
        "فين مقر الشركة؟"
    ]
    
    for query in test_queries:
        response, found = handle_local_response(query)
        if found:
            print(f"السؤال: {query}")
            print(f"الرد: {response[:100]}...\n")
        else:
            print(f"لم يتم العثور على إجابة محلية لـ: {query}\n")