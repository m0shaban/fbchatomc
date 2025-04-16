#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
برنامج لاختبار الشات بوت محلياً قبل نشره على الفيسبوك ماسنجر
هذا الملف يساعد في اختبار "محمد سلامة" بوت في بيئة محلية عبر واجهة سطر الأوامر
"""

import os
import sys
import json
import time
import random
from bot import ChatBot
from config import BOT_SETTINGS, APP_SETTINGS, setup_log_directory, setup_conversations_directory

def clear_screen():
    """مسح الشاشة بما يتناسب مع نظام التشغيل"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """طباعة ترويسة البرنامج"""
    print("\n" + "=" * 60)
    print(" " * 20 + "مجمع عمال مصر")
    print(" " * 15 + "اختبار شات بوت محمد سلامة")
    print("=" * 60 + "\n")

def print_response(message, delay=0.01):
    """
    طباعة رسالة البوت بتأخير قليل لتقليد الكتابة
    
    :param message: الرسالة المراد طباعتها
    :param delay: التأخير بين كل حرف (بالثواني)
    """
    for char in message:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def save_conversation(conversation_history, filename="local_conversation.json"):
    """
    حفظ المحادثة في ملف JSON
    
    :param conversation_history: سجل المحادثة
    :param filename: اسم ملف الحفظ
    """
    conversations_dir = BOT_SETTINGS.get("CONVERSATIONS_DIR", "conversations")
    filepath = os.path.join(conversations_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=4)
        print(f"\n[تم حفظ المحادثة في {filepath}]")
    except Exception as e:
        print(f"\n[خطأ في حفظ المحادثة: {e}]")

def main():
    """الدالة الرئيسية للبرنامج"""
    # تأكد من وجود المجلدات اللازمة
    setup_log_directory()
    setup_conversations_directory()
    
    # إنشاء كائن الشات بوت
    chatbot = ChatBot()
    
    # معرف المستخدم الافتراضي للاختبار
    user_id = f"local_user_{random.randint(1000, 9999)}"
    
    # سجل المحادثة
    conversation_log = []
    
    # طباعة الترويسة
    clear_screen()
    print_header()
    
    print("أهلاً بك في اختبار شات بوت محمد سلامة!")
    print("يمكنك التحدث مع البوت وسيرد عليك. اكتب 'خروج' للخروج أو 'حفظ' لحفظ المحادثة.")
    print()
    
    # حلقة المحادثة
    while True:
        # الحصول على رسالة المستخدم
        user_message = input("\n👤 أنت: ")
        
        # التحقق من أوامر الخروج
        if user_message.lower() in ["خروج", "exit", "quit", "q"]:
            print("\nشكراً لاختبار الشات بوت! مع السلامة.")
            
            # سؤال المستخدم عن حفظ المحادثة
            save_option = input("\nهل تريد حفظ هذه المحادثة؟ (نعم/لا): ").strip()
            if save_option.lower() in ["نعم", "y", "yes"]:
                save_conversation(conversation_log)
            
            break
        
        # التحقق من أمر الحفظ
        if user_message.lower() in ["حفظ", "save", "s"]:
            save_conversation(conversation_log)
            continue
        
        # إضافة رسالة المستخدم إلى سجل المحادثة
        conversation_log.append({
            "role": "user",
            "message": user_message,
            "timestamp": time.time()
        })
        
        # الحصول على رد البوت
        bot_response = chatbot.generate_response(user_message, user_id)
        
        # طباعة رد البوت
        print("\n🤵 محمد: ")
        print_response(bot_response)
        
        # إضافة رد البوت إلى سجل المحادثة
        conversation_log.append({
            "role": "bot",
            "message": bot_response,
            "timestamp": time.time()
        })

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nتم إنهاء البرنامج بواسطة المستخدم. مع السلامة!")
    except Exception as e:
        print(f"\n\nحدث خطأ غير متوقع: {e}")