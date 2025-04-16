"""
أداة تشخيص إعدادات فيسبوك لشات بوت مجمع عمال مصر
تقوم بالتحقق من إعدادات فيسبوك وعرض معلومات عن الصفحة المتصلة
"""

import os
import requests
import json
from config import FACEBOOK_SETTINGS, load_dotenv

def test_page_token():
    """التحقق من صحة رمز وصول الصفحة"""
    page_token = FACEBOOK_SETTINGS["PAGE_TOKEN"]
    
    if not page_token:
        print("❌ خطأ: لم يتم تعيين رمز وصول الصفحة (FB_PAGE_TOKEN)")
        return False
    
    # الحصول على معلومات الصفحة باستخدام الرمز
    url = f"https://graph.facebook.com/me?access_token={page_token}"
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'error' in data:
            print(f"❌ خطأ في رمز وصول الصفحة: {data['error']['message']}")
            return False
        
        page_id = data.get('id')
        page_name = data.get('name')
        
        print(f"✅ تم التحقق من رمز وصول الصفحة بنجاح")
        print(f"• اسم الصفحة: {page_name}")
        print(f"• معرف الصفحة: {page_id}")
        
        # التحقق من تطابق معرف الصفحة مع الإعدادات
        configured_page_id = FACEBOOK_SETTINGS["PAGE_ID"]
        if configured_page_id and configured_page_id != page_id:
            print(f"⚠️ تحذير: معرف الصفحة المكون ({configured_page_id}) لا يتطابق مع معرف الصفحة الفعلي ({page_id})")
            print(f"    يرجى تحديث متغير البيئة FB_PAGE_ID ليكون {page_id}")
        
        return True
    
    except Exception as e:
        print(f"❌ خطأ أثناء الاتصال بـ Facebook API: {e}")
        return False

def test_app_secret():
    """التحقق من سر التطبيق"""
    app_secret = FACEBOOK_SETTINGS["APP_SECRET"]
    
    if not app_secret:
        print("❌ خطأ: لم يتم تعيين سر التطبيق (FB_APP_SECRET)")
        return False
    
    print("✅ تم تكوين سر التطبيق")
    return True

def test_verify_token():
    """التحقق من رمز التحقق"""
    verify_token = FACEBOOK_SETTINGS["VERIFY_TOKEN"]
    
    if not verify_token:
        print("❌ خطأ: لم يتم تعيين رمز التحقق (FB_VERIFY_TOKEN)")
        return False
    
    print(f"✅ تم تكوين رمز التحقق: {verify_token}")
    return True

def main():
    """الدالة الرئيسية للتشخيص"""
    print("\n=== تشخيص إعدادات فيسبوك لشات بوت مجمع عمال مصر ===\n")
    
    # التحقق من الإعدادات
    token_valid = test_page_token()
    app_secret_valid = test_app_secret()
    verify_token_valid = test_verify_token()
    
    # النتيجة النهائية
    print("\n=== النتيجة النهائية ===")
    if token_valid and app_secret_valid and verify_token_valid:
        print("✅ جميع إعدادات فيسبوك صحيحة")
    else:
        print("❌ هناك مشاكل في إعدادات فيسبوك. يرجى مراجعة التفاصيل أعلاه")
    
    # توصيات
    print("\n=== توصيات ===")
    if not token_valid:
        print("1. تأكد من إعادة إنشاء رمز وصول الصفحة من لوحة تحكم فيسبوك للمطورين")
    if not app_secret_valid:
        print("2. تأكد من نسخ سر التطبيق من إعدادات التطبيق في لوحة تحكم فيسبوك للمطورين")
    
    # للمساعدة في تحديث الإعدادات على Render
    print("\n=== تحديث الإعدادات على منصة Render ===")
    print("1. انتقل إلى لوحة تحكم Render")
    print("2. افتح الخدمة الخاصة بتطبيقك")
    print("3. انتقل إلى تبويب Environment")
    print("4. قم بتحديث المتغيرات التالية:")
    if not token_valid:
        print("   - FB_PAGE_TOKEN")
    if not app_secret_valid:
        print("   - FB_APP_SECRET")
    if not verify_token_valid:
        print("   - FB_VERIFY_TOKEN (رمز تحقق من اختيارك)")
    
    print("\n=== معلومات مفيدة ===")
    print("• رابط Webhook المستخدم في إعدادات فيسبوك يجب أن يكون:")
    print("  https://fbchatomc.onrender.com/webhook")
    
    print("\n==========================================\n")

if __name__ == "__main__":
    main()