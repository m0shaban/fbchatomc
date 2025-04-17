#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import re
from typing import Dict, Any, Optional, Tuple, List

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

def match_keywords(message: str, keywords: List[str]) -> bool:
    """
    التحقق مما إذا كانت أي من الكلمات المفتاحية موجودة في الرسالة
    
    :param message: الرسالة المراد فحصها
    :param keywords: قائمة الكلمات المفتاحية
    :return: True إذا تم العثور على تطابق
    """
    message = message.lower()
    for keyword in keywords:
        if keyword.lower() in message:
            return True
    return False

def search_faq(user_message: str, data: Dict) -> Tuple[Optional[str], float]:
    """
    البحث عن إجابة في قائمة الأسئلة الشائعة
    
    :param user_message: رسالة المستخدم
    :param data: بيانات المجمع
    :return: زوج من الإجابة ودرجة الثقة
    """
    prompts = data.get("prompts", [])
    best_match = None
    best_confidence = 0.0
    
    user_message = user_message.lower()
    
    for prompt in prompts:
        question = prompt.get("question", "").lower()
        answer = prompt.get("answer", "")
        
        # البحث عن كلمات متطابقة
        question_words = set(re.findall(r'\b\w+\b', question))
        message_words = set(re.findall(r'\b\w+\b', user_message))
        
        if not question_words:
            continue
        
        # حساب درجة التطابق
        common_words = question_words.intersection(message_words)
        
        if len(common_words) > 0:
            confidence = len(common_words) / len(question_words)
            
            # زيادة الثقة إذا كانت هناك تطابقات دقيقة
            if question in user_message:
                confidence += 0.3
            
            # تحديث أفضل تطابق
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = answer
    
    return best_match, best_confidence

def get_contact_info(data: Dict) -> str:
    """
    استخراج معلومات الاتصال بالمجمع
    
    :param data: بيانات المجمع
    :return: نص معلومات الاتصال
    """
    contact_info = data.get("contact_info", {})
    
    contact_text = "للتواصل معنا:\n"
    
    phone = contact_info.get("phone")
    if phone:
        contact_text += f"📞 هاتف: {phone}\n"
    
    whatsapp = contact_info.get("whatsapp", {}).get("main_office")
    if whatsapp:
        contact_text += f"📱 واتساب: {whatsapp}\n"
    
    email = contact_info.get("email")
    if email:
        contact_text += f"📧 بريد إلكتروني: {email}\n"
    
    website = contact_info.get("website")
    if website:
        contact_text += f"🌐 الموقع الإلكتروني: {website}\n"
    
    facebook = contact_info.get("social_media", {}).get("facebook")
    if facebook:
        contact_text += f"👍 فيسبوك: {facebook}\n"
    
    return contact_text

def get_company_info(data: Dict) -> str:
    """
    استخراج معلومات عامة عن مجمع عمال مصر
    
    :param data: بيانات المجمع
    :return: نص المعلومات
    """
    prompts = data.get("prompts", [])
    about_company = ""
    leadership = ""
    projects = ""
    
    # البحث عن المعلومات ذات الصلة
    for prompt in prompts:
        if prompt.get("id") == 1:  # ما هو مجمع عمال مصر؟
            about_company = prompt.get("answer", "")
        elif prompt.get("id") == 2:  # من يدير المجمع؟
            leadership = prompt.get("answer", "")
        elif prompt.get("id") == 3:  # ما هي أبرز مشروعات المجمع؟
            projects = prompt.get("answer", "")
    
    # تجميع المعلومات في رد شامل
    response = "معلومات عن مجمع عمال مصر:\n\n"
    
    if about_company:
        response += f"● نبذة عن المجمع:\n{about_company}\n\n"
    
    if leadership:
        response += f"● قيادة المجمع:\n{leadership}\n\n"
    
    if projects:
        response += f"● أبرز المشروعات:\n{projects}\n\n"
    
    # إضافة معلومات الاتصال
    response += get_contact_info(data)
    
    return response

def handle_local_response(user_message: str, data_file: str = None) -> Tuple[Optional[str], float]:
    """
    معالجة رسالة المستخدم محلياً بدون استخدام API
    
    :param user_message: رسالة المستخدم
    :param data_file: مسار ملف البيانات (اختياري)
    :return: زوج من الرد ودرجة الثقة
    """
    data_file = data_file or BOT_SETTINGS.get("DATA_FILE", "data.json")
    data = load_data_file(data_file)
    if not data:
        return None, 0.0
    
    user_message = user_message.lower()
    
    # طلب معلومات عن الشركة
    company_info_keywords = [
        "معلومات عن الشركة", "معلومات عن المجمع", "من هو مجمع عمال مصر",
        "ما هو مجمع عمال مصر", "عرفني بالمجمع", "نبذة عن المجمع", "نبذة عن الشركة"
    ]
    
    if match_keywords(user_message, company_info_keywords):
        return get_company_info(data), 0.9
    
    # طلب معلومات الاتصال
    contact_keywords = [
        "معلومات الاتصال", "اتصل بنا", "رقم الهاتف", "البريد الإلكتروني",
        "العنوان", "الموقع", "الواتساب", "التواصل", "فين المقر", "عنوان الشركة"
    ]
    
    if match_keywords(user_message, contact_keywords):
        return get_contact_info(data), 0.9
    
    # البحث في الأسئلة الشائعة
    faq_answer, confidence = search_faq(user_message, data)
    if faq_answer and confidence >= 0.6:
        # إضافة تعبير بشري في البداية
        human_expressions = data.get("human_expressions", {})
        greetings = human_expressions.get("greetings", ["أهلاً!"])
        explanations = human_expressions.get("explanations", ["إليك المعلومات المطلوبة:"])
        
        response = f"{random.choice(greetings)}\n\n{random.choice(explanations)}\n\n{faq_answer}"
        
        return response, confidence
    
    # التحقق من وجود ردود عامة للأسئلة الشائعة جدًا
    if "كيف حالك" in user_message or "ازيك" in user_message:
        return "أنا بخير، شكراً للسؤال! كيف يمكنني مساعدتك اليوم؟", 0.8
    
    if "شكرا" in user_message or "شكراً" in user_message:
        return "العفو! سعدت بخدمتك. هل هناك شيء آخر يمكنني مساعدتك به؟", 0.8
    
    # لم يتم العثور على رد محلي مناسب
    return None, 0.0

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
                if user_id in bot.conversation_history:
                    save_conversation(bot.conversation_history[user_id])
                else:
                    print("لا توجد محادثة لحفظها.")
                continue
            
            # التحقق من أمر الإحصائيات
            if user_message.strip().lower() in ["stats", "إحصائيات"]:
                # طباعة إحصائيات المحادثة
                if user_id in bot.conversation_history and "messages" in bot.conversation_history[user_id]:
                    messages_count = len(bot.conversation_history[user_id]["messages"])
                    print(f"\nإحصائيات المحادثة:")
                    print(f"عدد الرسائل: {messages_count}")
                    print(f"معرف المستخدم: {user_id}")
                    if "user_name" in bot.conversation_history[user_id]:
                        print(f"اسم المستخدم: {bot.conversation_history[user_id]['user_name']}")
                else:
                    print("لا توجد إحصائيات متاحة.")
                continue
            
            # التحقق من الردود المحلية
            local_response, confidence = handle_local_response(user_message)
            if local_response:
                print(f"\nمحمد سلامة: {local_response}")
                continue
            
            # الحصول على رد الشات بوت
            try:
                response = bot.generate_response(user_message, user_id)
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
    if BOT_SETTINGS.get("SAVE_CONVERSATIONS", True) and user_id in bot.conversation_history:
        save_conversation(bot.conversation_history[user_id])
    
    print("\nتم إنهاء المحادثة. نشكرك على اختبار الشات بوت!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"خطأ في تشغيل الواجهة المحلية: {e}")
        print(f"خطأ في تشغيل الواجهة المحلية: {e}")