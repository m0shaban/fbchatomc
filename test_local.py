#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
برنامج لاختبار الشات بوت محلياً قبل نشره على الفيسبوك ماسنجر
هذا الملف يساعد في اختبار "محمد سلامة" بوت في بيئة محلية عبر واجهة سطر الأوامر
"""
import os
import sys
import time
import json
import random
import platform
import subprocess
from datetime import datetime
from bot import ChatBot
from config import BOT_SETTINGS, APP_SETTINGS, setup_log_directory, setup_conversations_directory

def clear_screen():
    """مسح الشاشة بطريقة متوافقة مع نظام التشغيل"""
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def print_header():
    """طباعة رأس الصفحة للترحيب بالمستخدم"""
    header = """
============================================================
                    مجمع عمال مصر
               اختبار شات بوت محمد سلامة
============================================================

أهلاً بك في اختبار شات بوت محمد سلامة!
يمكنك التحدث مع البوت وسيرد عليك. اكتب 'خروج' للخروج أو 'حفظ' لحفظ المحادثة.
"""
    print(header)

def print_response(message, delay=0.01):
    """طباعة رد الشات بوت مع تأثير الكتابة الحية"""
    print("\n🤵 محمد: ")
    for char in message:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()  # سطر جديد بعد الانتهاء من الرسالة

def setup_terminal_encoding():
    """إعداد ترميز الطرفية لدعم اللغة العربية"""
    if platform.system() == "Windows":
        try:
            # محاولة ضبط ترميز النافذة الطرفية في ويندوز
            subprocess.run(["chcp", "65001"], shell=True, check=False)
            os.system("chcp 65001 > nul")
        except Exception:
            print("تعذّر ضبط ترميز النافذة الطرفية، قد تظهر الأحرف العربية بشكل غير صحيح.")
    else:
        # تأكد من ضبط متغيرات البيئة في لينكس/ماك
        os.environ['PYTHONIOENCODING'] = 'utf-8'

def save_conversation(bot, user_id, filename=None):
    """حفظ المحادثة في ملف"""
    # التأكد من وجود مجلد المحادثات
    if not os.path.exists(BOT_SETTINGS.get("CONVERSATIONS_DIR", "conversations")):
        os.makedirs(BOT_SETTINGS.get("CONVERSATIONS_DIR", "conversations"))
    
    # إنشاء اسم ملف فريد إذا لم يتم تمريره
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(BOT_SETTINGS.get("CONVERSATIONS_DIR", "conversations"), f"local_chat_{timestamp}.json")
    
    # حفظ المحادثة باستخدام دالة الشات بوت
    success = bot.save_conversation_history(filename)
    
    if success:
        print(f"\nتم حفظ المحادثة في الملف: {filename}")
    else:
        print("\nحدث خطأ أثناء حفظ المحادثة.")
    
    return success

def main():
    """الدالة الرئيسية للتفاعل مع الشات بوت"""
    # إعداد ترميز الطرفية
    setup_terminal_encoding()
    
    # إعداد بيئة التشغيل
    setup_log_directory()
    setup_conversations_directory()
    
    # مسح الشاشة وطباعة رأس الصفحة
    clear_screen()
    print_header()
    
    # إنشاء معرف فريد للمستخدم المحلي
    user_id = f"local_user_{random.randint(1000, 9999)}"
    
    # تهيئة الشات بوت
    try:
        bot = ChatBot()
        
        # تشغيل حلقة المحادثة
        while True:
            # استقبال مدخلات المستخدم
            try:
                user_input = input("\n👤 أنت: ")
            except KeyboardInterrupt:
                print("\n\nتم إنهاء المحادثة بواسطة المستخدم.")
                save_conversation(bot, user_id)
                break
            except Exception as e:
                print(f"\nحدث خطأ في قراءة المدخلات: {e}")
                continue
            
            # التحقق من أوامر الخروج أو الحفظ
            if user_input.lower() in ["خروج", "exit", "quit", "q"]:
                print("\n🤵 محمد: شكراً لتواصلك معنا! نتطلع للتحدث معك مرة أخرى.")
                break
            elif user_input.lower() in ["حفظ", "save", "s"]:
                save_conversation(bot, user_id)
                continue
            elif not user_input.strip():
                continue
            
            # الحصول على رد من الشات بوت
            try:
                # تغيير استدعاء دالة توليد الرد لاستخدام الدالة الصحيحة وترتيب المعلمات الصحيح
                response = bot.generate_messenger_response(user_id, user_input)
                print_response(response)
            except Exception as e:
                print(f"\n🤵 محمد: عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى. ({e})")
        
        # حفظ المحادثة تلقائياً عند الخروج
        save_conversation(bot, user_id)
    
    except Exception as e:
        print(f"حدث خطأ غير متوقع: {e}")

if __name__ == "__main__":
    main()