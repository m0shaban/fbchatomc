"""
أدوات مساعدة لتكامل فيسبوك ماسنجر مع شات بوت مجمع عمال مصر
يوفر هذا الملف دوالاً مساعدة لإرسال رسائل ماسنجر وتنسيق القوائم والأزرار
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

from config import FACEBOOK_SETTINGS, APP_SETTINGS

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=APP_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

def send_messenger_message(recipient_id: str, message_data: Dict) -> Dict:
    """
    إرسال رسالة إلى مستخدم ماسنجر
    
    :param recipient_id: معرف المستخدم
    :param message_data: بيانات الرسالة
    :return: استجابة API
    """
    try:
        page_token = FACEBOOK_SETTINGS.get("PAGE_TOKEN")
        if not page_token:
            logger.error("لم يتم تعيين PAGE_TOKEN في إعدادات فيسبوك")
            return {"error": "PAGE_TOKEN not set"}
        
        url = f"https://graph.facebook.com/v16.0/me/messages?access_token={page_token}"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": message_data
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"تم إرسال رسالة بنجاح إلى المستخدم {recipient_id}")
            return response.json()
        else:
            logger.error(f"فشل إرسال الرسالة: {response.status_code} - {response.text}")
            return {"error": f"Failed to send message: {response.status_code} - {response.text}"}
    
    except Exception as e:
        logger.error(f"حدث خطأ أثناء إرسال رسالة: {e}")
        return {"error": str(e)}

def send_text_message(recipient_id: str, text: str) -> Dict:
    """
    إرسال رسالة نصية بسيطة إلى مستخدم ماسنجر
    
    :param recipient_id: معرف المستخدم
    :param text: نص الرسالة
    :return: استجابة API
    """
    message_data = {"text": text}
    return send_messenger_message(recipient_id, message_data)

def send_image_message(recipient_id: str, image_url: str) -> Dict:
    """
    إرسال رسالة تحتوي على صورة إلى مستخدم ماسنجر
    
    :param recipient_id: معرف المستخدم
    :param image_url: رابط الصورة
    :return: استجابة API
    """
    message_data = {
        "attachment": {
            "type": "image",
            "payload": {
                "url": image_url,
                "is_reusable": True
            }
        }
    }
    return send_messenger_message(recipient_id, message_data)

def send_button_template(recipient_id: str, text: str, buttons: List[Dict]) -> Dict:
    """
    إرسال قالب أزرار إلى مستخدم ماسنجر
    
    :param recipient_id: معرف المستخدم
    :param text: نص الرسالة
    :param buttons: قائمة بالأزرار
    :return: استجابة API
    """
    message_data = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "button",
                "text": text,
                "buttons": buttons
            }
        }
    }
    return send_messenger_message(recipient_id, message_data)

def send_generic_template(recipient_id: str, elements: List[Dict]) -> Dict:
    """
    إرسال قالب عام إلى مستخدم ماسنجر
    
    :param recipient_id: معرف المستخدم
    :param elements: قائمة بعناصر القالب
    :return: استجابة API
    """
    message_data = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": elements
            }
        }
    }
    return send_messenger_message(recipient_id, message_data)

def send_quick_replies(recipient_id: str, text: str, quick_replies: List[Dict]) -> Dict:
    """
    إرسال ردود سريعة إلى مستخدم ماسنجر
    
    :param recipient_id: معرف المستخدم
    :param text: نص الرسالة
    :param quick_replies: قائمة بالردود السريعة
    :return: استجابة API
    """
    message_data = {
        "text": text,
        "quick_replies": quick_replies
    }
    return send_messenger_message(recipient_id, message_data)

def create_postback_button(title: str, payload: str) -> Dict:
    """
    إنشاء زر بأمر خلفي
    
    :param title: عنوان الزر
    :param payload: البيانات المرسلة عند النقر
    :return: بيانات الزر
    """
    return {
        "type": "postback",
        "title": title,
        "payload": payload
    }

def create_url_button(title: str, url: str) -> Dict:
    """
    إنشاء زر رابط
    
    :param title: عنوان الزر
    :param url: عنوان URL
    :return: بيانات الزر
    """
    return {
        "type": "web_url",
        "title": title,
        "url": url
    }

def create_quick_reply(title: str, payload: str, image_url: Optional[str] = None) -> Dict:
    """
    إنشاء رد سريع
    
    :param title: عنوان الرد السريع
    :param payload: البيانات المرسلة عند النقر
    :param image_url: رابط صورة اختياري
    :return: بيانات الرد السريع
    """
    quick_reply = {
        "content_type": "text",
        "title": title,
        "payload": payload
    }
    
    if image_url:
        quick_reply["image_url"] = image_url
    
    return quick_reply

def extract_menu_quick_replies(menu_data: Dict, menu_type: str = "main", submenu_key: Optional[str] = None) -> List[Dict]:
    """
    استخراج ردود سريعة من بيانات القائمة
    
    :param menu_data: بيانات القائمة
    :param menu_type: نوع القائمة ("main" للقائمة الرئيسية أو "submenu" للقائمة الفرعية)
    :param submenu_key: مفتاح القائمة الفرعية المطلوبة (لقوائم الفرعية فقط)
    :return: قائمة بالردود السريعة
    """
    quick_replies = []
    
    if menu_type == "main":
        # القائمة الرئيسية
        for key, item in menu_data.items():
            # ضمان أننا لا نتجاوز الحد الأقصى للردود السريعة (11)
            if len(quick_replies) < 11:
                quick_replies.append(
                    create_quick_reply(item["title"], f"MENU_{key}")
                )
    
    elif menu_type == "submenu" and submenu_key and submenu_key in menu_data:
        # القائمة الفرعية
        menu_item = menu_data[submenu_key]
        
        if "submenu" in menu_item:
            for key, subitem in menu_item["submenu"].items():
                # ضمان أننا لا نتجاوز الحد الأقصى للردود السريعة (11)
                if len(quick_replies) < 10:  # نترك مساحة لزر العودة للقائمة الرئيسية
                    quick_replies.append(
                        create_quick_reply(subitem["title"], f"SUBMENU_{submenu_key}_{key}")
                    )
            
            # إضافة زر العودة للقائمة الرئيسية
            quick_replies.append(
                create_quick_reply("العودة للقائمة الرئيسية", "MENU_MAIN")
            )
    
    return quick_replies

def create_service_generic_template(menu_data: Dict) -> List[Dict]:
    """
    إنشاء قالب عام لخدمات المجمع
    
    :param menu_data: بيانات القائمة
    :return: قائمة بعناصر القالب العام
    """
    elements = []
    
    # أقصى عدد من العناصر هو 10
    count = 0
    for key, item in menu_data.items():
        if count >= 10:
            break
        
        element = {
            "title": item["title"],
            "subtitle": item["description"],
            "buttons": []
        }
        
        # إضافة زر للرابط إذا كان موجوداً
        if "link" in item:
            element["buttons"].append(create_url_button("فتح الرابط", item["link"]))
        
        # إضافة زر لفتح القائمة الفرعية إذا كانت موجودة
        if "submenu" in item:
            element["buttons"].append(create_postback_button("عرض التفاصيل", f"MENU_{key}"))
        
        elements.append(element)
        count += 1
    
    return elements

def extract_main_menu_buttons(menu_data: Dict) -> List[Dict]:
    """
    استخراج أزرار من القائمة الرئيسية
    
    :param menu_data: بيانات القائمة
    :return: قائمة بالأزرار
    """
    buttons = []
    
    # أقصى عدد من الأزرار هو 3
    count = 0
    for key, item in menu_data.items():
        if count >= 3:
            break
        
        if "submenu" in item:
            buttons.append(create_postback_button(item["title"], f"MENU_{key}"))
        else:
            buttons.append(create_url_button(item["title"], item["link"]))
        
        count += 1
    
    return buttons

def handle_postback(user_id: str, payload: str, menu_data: Dict) -> Dict:
    """
    معالجة الأوامر الخلفية من أزرار ماسنجر
    
    :param user_id: معرف المستخدم
    :param payload: البيانات المرسلة من الزر
    :param menu_data: بيانات القائمة
    :return: استجابة API
    """
    if payload == "MENU_MAIN":
        # العودة للقائمة الرئيسية
        quick_replies = extract_menu_quick_replies(menu_data, "main")
        return send_quick_replies(
            user_id,
            "الرجاء اختيار خدمة من القائمة الرئيسية:",
            quick_replies
        )
    
    if payload.startswith("MENU_"):
        menu_key = payload.replace("MENU_", "")
        if menu_key in menu_data:
            menu_item = menu_data[menu_key]
            
            if "submenu" in menu_item:
                # عرض القائمة الفرعية
                quick_replies = extract_menu_quick_replies(menu_data, "submenu", menu_key)
                return send_quick_replies(
                    user_id,
                    f"خدمات {menu_item['title']}:",
                    quick_replies
                )
            else:
                # عرض تفاصيل الخدمة
                service_text = f"📋 {menu_item['title']}\n\n{menu_item['description']}\n\n🔗 الرابط: {menu_item['link']}"
                
                buttons = [
                    create_url_button("فتح الرابط", menu_item["link"]),
                    create_postback_button("العودة للقائمة", "MENU_MAIN")
                ]
                
                return send_button_template(user_id, service_text, buttons)
    
    if payload.startswith("SUBMENU_"):
        parts = payload.split("_")
        if len(parts) >= 3:
            main_key = parts[1]
            sub_key = "_".join(parts[2:])
            
            if main_key in menu_data and "submenu" in menu_data[main_key] and sub_key in menu_data[main_key]["submenu"]:
                subitem = menu_data[main_key]["submenu"][sub_key]
                
                # عرض تفاصيل الخدمة الفرعية
                service_text = f"📋 {subitem['title']}\n\n{subitem['description']}\n\n🔗 الرابط: {subitem['link']}"
                
                buttons = [
                    create_url_button("فتح الرابط", subitem["link"]),
                    create_postback_button("العودة للقائمة", f"MENU_{main_key}")
                ]
                
                return send_button_template(user_id, service_text, buttons)
    
    # إذا لم يتم التعرف على الأمر الخلفي
    return send_text_message(user_id, "عذرًا، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.")

def process_messenger_text(text: str) -> Dict:
    """
    تحليل النص المرسل عبر ماسنجر لاستخراج النص والأزرار
    
    :param text: النص المرسل
    :return: قاموس يحتوي على النص والأزرار
    """
    # النمط: TEXT_CONTENT###BUTTONS:button1|value1,button2|value2
    result = {
        "text": text,
        "buttons": []
    }
    
    # البحث عن قسم الأزرار
    if "###BUTTONS:" in text:
        parts = text.split("###BUTTONS:")
        if len(parts) == 2:
            result["text"] = parts[0].strip()
            buttons_text = parts[1].strip()
            
            # استخراج الأزرار
            button_items = buttons_text.split(",")
            for button_item in button_items:
                if "|" in button_item:
                    button_parts = button_item.split("|")
                    if len(button_parts) == 2:
                        button_title = button_parts[0].strip()
                        button_value = button_parts[1].strip()
                        
                        if button_value.startswith("http"):
                            result["buttons"].append(create_url_button(button_title, button_value))
                        else:
                            result["buttons"].append(create_postback_button(button_title, button_value))
    
    return result

def send_formatted_message(recipient_id: str, text_content: str) -> Dict:
    """
    إرسال رسالة منسقة إلى مستخدم ماسنجر
    
    :param recipient_id: معرف المستخدم
    :param text_content: نص الرسالة
    :return: استجابة API
    """
    processed = process_messenger_text(text_content)
    
    if processed["buttons"]:
        # إذا كان هناك أزرار، استخدم قالب الأزرار
        return send_button_template(recipient_id, processed["text"], processed["buttons"])
    else:
        # إذا لم تكن هناك أزرار، استخدم رسالة نصية عادية
        return send_text_message(recipient_id, processed["text"])

def send_menu_message(recipient_id: str, menu_data: Dict, menu_type: str = "main", submenu_key: Optional[str] = None) -> Dict:
    """
    إرسال رسالة قائمة إلى مستخدم ماسنجر
    
    :param recipient_id: معرف المستخدم
    :param menu_data: بيانات القائمة
    :param menu_type: نوع القائمة ("main" للقائمة الرئيسية أو "submenu" للقائمة الفرعية)
    :param submenu_key: مفتاح القائمة الفرعية المطلوبة (لقوائم الفرعية فقط)
    :return: استجابة API
    """
    if menu_type == "main":
        # عرض القائمة الرئيسية كردود سريعة
        quick_replies = extract_menu_quick_replies(menu_data, "main")
        return send_quick_replies(
            recipient_id,
            "مرحباً بك في مجمع عمال مصر! يرجى اختيار الخدمة التي ترغب فيها:",
            quick_replies
        )
    
    elif menu_type == "submenu" and submenu_key and submenu_key in menu_data:
        # عرض القائمة الفرعية كردود سريعة
        menu_item = menu_data[submenu_key]
        
        if "submenu" in menu_item:
            quick_replies = extract_menu_quick_replies(menu_data, "submenu", submenu_key)
            return send_quick_replies(
                recipient_id,
                f"خدمات {menu_item['title']}:",
                quick_replies
            )
    
    # في حالة عدم وجود بيانات قائمة مناسبة
    generic_text = "مرحباً بك في مجمع عمال مصر! يمكنك طلب المساعدة أو الاستفسار عن خدماتنا في أي وقت."
    return send_text_message(recipient_id, generic_text)

def format_text_with_quick_replies(text: str, quick_replies_data: List[Dict]) -> Dict:
    """
    تنسيق نص مع ردود سريعة لإرساله عبر ماسنجر
    
    :param text: نص الرسالة
    :param quick_replies_data: بيانات الردود السريعة
    :return: بيانات الرسالة المنسقة
    """
    return {
        "text": text,
        "quick_replies": quick_replies_data
    }

# اختبار وظائف الملف عند تشغيله مباشرة
if __name__ == "__main__":
    # اختبار التنسيق
    test_text = "مرحباً بك في مجمع عمال مصر!###BUTTONS:زيارة موقعنا|https://www.omalmisr.com,التواصل معنا|CONTACT_US"
    processed = process_messenger_text(test_text)
    print(f"النص: {processed['text']}")
    print(f"الأزرار: {processed['buttons']}")
    
    # اختبار إنشاء ردود سريعة
    quick_replies = [
        create_quick_reply("وظائف", "JOBS"),
        create_quick_reply("استثمار", "INVESTMENT"),
        create_quick_reply("تدريب", "TRAINING")
    ]
    formatted = format_text_with_quick_replies("اختر من الخدمات التالية:", quick_replies)
    print(f"الرسالة المنسقة: {formatted}")