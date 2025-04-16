"""
Flask server لتشغيل واجهة webhook لصفحة الفيسبوك
يقوم باستقبال الطلبات من فيسبوك ومعالجتها
"""

import os
import json
import hmac
import hashlib
import logging
import datetime
from typing import Dict, Any, Union

from flask import Flask, request, jsonify
from flask_cors import CORS

from config import SERVER_SETTINGS, FACEBOOK_SETTINGS, setup_logging
from bot import ChatBot

# إعداد السجلات
setup_logging()
logger = logging.getLogger(__name__)

# إنشاء تطبيق Flask
app = Flask(__name__)
CORS(app)  # السماح بطلبات CORS

# إنشاء كائن الشات بوت
chatbot = ChatBot()

@app.route('/', methods=['GET'])
def index():
    """صفحة الترحيب الرئيسية"""
    return jsonify({
        "status": "online",
        "app": "fbchatomc",
        "version": "1.0.0",
        "description": "شات بوت مجمع عمال مصر"
    })

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    معالجة طلبات webhook من الفيسبوك
    GET: للتحقق من صحة webhook
    POST: لاستقبال الأحداث (رسائل، تعليقات، إلخ)
    """
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        return process_webhook_event(request)
    else:
        return jsonify({"error": "طريقة غير مدعومة"}), 405

def verify_webhook(req):
    """
    التحقق من صحة webhook عند تسجيله مع فيسبوك
    """
    # استخراج المعلمات من الطلب
    mode = req.args.get('hub.mode')
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')
    
    # التحقق من صحة الطلب
    if mode and token:
        if mode == 'subscribe' and token == FACEBOOK_SETTINGS['VERIFY_TOKEN']:
            logger.info("تم التحقق من webhook بنجاح!")
            return challenge
        else:
            logger.warning(f"فشل التحقق من webhook! المفتاح غير صحيح: {token}")
            return jsonify({"error": "تحقق غير صحيح"}), 403
    
    return jsonify({"error": "معلمات مفقودة"}), 400

def verify_request_signature(req):
    """
    التحقق من توقيع طلب webhook للتأكد من أنه من فيسبوك
    """
    # إذا لم يكن هناك مفتاح سري للتطبيق، فلا يمكن التحقق
    if not FACEBOOK_SETTINGS['APP_SECRET']:
        return True
    
    # الحصول على التوقيع من الرأس
    signature = req.headers.get('X-Hub-Signature-256')
    if not signature:
        logger.warning("لم يتم العثور على توقيع في الطلب!")
        return False
    
    # حساب التوقيع المتوقع
    signature_parts = signature.split('=')
    if len(signature_parts) != 2 or signature_parts[0] != 'sha256':
        logger.warning(f"تنسيق توقيع غير صالح: {signature}")
        return False
    
    # حساب HMAC لمحتوى الطلب
    request_data = req.get_data()
    expected_signature = hmac.new(
        bytes(FACEBOOK_SETTINGS['APP_SECRET'], 'utf-8'),
        msg=request_data,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # مقارنة التوقيعات
    if not hmac.compare_digest(signature_parts[1], expected_signature):
        logger.warning("توقيع غير متطابق!")
        return False
    
    return True

def process_webhook_event(req):
    """
    معالجة الأحداث الواردة من webhook الفيسبوك
    """
    # التحقق من توقيع الطلب
    if not verify_request_signature(req):
        return jsonify({"error": "توقيع غير صالح"}), 403
    
    # استخراج الجسم من الطلب
    data = req.json
    
    try:
        # التحقق من أن الحدث من صفحة
        if data["object"] == "page":
            # معالجة كل مدخل
            for entry in data["entry"]:
                # التحقق من صفحة المصدر
                page_id = entry.get("id")
                if FACEBOOK_SETTINGS['PAGE_ID'] and page_id != FACEBOOK_SETTINGS['PAGE_ID']:
                    logger.warning(f"تم استلام حدث من صفحة غير معروفة: {page_id}")
                    continue
                
                if "messaging" in entry:
                    # حدث ماسنجر
                    process_messenger_events(entry.get("messaging", []))
                elif "changes" in entry:
                    # حدث تغيير (مثل تعليق جديد)
                    process_change_events(entry.get("changes", []))
                else:
                    logger.warning(f"نوع حدث غير معروف: {entry}")
            
            return jsonify({"status": "success"}), 200
        else:
            # ليس حدث صفحة
            logger.warning(f"كائن غير معروف: {data['object']}")
            return jsonify({"error": "غير مدعوم"}), 400
    except Exception as e:
        logger.error(f"خطأ في معالجة حدث webhook: {e}")
        return jsonify({"error": str(e)}), 500

def process_messenger_events(events):
    """
    معالجة أحداث ماسنجر (رسائل المستخدمين)
    """
    for event in events:
        sender_id = event.get("sender", {}).get("id")
        recipient_id = event.get("recipient", {}).get("id")
        timestamp = event.get("timestamp")
        
        # التحقق من أن الحدث موجه إلى صفحتنا
        if recipient_id != FACEBOOK_SETTINGS['PAGE_ID']:
            logger.warning(f"تم استلام رسالة لصفحة مختلفة: {recipient_id}")
            continue
        
        # التحقق من نوع الحدث
        if "message" in event:
            message = event["message"]
            message_text = message.get("text", "")
            
            logger.info(f"تم استلام رسالة من {sender_id}: {message_text[:50]}...")
            
            # توليد رد
            response = chatbot.generate_messenger_response(message_text, sender_id)
            
            # إرسال الرد إلى المستخدم
            send_facebook_message(sender_id, response)
        elif "postback" in event:
            # معالجة postback من قائمة
            postback = event["postback"]
            payload = postback.get("payload", "")
            
            logger.info(f"تم استلام postback من {sender_id}: {payload}")
            
            # توليد رد بناءً على payload
            response = chatbot.process_menu_request(payload)
            
            # إرسال الرد إلى المستخدم
            send_facebook_message(sender_id, response or "عذراً، لم أتمكن من معالجة طلبك.")

def process_change_events(changes):
    """
    معالجة أحداث التغيير (مثل التعليقات الجديدة)
    """
    for change in changes:
        # التحقق من نوع التغيير
        if change["field"] == "feed":
            value = change["value"]
            
            # معالجة التعليق الجديد
            if "comment_id" in value and "message" in value:
                comment_id = value["comment_id"]
                message = value["message"]
                post_id = value.get("post_id", "")
                
                logger.info(f"تم استلام تعليق جديد: {comment_id} على المنشور: {post_id}")
                
                # توليد رد على التعليق
                response = chatbot.generate_comment_response(message)
                
                # الرد على التعليق
                if response:
                    reply_to_facebook_comment(comment_id, response)

def send_facebook_message(recipient_id, message_text):
    """
    إرسال رسالة إلى المستخدم عبر ماسنجر الفيسبوك
    """
    import requests
    
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={FACEBOOK_SETTINGS['PAGE_TOKEN']}"
    
    try:
        # تحضير محتوى الرسالة
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        # إرسال الطلب إلى API الفيسبوك
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            logger.info(f"تم إرسال الرسالة بنجاح إلى {recipient_id}")
            return True
        else:
            logger.error(f"فشل إرسال الرسالة: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"خطأ في إرسال الرسالة إلى {recipient_id}: {e}")
        return False

def reply_to_facebook_comment(comment_id, message):
    """
    الرد على تعليق على الفيسبوك
    """
    import requests
    
    url = f"https://graph.facebook.com/{comment_id}/comments?access_token={FACEBOOK_SETTINGS['PAGE_TOKEN']}"
    
    try:
        # إرسال الطلب إلى API الفيسبوك
        response = requests.post(url, data={"message": message})
        
        if response.status_code == 200:
            logger.info(f"تم الرد على التعليق {comment_id} بنجاح")
            
            # حفظ المعلومات للتحليلات
            chatbot.save_facebook_response(comment_id, message)
            return True
        else:
            logger.error(f"فشل الرد على التعليق: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"خطأ في الرد على التعليق {comment_id}: {e}")
        return False

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """
    واجهة API للدردشة لاختبار الشات بوت محلياً
    """
    try:
        data = request.json
        
        # التحقق من وجود الرسالة
        if not data or "message" not in data:
            return jsonify({"error": "يجب توفير رسالة"}), 400
        
        message = data["message"]
        user_id = data.get("user_id", "local_user")
        
        # توليد رد
        response = chatbot.generate_messenger_response(message, user_id)
        
        # حفظ المحادثة
        conversation_id = f"local_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        chatbot.save_conversation(user_id, message, response, conversation_id=conversation_id)
        
        return jsonify({
            "response": response,
            "user_id": user_id,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"خطأ في معالجة طلب API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    التحقق من صحة التطبيق
    """
    return jsonify({
        "status": "healthy",
        "time": datetime.datetime.now().isoformat(),
        "api": chatbot.api.get_status()
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", SERVER_SETTINGS["PORT"]))
    app.run(
        host=SERVER_SETTINGS["HOST"],
        port=port,
        debug=SERVER_SETTINGS["DEBUG"]
    )