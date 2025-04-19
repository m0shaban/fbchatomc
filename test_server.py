"""
خادم اختبار لشات بوت مجمع عمال مصر
يوفر واجهة محلية لاختبار الشات بوت قبل نشره على فيسبوك ماسنجر
"""

import os
import json
import logging
from flask import Flask, request, jsonify, Response, send_from_directory
from bot import ChatBot
from config import SERVER_SETTINGS, APP_SETTINGS, BOT_SETTINGS
import traceback

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS.get("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=BOT_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger("test_server")

# إنشاء تطبيق Flask
app = Flask(__name__)

# إنشاء كائن الشات بوت
chatbot = ChatBot()

@app.route('/')
def index():
    """توجيه المستخدم إلى واجهة الاختبار"""
    return send_from_directory('.', 'test_interface.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    واجهة برمجة التطبيقات للدردشة مع الشات بوت للاختبار المحلي
    يدعم خيارات إضافية مثل استخدام البيانات المحلية وتخصيص الرد
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "البيانات المدخلة فارغة"}), 400
        
        # استخراج البيانات من الطلب
        message = data.get('message')
        use_local_data = data.get('use_local_data', True)
        personalize_response = data.get('personalize_response', True)
        user_category = data.get('user_category', '')
        user_id = data.get('user_id', 'test_user')
        
        if not message:
            return jsonify({"error": "الرسالة فارغة"}), 400
        
        logger.info(f"طلب جديد من {user_id}: {message[:50]}...")
        logger.debug(f"استخدام البيانات المحلية: {use_local_data}, تخصيص الرد: {personalize_response}, فئة المستخدم: {user_category}")
        
        # توليد رد باستخدام الشات بوت
        try:
            # تكييف سلوك الشات بوت استناداً إلى الإعدادات
            original_settings = {
                "use_local_data": chatbot.use_local_data,
                "personalize_response": chatbot.personalize_response,
            }
            
            # تطبيق الإعدادات المؤقتة
            chatbot.use_local_data = use_local_data
            chatbot.personalize_response = personalize_response
            
            # تعيين فئة المستخدم إذا تم تحديدها
            user_details = chatbot.get_user_details(user_id)
            if user_category:
                user_details["category"] = user_category
                chatbot.update_user_details(user_id, user_details)
            
            # توليد الرد
            response = chatbot.generate_response(message, user_id)
            
            # استعادة الإعدادات الأصلية
            chatbot.use_local_data = original_settings["use_local_data"]
            chatbot.personalize_response = original_settings["personalize_response"]
            
            return jsonify({
                "response": response,
                "user_id": user_id
            })
            
        except Exception as e:
            logger.error(f"خطأ في توليد الرد: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "حدث خطأ في توليد الرد",
                "details": str(e)
            }), 500
    
    except Exception as e:
        logger.error(f"خطأ في معالجة طلب API Chat: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """الحصول على حالة الشات بوت"""
    try:
        # اختبار اتصال الشات بوت بـ API
        api_status = chatbot.api.validate_connection()
        
        status_data = {
            "status": "متصل" if api_status.get("status") == "متصل" else "غير متصل",
            "api_status": api_status,
            "bot_name": chatbot.bot_name,
            "version": APP_SETTINGS.get("VERSION", "1.0.0"),
            "environment": "testing",
            "use_local_data": chatbot.use_local_data,
            "personalize_response": chatbot.personalize_response
        }
        
        return jsonify(status_data)
    
    except Exception as e:
        logger.error(f"خطأ في الحصول على حالة الشات بوت: {e}")
        return jsonify({"error": str(e), "status": "خطأ"}), 500

@app.route('/api/user_categories', methods=['GET'])
def get_user_categories():
    """الحصول على قائمة بفئات المستخدمين المتاحة"""
    categories = [
        {"id": "باحث عن عمل", "name": "باحث عن عمل"},
        {"id": "مستثمر", "name": "مستثمر"},
        {"id": "رجل أعمال", "name": "رجل أعمال"},
        {"id": "صحفي", "name": "صحفي"},
        {"id": "جهة تعليمية", "name": "جهة تعليمية"},
        {"id": "شركة", "name": "شركة"}
    ]
    
    return jsonify(categories)

if __name__ == '__main__':
    # تشغيل خادم الاختبار
    host = "127.0.0.1"  # localhost فقط للأمان
    port = 5001  # استخدام منفذ مختلف عن الخادم الرئيسي
    
    print(f"""
=======================================================
    اختبار شات بوت مجمع عمال مصر
=======================================================
    
    الخادم يعمل على: http://{host}:{port}
    
    افتح المتصفح على العنوان أعلاه لبدء الاختبار
    
    اضغط CTRL+C لإيقاف الخادم
=======================================================
""")
    
    app.run(host=host, port=port, debug=True)