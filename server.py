"""
خادم الويب لشات بوت مجمع عمال مصر
يوفر واجهة برمجة تطبيقات (API) للتفاعل مع الشات بوت
ويتعامل مع أحداث Webhook لماسنجر فيسبوك
"""

import os
import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, Response
from bot import ChatBot
from messenger_utils import (
    send_text_message, 
    send_button_template, 
    send_quick_replies,
    handle_postback,
    extract_menu_quick_replies,
    send_menu_message
)
from config import (
    SERVER_SETTINGS, 
    FACEBOOK_SETTINGS, 
    BOT_SETTINGS, 
    APP_SETTINGS
)

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=BOT_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

# إنشاء تطبيق Flask
app = Flask(__name__)

# إنشاء كائن الشات بوت
chatbot = ChatBot()

@app.route('/', methods=['GET'])
def index():
    """الصفحة الرئيسية للخادم"""
    return jsonify({
        "name": "شات بوت مجمع عمال مصر - محمد سلامة",
        "version": APP_SETTINGS.get("VERSION", "1.0.0"),
        "status": "متصل",
        "environment": APP_SETTINGS.get("ENVIRONMENT", "development")
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    واجهة برمجة التطبيقات للدردشة مع الشات بوت
    تستخدم لاختبار الشات بوت عبر واجهة مخصصة
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "البيانات المدخلة فارغة"}), 400
        
        user_id = data.get('user_id', 'api_user')
        message = data.get('message')
        
        if not message:
            return jsonify({"error": "الرسالة فارغة"}), 400
        
        response = chatbot.generate_response(message, user_id)
        
        return jsonify({
            "user_id": user_id,
            "response": response
        })
    
    except Exception as e:
        logger.error(f"خطأ في معالجة طلب API Chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """الحصول على حالة الشات بوت"""
    try:
        # اختبار اتصال الشات بوت بـ DeepSeek API
        api_status = chatbot.api.validate_connection()
        
        status_data = {
            "status": "متصل" if api_status.get("status") == "متصل" else "غير متصل",
            "api_status": api_status,
            "bot_name": chatbot.bot_name,
            "version": APP_SETTINGS.get("VERSION", "1.0.0"),
            "environment": APP_SETTINGS.get("ENVIRONMENT", "development")
        }
        
        return jsonify(status_data)
    
    except Exception as e:
        logger.error(f"خطأ في الحصول على حالة الشات بوت: {e}")
        return jsonify({"error": str(e), "status": "خطأ"}), 500

@app.route(SERVER_SETTINGS.get("WEBHOOK_ROUTE", "/webhook"), methods=['GET'])
def webhook_verify():
    """
    التحقق من صحة webhook لفيسبوك
    يتم استدعاؤها عند تسجيل webhook في إعدادات تطبيق فيسبوك
    """
    verify_token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if not verify_token or not challenge:
        return "رمز التحقق أو التحدي غير موجود", 400
    
    # التحقق من رمز التحقق
    if verify_token == FACEBOOK_SETTINGS.get("VERIFY_TOKEN"):
        logger.info("تم التحقق من webhook بنجاح")
        return challenge
    else:
        logger.warning(f"فشل التحقق من webhook: رمز تحقق غير صالح: {verify_token}")
        return "رمز تحقق غير صالح", 403

def verify_facebook_signature(request_data: bytes, signature_header: str) -> bool:
    """
    التحقق من توقيع فيسبوك للتأكد من أن الطلب قادم من فيسبوك
    
    :param request_data: بيانات الطلب
    :param signature_header: رأس التوقيع
    :return: True إذا كان التوقيع صحيحًا
    """
    app_secret = FACEBOOK_SETTINGS.get("APP_SECRET")
    
    if not app_secret:
        logger.warning("لم يتم تعيين APP_SECRET، تخطي التحقق من التوقيع")
        return True
    
    if not signature_header:
        logger.warning("رأس X-Hub-Signature-256 مفقود")
        return False
    
    # التحقق من صحة التوقيع
    signature_parts = signature_header.split('=')
    if len(signature_parts) != 2:
        logger.warning(f"تنسيق رأس X-Hub-Signature-256 غير صالح: {signature_header}")
        return False
    
    algorithm, signature = signature_parts
    if algorithm != 'sha256':
        logger.warning(f"خوارزمية توقيع غير معتمدة: {algorithm}")
        return False
    
    # حساب HMAC والتحقق من التوقيع
    expected_signature = hmac.new(
        app_secret.encode('utf-8'),
        msg=request_data,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        logger.warning("توقيع فيسبوك غير صالح")
        return False
    
    return True

@app.route(SERVER_SETTINGS.get("WEBHOOK_ROUTE", "/webhook"), methods=['POST'])
def webhook_handler():
    """
    معالجة أحداث webhook من فيسبوك (رسائل، أوامر خلفية، إلخ)
    """
    # الحصول على بيانات الطلب
    request_data = request.get_data()
    
    # التحقق من توقيع فيسبوك إذا كانت بيئة الإنتاج
    if APP_SETTINGS.get("ENVIRONMENT") == "production":
        signature_header = request.headers.get('X-Hub-Signature-256')
        if not verify_facebook_signature(request_data, signature_header):
            logger.warning("تم رفض طلب webhook، توقيع غير صالح")
            return "توقيع غير صالح", 403
    
    try:
        data = request.get_json()
        
        if data.get('object') != 'page':
            logger.warning(f"نوع كائن غير مدعوم: {data.get('object')}")
            return "نوع كائن غير مدعوم", 400
        
        entries = data.get('entry', [])
        
        for entry in entries:
            for event in entry.get('messaging', []):
                process_messenger_event(event)
        
        return "OK"
    
    except Exception as e:
        logger.error(f"خطأ في معالجة webhook: {e}")
        return "خطأ في المعالجة", 500

def process_messenger_event(event: Dict[str, Any]) -> None:
    """
    معالجة حدث ماسنجر (رسالة، أمر خلفي، إلخ)
    
    :param event: بيانات الحدث من فيسبوك
    """
    sender_id = event.get('sender', {}).get('id')
    
    if not sender_id:
        logger.warning("معرف المرسل غير موجود في الحدث")
        return
    
    # معالجة الرسائل النصية
    if 'message' in event:
        handle_messenger_message(sender_id, event['message'])
    
    # معالجة الأوامر الخلفية (الأزرار)
    elif 'postback' in event:
        handle_messenger_postback(sender_id, event['postback'])
    
    # معالجة قراءة الرسائل
    elif 'read' in event:
        # تسجيل وقت قراءة الرسالة
        logger.debug(f"تم قراءة الرسائل من قبل المستخدم {sender_id} في الوقت {event['read'].get('watermark')}")
    
    # معالجة كتابة الرسائل
    elif 'typing' in event:
        typing_status = "بدأ" if event['typing'].get('status') == 1 else "توقف"
        logger.debug(f"المستخدم {sender_id} {typing_status} الكتابة")

def handle_messenger_message(sender_id: str, message_data: Dict[str, Any]) -> None:
    """
    معالجة رسالة ماسنجر
    
    :param sender_id: معرف المرسل
    :param message_data: بيانات الرسالة
    """
    # تجاهل الإصدار المتكرر لنفس الرسالة
    if message_data.get('is_echo', False):
        return
    
    # التعامل مع الردود السريعة
    if 'quick_reply' in message_data:
        quick_reply_payload = message_data['quick_reply'].get('payload')
        if quick_reply_payload:
            logger.info(f"تم استلام رد سريع من المستخدم {sender_id}: {quick_reply_payload}")
            handle_messenger_quick_reply(sender_id, quick_reply_payload)
            return
    
    # التعامل مع النص
    if 'text' in message_data:
        message_text = message_data['text']
        logger.info(f"تم استلام رسالة نصية من المستخدم {sender_id}: {message_text[:50]}...")
        
        # التحقق من طلبات القائمة
        if message_text.lower() in ["القائمة", "menu", "خدمات", "services", "قائمة"]:
            send_menu_message(sender_id, chatbot.main_menu, "main")
            return
        
        # توليد رد باستخدام الشات بوت
        try:
            response = chatbot.generate_messenger_response(sender_id, message_text)
            
            # التحقق من وجود طلب قائمة في الرد
            if "###MENU:" in response:
                menu_parts = response.split("###MENU:")
                text = menu_parts[0].strip()
                menu_type = menu_parts[1].strip()
                
                # إرسال الرد النصي أولاً
                if text:
                    send_text_message(sender_id, text)
                
                # إرسال القائمة
                if menu_type == "MAIN":
                    send_menu_message(sender_id, chatbot.main_menu, "main")
                elif menu_type.startswith("SUB:"):
                    submenu_key = menu_type.split("SUB:")[1]
                    send_menu_message(sender_id, chatbot.main_menu, "submenu", submenu_key)
            
            # التحقق من وجود أزرار في الرد
            elif "###BUTTONS:" in response:
                from messenger_utils import process_messenger_text, send_formatted_message
                send_formatted_message(sender_id, response)
            
            # إرسال رد نصي عادي
            else:
                # حد أقصى لعدد الأحرف في رسالة ماسنجر فيسبوك (استناداً على حدود منصة فيسبوك)
                MAX_MESSAGE_LENGTH = 2000
                
                # تقسيم الرسائل الطويلة فقط عند تجاوز حد الأحرف المسموح به
                if len(response) > MAX_MESSAGE_LENGTH:
                    logger.info(f"الرسالة تجاوزت الحد الأقصى ({len(response)} حرف)، سيتم تقسيمها")
                    
                    # تقسيم ذكي للرسالة على أساس الفقرات والجمل لتجنب قطع الجمل
                    message_parts = []
                    current_part = ""
                    
                    # تقسيم الرسالة إلى فقرات أولاً
                    paragraphs = response.split('\n\n')
                    
                    for paragraph in paragraphs:
                        # إذا كانت الفقرة نفسها أكبر من الحد الأقصى، نقسمها إلى جمل
                        if len(paragraph) > MAX_MESSAGE_LENGTH:
                            sentences = paragraph.replace('\n', ' ').split('. ')
                            for sentence in sentences:
                                if len(current_part + sentence + '. ') <= MAX_MESSAGE_LENGTH:
                                    current_part += sentence + '. '
                                else:
                                    # إذا كانت الجملة الواحدة أكبر من الحد الأقصى، نقسمها
                                    if len(sentence) > MAX_MESSAGE_LENGTH:
                                        sentence_chunks = [sentence[i:i+MAX_MESSAGE_LENGTH] 
                                                          for i in range(0, len(sentence), MAX_MESSAGE_LENGTH)]
                                        
                                        # إضافة الجزء الحالي إذا لم يكن فارغاً
                                        if current_part:
                                            message_parts.append(current_part)
                                            current_part = ""
                                        
                                        # إضافة أجزاء الجملة الطويلة
                                        message_parts.extend(sentence_chunks[:-1])
                                        current_part = sentence_chunks[-1] + '. '
                                    else:
                                        # حفظ الجزء الحالي وبدء جزء جديد
                                        message_parts.append(current_part)
                                        current_part = sentence + '. '
                        else:
                            # التحقق مما إذا كانت إضافة الفقرة ستتجاوز الحد الأقصى
                            if len(current_part + '\n\n' + paragraph) <= MAX_MESSAGE_LENGTH:
                                if current_part:
                                    current_part += '\n\n'
                                current_part += paragraph
                            else:
                                # حفظ الجزء الحالي وبدء جزء جديد
                                message_parts.append(current_part)
                                current_part = paragraph
                    
                    # إضافة الجزء الأخير إذا لم يكن فارغاً
                    if current_part:
                        message_parts.append(current_part)
                    
                    # إرسال كل جزء كرسالة منفصلة
                    logger.info(f"تم تقسيم الرسالة إلى {len(message_parts)} أجزاء")
                    for part in message_parts:
                        send_text_message(sender_id, part)
                else:
                    # إرسال الرسالة كاملة إذا كانت ضمن الحد المسموح
                    send_text_message(sender_id, response)
        
        except Exception as e:
            logger.error(f"خطأ في توليد الرد للمستخدم {sender_id}: {e}")
            
            # استخدام رسالة خطأ احتياطية
            error_message = """
عذراً، حدث خطأ أثناء معالجة رسالتك.

يمكنك التواصل معنا مباشرة على الأرقام التالية:
📞 01100901200 (المقر الرئيسي)
📞 01103642612 (العاشر من رمضان)
أو زيارة موقعنا الإلكتروني: https://www.omalmisr.com/
            """
            
            send_text_message(sender_id, error_message)
    
    # التعامل مع المرفقات (صور، فيديو، ملفات، إلخ)
    elif 'attachments' in message_data:
        attachments = message_data['attachments']
        attachment_types = [attachment.get('type') for attachment in attachments]
        
        logger.info(f"تم استلام مرفقات من المستخدم {sender_id}: {', '.join(attachment_types)}")
        
        # إرسال رد على المرفقات
        send_text_message(
            sender_id,
            "شكراً لإرسال هذه المرفقات. هل يمكنني مساعدتك في شيء آخر؟"
        )

def handle_messenger_postback(sender_id: str, postback_data: Dict[str, Any]) -> None:
    """
    معالجة أمر خلفي من ماسنجر (الأزرار)
    
    :param sender_id: معرف المرسل
    :param postback_data: بيانات الأمر الخلفي
    """
    payload = postback_data.get('payload')
    
    if not payload:
        logger.warning(f"أمر خلفي بدون payload من المستخدم {sender_id}")
        return
    
    logger.info(f"تم استلام أمر خلفي من المستخدم {sender_id}: {payload}")
    
    # معالجة الأمر الخلفي مع بيانات القائمة الرئيسية
    handle_postback(sender_id, payload, chatbot.main_menu)

def handle_messenger_quick_reply(sender_id: str, payload: str) -> None:
    """
    معالجة رد سريع من ماسنجر
    
    :param sender_id: معرف المرسل
    :param payload: البيانات المرسلة مع الرد السريع
    """
    logger.info(f"معالجة رد سريع من المستخدم {sender_id}: {payload}")
    
    # معالجة الأمر الخلفي مع بيانات القائمة الرئيسية
    handle_postback(sender_id, payload, chatbot.main_menu)

if __name__ == '__main__':
    # تشغيل الخادم
    host = SERVER_SETTINGS.get("HOST", "0.0.0.0")
    port = SERVER_SETTINGS.get("PORT", 5000)
    debug = SERVER_SETTINGS.get("DEBUG", False)
    
    logger.info(f"بدء تشغيل الخادم على {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)