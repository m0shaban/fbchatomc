"""
خادم ويب لشات بوت مجمع عمال مصر للتكامل مع Facebook API
يعمل كـ webhook للتعامل مع رسائل الماسنجر وتعليقات الفيسبوك
"""

import os
import json
import hmac
import hashlib
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify

from bot import ChatBot
from facebook_comments import FacebookCommentsHandler
from config import (
    FACEBOOK_SETTINGS, SERVER_SETTINGS, BOT_SETTINGS, 
    setup_log_directory, setup_conversations_directory, setup_logging
)

# إنشاء المجلدات اللازمة
setup_log_directory()
setup_conversations_directory()
setup_logging()

# إعداد التسجيل
logger = logging.getLogger(__name__)

# إنشاء كائن الشات بوت
chatbot = ChatBot()

# إنشاء كائن معالج تعليقات الفيسبوك
comments_handler = FacebookCommentsHandler(chatbot)

# إنشاء تطبيق Flask
app = Flask(__name__)

def verify_fb_signature(request_data, signature):
    """
    التحقق من توقيع الطلب الوارد من فيسبوك
    
    :param request_data: البيانات الواردة في جسم الطلب
    :param signature: التوقيع المرفق في الطلب
    :return: True إذا كان التوقيع صحيحًا
    """
    if not FACEBOOK_SETTINGS.get("APP_SECRET"):
        logger.warning("تحذير: لم يتم تكوين APP_SECRET. تخطي التحقق من التوقيع.")
        return True
    
    try:
        expected_signature = "sha1=" + hmac.new(
            FACEBOOK_SETTINGS["APP_SECRET"].encode('utf-8'),
            request_data,
            hashlib.sha1
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"خطأ في التحقق من توقيع Facebook: {e}")
        return False

def send_messenger_response(recipient_id, message_text):
    """
    إرسال رد إلى مستخدم الماسنجر
    
    :param recipient_id: معرف المستخدم المستلم
    :param message_text: نص الرسالة
    :return: True إذا تم الإرسال بنجاح
    """
    if not FACEBOOK_SETTINGS.get("PAGE_TOKEN"):
        logger.error("خطأ: لم يتم تكوين PAGE_TOKEN. لا يمكن إرسال الرد.")
        return False
    
    try:
        response_data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        response = requests.post(
            f"https://graph.facebook.com/v18.0/me/messages?access_token={FACEBOOK_SETTINGS['PAGE_TOKEN']}",
            json=response_data
        )
        
        if response.status_code == 200:
            logger.info(f"تم إرسال الرد إلى مستخدم الماسنجر: {recipient_id}")
            return True
        else:
            logger.error(f"فشل إرسال الرد إلى Facebook: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إرسال الرد إلى Facebook: {e}")
        return False

def send_comment_reply(comment_id, message_text):
    """
    إرسال رد على تعليق فيسبوك
    
    :param comment_id: معرف التعليق
    :param message_text: نص الرد
    :return: True إذا تم الإرسال بنجاح
    """
    if not FACEBOOK_SETTINGS.get("PAGE_TOKEN"):
        logger.error("خطأ: لم يتم تكوين PAGE_TOKEN. لا يمكن إرسال الرد.")
        return False
    
    try:
        response = requests.post(
            f"https://graph.facebook.com/v18.0/{comment_id}/comments",
            params={"access_token": FACEBOOK_SETTINGS["PAGE_TOKEN"]},
            data={"message": message_text}
        )
        
        if response.status_code == 200:
            logger.info(f"تم إرسال الرد على التعليق: {comment_id}")
            return True
        else:
            logger.error(f"فشل إرسال الرد على التعليق: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إرسال الرد على التعليق: {e}")
        return False

def save_conversation(user_id, message, response, source):
    """
    حفظ المحادثة في ملف JSON
    
    :param user_id: معرف المستخدم
    :param message: رسالة المستخدم
    :param response: رد الشات بوت
    :param source: مصدر المحادثة (messenger أو facebook_comment)
    """
    if not BOT_SETTINGS.get("SAVE_CONVERSATIONS"):
        return
    
    try:
        # إنشاء اسم ملف فريد باستخدام معرف المستخدم والتاريخ
        filename = f"{BOT_SETTINGS['CONVERSATIONS_DIR']}/{source}_{user_id}_{datetime.now().strftime('%Y%m%d')}.json"
        
        # التحقق من وجود الملف وقراءة محتوياته إذا كان موجودًا
        conversation_data = []
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    conversation_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"ملف المحادثة {filename} غير صالح. سيتم إنشاؤه من جديد.")
        
        # إضافة الرسالة والرد إلى المحادثة
        timestamp = datetime.now().isoformat()
        conversation_data.append({
            "timestamp": timestamp,
            "user_id": user_id,
            "message": message,
            "response": response,
            "source": source
        })
        
        # حفظ المحادثة في الملف
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=4)
            
        logger.debug(f"تم حفظ المحادثة في ملف: {filename}")
        
    except Exception as e:
        logger.error(f"خطأ في حفظ المحادثة: {e}")

@app.route("/", methods=["GET"])
def home():
    """
    الصفحة الرئيسية للتأكد من أن الخادم يعمل
    """
    return "شات بوت مجمع عمال مصر - الخادم يعمل"

@app.route(SERVER_SETTINGS.get("WEBHOOK_ROUTE", "/webhook"), methods=["GET", "POST"])
def webhook():
    """
    معالجة طلبات Webhook من Facebook
    """
    # التحقق من الصلاحية للـ GET request (مطلوب للتسجيل الأولي للـ webhook)
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        
        if verify_token == FACEBOOK_SETTINGS.get("VERIFY_TOKEN"):
            challenge = request.args.get("hub.challenge")
            logger.info("تم التحقق من Webhook بنجاح")
            return challenge
        else:
            logger.warning(f"فشل في التحقق من Webhook. رمز التحقق غير صحيح: {verify_token}")
            return "رمز التحقق غير صحيح", 403
    
    # معالجة طلبات POST (الأحداث الواردة)
    elif request.method == "POST":
        # التحقق من توقيع فيسبوك
        signature = request.headers.get("X-Hub-Signature", "")
        
        if not verify_fb_signature(request.data, signature):
            logger.warning("توقيع غير صالح للطلب")
            return "توقيع غير صالح", 403
        
        # تحليل البيانات الواردة
        try:
            data = request.json
            logger.debug(f"تم استلام طلب Webhook: {json.dumps(data)}")
            
            # التحقق من نوع الحدث
            if data.get("object") == "page":
                for entry in data.get("entry", []):
                    # معالجة رسائل الماسنجر
                    if "messaging" in entry:
                        for messaging_event in entry.get("messaging", []):
                            if "message" in messaging_event:
                                sender_id = messaging_event["sender"]["id"]
                                message_text = messaging_event.get("message", {}).get("text", "")
                                
                                logger.info(f"تم استلام رسالة ماسنجر من {sender_id}: {message_text[:50]}...")
                                
                                # توليد رد باستخدام الشات بوت
                                chatbot.set_conversation_source("messenger")
                                response = chatbot.generate_messenger_response(message_text)
                                
                                # إرسال الرد
                                send_messenger_response(sender_id, response)
                                
                                # حفظ المحادثة
                                save_conversation(sender_id, message_text, response, "messenger")
                    
                    # معالجة تعليقات المنشورات
                    if "changes" in entry:
                        for change in entry.get("changes", []):
                            if change.get("field") == "feed" and "comment" in change.get("value", {}):
                                comment_data = change["value"]
                                comment_id = comment_data.get("comment_id")
                                comment_text = comment_data.get("message", "")
                                commenter_id = comment_data.get("from", {}).get("id")
                                
                                # التحقق مما إذا كان يجب الرد على التعليق
                                if comments_handler.should_respond_to_comment(comment_text):
                                    logger.info(f"تم استلام تعليق فيسبوك من {commenter_id}: {comment_text[:50]}...")
                                    
                                    # توليد رد على التعليق
                                    response = comments_handler.generate_comment_response(comment_text)
                                    
                                    # إرسال الرد إذا كان هناك رد
                                    if response:
                                        send_comment_reply(comment_id, response)
                                        
                                        # حفظ المحادثة
                                        save_conversation(commenter_id, comment_text, response, "facebook_comment")
                                else:
                                    logger.info(f"تجاهل تعليق من {commenter_id}: {comment_text[:50]}...")
                
                return "EVENT_RECEIVED"
            else:
                logger.warning(f"نوع كائن غير مدعوم: {data.get('object')}")
                return "نوع كائن غير مدعوم", 400
                
        except Exception as e:
            logger.error(f"خطأ في معالجة طلب Webhook: {e}")
            return "خطأ في المعالجة", 500

# تشغيل التطبيق
if __name__ == "__main__":
    # طباعة معلومات حول الخادم
    logger.info(f"بدء تشغيل خادم الويب على {SERVER_SETTINGS['HOST']}:{SERVER_SETTINGS['PORT']}")
    logger.info(f"مسار Webhook: {SERVER_SETTINGS.get('WEBHOOK_ROUTE', '/webhook')}")
    
    if FACEBOOK_SETTINGS.get("PAGE_TOKEN"):
        logger.info("تم تكوين إعدادات فيسبوك بنجاح")
    else:
        logger.warning("تحذير: إعدادات فيسبوك غير مكتملة. قد لا يعمل التكامل مع فيسبوك بشكل صحيح.")
    
    # تشغيل الخادم
    app.run(
        host=SERVER_SETTINGS.get("HOST", "0.0.0.0"),
        port=SERVER_SETTINGS.get("PORT", 5000),
        debug=SERVER_SETTINGS.get("DEBUG", False)
    )