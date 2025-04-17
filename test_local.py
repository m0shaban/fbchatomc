"""
واجهة محادثة محلية لاختبار شات بوت مجمع عمال مصر
تستخدم هذه الواجهة لاختبار وتقييم أداء الشات بوت قبل نشره على فيسبوك
"""

import os
import json
import random
import datetime
import subprocess
import logging
from typing import Dict, Any

from bot import ChatBot
from config import BOT_SETTINGS, APP_SETTINGS, init

# تهيئة الإعدادات
init()

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=APP_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

def save_conversation(conversation: Dict[str, Any]) -> None:
    """
    حفظ المحادثة في ملف JSON
    
    :param conversation: قاموس يحتوي على بيانات المحادثة
    """
    # إنشاء اسم الملف باستخدام الوقت الحالي
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"local_chat_{timestamp}.json"
    
    # التأكد من وجود مجلد المحادثات
    if not os.path.exists(BOT_SETTINGS["CONVERSATIONS_DIR"]):
        os.makedirs(BOT_SETTINGS["CONVERSATIONS_DIR"], exist_ok=True)
    
    # حفظ المحادثة في ملف JSON
    filepath = os.path.join(BOT_SETTINGS["CONVERSATIONS_DIR"], filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, ensure_ascii=False, indent=4)
        print(f"تم حفظ المحادثة في الملف: {filepath}")
    except Exception as e:
        logger.error(f"خطأ في حفظ المحادثة: {e}")
        print(f"خطأ في حفظ المحادثة: {e}")

def set_console_arabic() -> bool:
    """
    تعيين ترميز وحدة التحكم لدعم اللغة العربية
    
    :return: True إذا تم تعيين الترميز بنجاح
    """
    try:
        # محاولة تعيين ترميز وحدة التحكم إلى UTF-8
        if os.name == 'nt':  # نظام Windows
            # استخدام subprocess بدلاً من os.system لتحسين التوافق
            subprocess.run(['chcp', '65001'], check=True, shell=True)
        return True
    except Exception as e:
        logger.error(f"خطأ في تعيين ترميز وحدة التحكم: {e}")
        print(f"تحذير: قد يكون هناك مشكلة في عرض النص العربي بسبب خطأ في تعيين الترميز: {e}")
        return False

def print_welcome() -> None:
    """
    طباعة رسالة ترحيبية
    """
    print("\n" + "=" * 50)
    print("مرحباً بك في واجهة اختبار شات بوت مجمع عمال مصر!")
    print("هذه الواجهة تسمح لك باختبار الشات بوت قبل نشره على فيسبوك")
    print("اكتب 'خروج' للخروج من الواجهة، أو 'حفظ' لحفظ المحادثة")
    print("الأوامر المتاحة:")
    print("- القائمة: لعرض قائمة الخدمات المتاحة")
    print("- إحصائيات: لعرض إحصائيات المحادثة الحالية")
    print("- حفظ: لحفظ المحادثة الحالية")
    print("- خروج: للخروج من الواجهة")
    print("=" * 50 + "\n")

def test_connection() -> bool:
    """
    اختبار الاتصال بـ DeepSeek API
    
    :return: True إذا نجح الاتصال
    """
    try:
        print("اختبار الاتصال بـ DeepSeek API...")
        
        # إنشاء نسخة من الشات بوت
        bot = ChatBot()
        
        # اختبار الاتصال عن طريق إرسال رسالة اختبار
        test_message = "اختبار الاتصال"
        
        # تحضير المستخدم الوهمي للاختبار
        user_id = "test_connection"
        bot.conversation_state[user_id] = {"awaiting_name": False}
        
        # توجيه رسالة اختبار
        api_response = bot.api.generate_response(
            test_message, 
            context="هذا اختبار اتصال فقط، يرجى الرد بـ 'اختبار ناجح' فقط."
        )
        
        # التحقق من الاستجابة
        if api_response and "choices" in api_response:
            print("✅ تم الاتصال بـ DeepSeek API بنجاح!")
            logger.info("نجح اختبار الاتصال بـ DeepSeek API")
            return True
        else:
            print("❌ فشل الاتصال بـ DeepSeek API!")
            logger.error(f"فشل اختبار الاتصال بـ DeepSeek API: {api_response}")
            return False
            
    except Exception as e:
        print(f"❌ حدث خطأ أثناء اختبار الاتصال: {e}")
        logger.error(f"خطأ في اختبار الاتصال بـ DeepSeek API: {e}")
        return False

def main() -> None:
    """
    الدالة الرئيسية لواجهة المحادثة المحلية
    """
    # محاولة تعيين ترميز وحدة التحكم لدعم اللغة العربية
    set_console_arabic()
    
    # طباعة رسالة ترحيبية
    print_welcome()
    
    # اختبار الاتصال بـ DeepSeek API
    connection_success = test_connection()
    if not connection_success:
        print("\nتحذير: فشل الاتصال بـ DeepSeek API. سيستخدم الشات بوت آلية الاحتياط.")
    
    # تهيئة الشات بوت
    print("\nجاري تهيئة الشات بوت...")
    bot = ChatBot()
    print("تم تهيئة الشات بوت بنجاح.")
    
    # تعيين معرف المستخدم المحلي
    user_id = f"local_user_{random.randint(1000, 9999)}"
    
    # بدء المحادثة مع الشات بوت
    print("\nمحادثة جديدة بدأت. اكتب رسالتك أدناه:")
    
    # حلقة المحادثة
    while True:
        try:
            # الحصول على رسالة المستخدم
            user_message = input("\nأنت: ")
            
            # التحقق من أوامر الخروج
            if user_message.strip().lower() in ["exit", "quit", "خروج"]:
                print("\nإنهاء المحادثة...")
                break
            
            # التحقق من أمر الحفظ
            if user_message.strip().lower() in ["save", "حفظ"]:
                # حفظ المحادثة الحالية
                if hasattr(bot, 'conversation_history') and user_id in bot.conversation_history:
                    save_conversation(bot.conversation_history[user_id])
                else:
                    print("لا توجد محادثة لحفظها.")
                continue
            
            # التحقق من أمر الإحصائيات
            if user_message.strip().lower() in ["stats", "إحصائيات"]:
                # طباعة إحصائيات المحادثة
                if hasattr(bot, 'conversation_history') and user_id in bot.conversation_history:
                    messages_count = len(bot.conversation_history[user_id])
                    print(f"\nإحصائيات المحادثة:")
                    print(f"عدد الرسائل: {messages_count}")
                    print(f"معرف المستخدم: {user_id}")
                    if hasattr(bot, 'conversation_state') and user_id in bot.conversation_state:
                        if 'user_name' in bot.conversation_state[user_id]:
                            print(f"اسم المستخدم: {bot.conversation_state[user_id]['user_name']}")
                else:
                    print("لا توجد إحصائيات متاحة.")
                continue
            
            # الحصول على رد الشات بوت
            try:
                response = bot.generate_messenger_response(user_id, user_message)
                print(f"\nمحمد سلامة: {response}")
            except Exception as e:
                logger.error(f"خطأ أثناء توليد الرد: {e}")
                print(f"\nحدث خطأ: {e}")
                print("استخدام رد احتياطي...")
                print("\nمحمد سلامة: عذراً، حدث خطأ أثناء معالجة رسالتك. يمكنك التواصل معنا مباشرة على رقم الهاتف: 01100901200 وسنكون سعداء بمساعدتك.")
            
        except KeyboardInterrupt:
            print("\n\nتم إنهاء المحادثة بواسطة المستخدم.")
            break
        
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {e}")
            print(f"\nحدث خطأ غير متوقع: {e}")
    
    # حفظ المحادثة عند الخروج
    if hasattr(bot, 'conversation_history') and user_id in bot.conversation_history:
        if BOT_SETTINGS.get("SAVE_CONVERSATIONS", True):
            save_conversation(bot.conversation_history[user_id])
    
    print("\nتم إنهاء المحادثة. نشكرك على اختبار الشات بوت!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"خطأ في تشغيل الواجهة المحلية: {e}")
        print(f"خطأ في تشغيل الواجهة المحلية: {e}")