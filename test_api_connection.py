"""
أداة سطر أوامر لاختبار الاتصال بـ DeepSeek API
استخدم هذا السكريبت للتحقق من صحة تكامل DeepSeek API
"""

import os
import sys
import json
import argparse
import logging
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import API_SETTINGS
from api import DeepSeekAPI
from api_alternatives import OpenAIClientAPI, get_api_client

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_deepseek_connection(api_key=None, implementation="default", query="مرحباً، قم بتقديم نفسك كمساعد رسمي لمجمع عمال مصر"):
    """
    اختبار الاتصال بـ DeepSeek API
    
    :param api_key: مفتاح API اختياري
    :param implementation: نوع التنفيذ ("default" أو "openai")
    :param query: الاستعلام المستخدم للاختبار
    :return: النتيجة كنص
    """
    print(f"جاري اختبار الاتصال بـ DeepSeek API باستخدام تنفيذ {implementation}...")
    
    try:
        # الحصول على مفتاح API من الوسائط أو متغيرات البيئة
        api_key = api_key or API_SETTINGS.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("خطأ: مفتاح API غير متوفر. يرجى توفيره كوسيط أو عبر ملف .env")
            return False
        
        # إنشاء كائن API المناسب
        if implementation.lower() == "openai":
            try:
                api_client = OpenAIClientAPI(api_key)
                print("تم تهيئة OpenAI Client للاتصال بـ DeepSeek API")
            except ImportError:
                print("تحذير: فشل في استخدام OpenAI Client، العودة إلى التنفيذ الافتراضي")
                api_client = DeepSeekAPI(api_key)
        else:
            api_client = DeepSeekAPI(api_key)
        
        print(f"إرسال طلب اختبار إلى DeepSeek API: '{query}'")
        
        # إرسال الطلب إلى API
        response = api_client.generate_response(query)
        
        # التحقق من الاستجابة
        if "error" in response:
            print(f"❌ فشل الاختبار: {response['error']}")
            if "error_type" in response:
                print(f"نوع الخطأ: {response['error_type']}")
            return False
        
        # استخراج النص من الاستجابة
        response_text = api_client.extract_response_text(response)
        
        if response_text:
            print(f"✅ نجح الاختبار!")
            print("\nالرد المستلم من DeepSeek API:")
            print("-" * 40)
            print(response_text)
            print("-" * 40)
            return True
        else:
            print("❌ فشل الاختبار: لم يتم استلام محتوى صالح")
            return False
    
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الاختبار: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description="أداة اختبار تكامل DeepSeek API")
    parser.add_argument("--api-key", help="مفتاح API لـ DeepSeek")
    parser.add_argument("--implementation", choices=["default", "openai"], default="default",
                        help="نوع التنفيذ المستخدم للاتصال")
    parser.add_argument("--query", default="مرحباً، كيف يمكنني الاستفسار عن الوظائف في مجمع عمال مصر؟",
                        help="الاستعلام المستخدم في الاختبار")
    
    args = parser.parse_args()
    
    # اختبار الاتصال
    success = test_deepseek_connection(args.api_key, args.implementation, args.query)
    
    # إعداد رمز الخروج
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()