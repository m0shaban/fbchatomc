"""
ملف إعدادات تطبيق شات بوت مجمع عمال مصر
يحتوي على الإعدادات والتهيئة اللازمة لتشغيل الشات بوت
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# إعدادات الـ API
API_SETTINGS = {
    "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
    "DEEPSEEK_API_URL": os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "DEFAULT_MODEL": os.getenv("DEFAULT_MODEL", "deepseek-chat"),
    "MAX_TOKENS": int(os.getenv("MAX_TOKENS", "1000")),
    "TEMPERATURE": float(os.getenv("TEMPERATURE", "0.7")),
    "USE_FALLBACK_API": os.getenv("USE_FALLBACK_API", "True").lower() in ("true", "1", "yes"),
    "FALLBACK_PROVIDER": os.getenv("FALLBACK_PROVIDER", "openai")
}

# إعدادات الشات بوت
BOT_SETTINGS = {
    "DATA_FILE": os.getenv("DATA_FILE", "data.json"),
    "LOG_FILE": os.getenv("LOG_FILE", "logs/chatbot.log"),
    "SIMILARITY_THRESHOLD": float(os.getenv("SIMILARITY_THRESHOLD", "0.4")),
    "PERSONALIZE_RESPONSE": os.getenv("PERSONALIZE_RESPONSE", "True").lower() in ("true", "1", "yes"),
    "SAVE_CONVERSATIONS": os.getenv("SAVE_CONVERSATIONS", "True").lower() in ("true", "1", "yes"),
    "CONVERSATIONS_DIR": os.getenv("CONVERSATIONS_DIR", "conversations"),
    "AUTO_LEARN": os.getenv("AUTO_LEARN", "False").lower() in ("true", "1", "yes"),
    "RESPONSE_TIMEOUT": int(os.getenv("RESPONSE_TIMEOUT", "30"))
}

# إعدادات فيسبوك
FACEBOOK_SETTINGS = {
    "PAGE_TOKEN": os.getenv("FB_PAGE_TOKEN"),
    "VERIFY_TOKEN": os.getenv("FB_VERIFY_TOKEN", "omc_verify_token"),
    "APP_SECRET": os.getenv("FB_APP_SECRET"),
    "PAGE_ID": os.getenv("FB_PAGE_ID"),
    "IGNORE_PRAISE_COMMENTS": os.getenv("FB_IGNORE_PRAISE", "True").lower() in ("true", "1", "yes"),
    "COMMENT_LENGTH_THRESHOLD": int(os.getenv("FB_COMMENT_LENGTH", "3")),
    "AUTO_COMMENT": os.getenv("FB_AUTO_COMMENT", "True").lower() in ("true", "1", "yes"),
    "BATCH_SIZE": int(os.getenv("FB_BATCH_SIZE", "10")),
    "REFRESH_INTERVAL": int(os.getenv("FB_REFRESH_INTERVAL", "300"))
}

# إعدادات الويب سيرفر
SERVER_SETTINGS = {
    "HOST": os.getenv("SERVER_HOST", "0.0.0.0"),
    "PORT": int(os.getenv("SERVER_PORT", "5000")),
    "DEBUG": os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "yes"),
    "WEBHOOK_ROUTE": os.getenv("WEBHOOK_ROUTE", "/webhook"),
    "ADMIN_ROUTE": os.getenv("ADMIN_ROUTE", "/admin"),
    "ADMIN_USERNAME": os.getenv("ADMIN_USERNAME", "admin"),
    "ADMIN_PASSWORD": os.getenv("ADMIN_PASSWORD", "omc_admin"),
    "ENABLE_CORS": os.getenv("ENABLE_CORS", "True").lower() in ("true", "1", "yes")
}

# إعدادات تحليلات البيانات
ANALYTICS_SETTINGS = {
    "TRACK_METRICS": os.getenv("TRACK_METRICS", "True").lower() in ("true", "1", "yes"),
    "METRICS_FILE": os.getenv("METRICS_FILE", "analytics/metrics.json"),
    "DASHBOARD_ENABLED": os.getenv("DASHBOARD_ENABLED", "True").lower() in ("true", "1", "yes"),
    "EXPORT_FORMATS": os.getenv("EXPORT_FORMATS", "json,csv").split(",")
}

# إعدادات التطبيق العامة
APP_SETTINGS = {
    "DEBUG_MODE": os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "yes"),
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
    "VERSION": "1.2.0",
    "MAINTENANCE_MODE": os.getenv("MAINTENANCE_MODE", "False").lower() in ("true", "1", "yes")
}

# إنشاء مجلد للسجلات إذا لم يكن موجوداً
def setup_log_directory():
    """إنشاء مجلد للسجلات إذا لم يكن موجوداً"""
    log_dir = os.path.dirname(BOT_SETTINGS["LOG_FILE"])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        print(f"تم إنشاء مجلد السجلات: {log_dir}")

# إنشاء مجلد للمحادثات إذا لم يكن موجوداً
def setup_conversations_directory():
    """إنشاء مجلد لحفظ المحادثات إذا لم يكن موجوداً"""
    if BOT_SETTINGS["SAVE_CONVERSATIONS"] and BOT_SETTINGS["CONVERSATIONS_DIR"]:
        os.makedirs(BOT_SETTINGS["CONVERSATIONS_DIR"], exist_ok=True)
        print(f"تم إنشاء مجلد المحادثات: {BOT_SETTINGS['CONVERSATIONS_DIR']}")

# إنشاء مجلد للتحليلات إذا لم يكن موجوداً
def setup_analytics_directory():
    """إنشاء مجلد لحفظ التحليلات إذا لم يكن موجوداً"""
    if ANALYTICS_SETTINGS["TRACK_METRICS"]:
        analytics_dir = os.path.dirname(ANALYTICS_SETTINGS["METRICS_FILE"])
        if analytics_dir and not os.path.exists(analytics_dir):
            os.makedirs(analytics_dir, exist_ok=True)
            print(f"تم إنشاء مجلد التحليلات: {analytics_dir}")

# تهيئة ملف .env إذا لم يكن موجوداً
def create_env_file():
    """إنشاء ملف .env إذا لم يكن موجوداً مع القيم الافتراضية"""
    if not os.path.exists(".env"):
        with open(".env", "w", encoding="utf-8") as f:
            f.write("""# إعدادات API
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
# OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=deepseek-chat
MAX_TOKENS=1000
TEMPERATURE=0.7
USE_FALLBACK_API=True
FALLBACK_PROVIDER=openai

# إعدادات الشات بوت
DATA_FILE=data.json
LOG_FILE=logs/chatbot.log
SIMILARITY_THRESHOLD=0.4
PERSONALIZE_RESPONSE=True
SAVE_CONVERSATIONS=True
CONVERSATIONS_DIR=conversations
AUTO_LEARN=False
RESPONSE_TIMEOUT=30

# إعدادات فيسبوك
FB_PAGE_TOKEN=your_page_access_token_here
FB_VERIFY_TOKEN=omc_verify_token
FB_APP_SECRET=your_app_secret_here
FB_PAGE_ID=your_page_id_here
FB_IGNORE_PRAISE=True
FB_COMMENT_LENGTH=3
FB_AUTO_COMMENT=True
FB_BATCH_SIZE=10
FB_REFRESH_INTERVAL=300

# إعدادات الويب سيرفر
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
WEBHOOK_ROUTE=/webhook
ADMIN_ROUTE=/admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=omc_admin
ENABLE_CORS=True

# إعدادات تحليلات البيانات
TRACK_METRICS=True
METRICS_FILE=analytics/metrics.json
DASHBOARD_ENABLED=True
EXPORT_FORMATS=json,csv

# إعدادات التطبيق
DEBUG_MODE=False
LOG_LEVEL=INFO
ENVIRONMENT=development
MAINTENANCE_MODE=False
""")
        print("تم إنشاء ملف .env بنجاح. يرجى تعديل البيانات وإعادة تشغيل التطبيق.")

# فحص وجود المفاتيح الضرورية
def validate_config():
    """التحقق من وجود الإعدادات الضرورية"""
    errors = []
    
    if not API_SETTINGS["DEEPSEEK_API_KEY"]:
        errors.append("لم يتم تعيين مفتاح API لـ DeepSeek. يرجى تعيينه في ملف .env")
    
    if not os.path.exists(BOT_SETTINGS["DATA_FILE"]):
        errors.append(f"ملف البيانات غير موجود: {BOT_SETTINGS['DATA_FILE']}")
    
    # التحقق من صحة ملف البيانات
    try:
        with open(BOT_SETTINGS["DATA_FILE"], "r", encoding="utf-8") as f:
            json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        errors.append(f"ملف البيانات غير صالح أو غير موجود: {BOT_SETTINGS['DATA_FILE']}")
    
    if errors:
        for error in errors:
            print(f"خطأ: {error}")
        return False
    
    return True

# إعداد التسجيل
def setup_logging():
    """إعداد نظام التسجيل"""
    setup_log_directory()
    
    log_level = getattr(logging, APP_SETTINGS["LOG_LEVEL"])
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=BOT_SETTINGS["LOG_FILE"],
        filemode='a'
    )
    
    # إضافة معالج للطباعة على وحدة التحكم عند تفعيل وضع التصحيح
    if APP_SETTINGS["DEBUG_MODE"]:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        logging.getLogger().addHandler(console_handler)
    
    logging.info(f"تم بدء التسجيل بنجاح. المستوى: {APP_SETTINGS['LOG_LEVEL']}")

# تهيئة الإعدادات عند تشغيل هذا الملف مباشرة
def init():
    """تهيئة الإعدادات عند تشغيل الملف مباشرة"""
    # إنشاء ملف .env إذا لم يكن موجوداً
    create_env_file()
    
    # إعداد المجلدات
    setup_log_directory()
    setup_conversations_directory()
    setup_analytics_directory()
    
    # إعداد التسجيل
    setup_logging()
    
    # التحقق من الإعدادات
    if validate_config():
        print("تم التحقق من الإعدادات بنجاح.")
        print(f"وضع التشغيل: {APP_SETTINGS['ENVIRONMENT']}")
        print(f"إصدار التطبيق: {APP_SETTINGS['VERSION']}")
        if API_SETTINGS["DEEPSEEK_API_KEY"]:
            masked_key = API_SETTINGS["DEEPSEEK_API_KEY"][:4] + "*" * (len(API_SETTINGS["DEEPSEEK_API_KEY"]) - 8) + API_SETTINGS["DEEPSEEK_API_KEY"][-4:]
            print(f"مفتاح DeepSeek API: {masked_key}")
        
        # طباعة معلومات إضافية
        if FACEBOOK_SETTINGS["PAGE_TOKEN"]:
            print("تم تكوين إعدادات فيسبوك بنجاح.")
        else:
            print("تحذير: إعدادات فيسبوك غير مكتملة. يمكن استخدام وضع CLI فقط.")
        
        if APP_SETTINGS["MAINTENANCE_MODE"]:
            print("تحذير: التطبيق في وضع الصيانة!")
    else:
        print("يوجد خطأ في الإعدادات. يرجى مراجعة ملف .env")

# عند تشغيل هذا الملف مباشرة
if __name__ == "__main__":
    init()