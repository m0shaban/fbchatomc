"""
ملف للتعامل مع تعليقات صفحة الفيسبوك لمجمع عمال مصر
يقوم بتحليل التعليقات والرد عليها وفقاً للقواعد المحددة
"""

import re
import json
import logging
import random
from typing import Dict, List, Any, Optional
from config import BOT_SETTINGS, APP_SETTINGS
from bot import ChatBot

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=BOT_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

class FacebookCommentsHandler:
    """
    معالج تعليقات صفحة الفيسبوك لمجمع عمال مصر
    """
    
    def __init__(self, chatbot: Optional[ChatBot] = None):
        """
        تهيئة معالج التعليقات
        
        :param chatbot: كائن الشات بوت لاستخدامه في توليد الردود
        """
        self.chatbot = chatbot or ChatBot()
        
        # قائمة بالكلمات المفتاحية للتعليقات التي تتطلب رداً
        self.job_keywords = [
            "بحث عن عمل", "عايز شغل", "فرصة عمل", "وظائف", "وظيفة", "عمل", 
            "توظيف", "شغل", "مرتب", "راتب", "تقديم", "سيرة ذاتية"
        ]
        
        self.investor_keywords = [
            "مستثمر", "استثمار", "تفاصيل الاستثمار", "أريد التعاون", "مشروع", 
            "تمويل", "شراكة", "فرصة استثمارية", "أريد الاستثمار", "عائد"
        ]
        
        self.media_keywords = [
            "صحفي", "مقابلة", "لقاء", "تقرير", "نشر", "إعلام", "تصريح", "خبر", 
            "تلفزيون", "راديو", "إذاعة", "مجلة", "جريدة", "تغطية"
        ]
        
        # كلمات الإشادة التي لا تتطلب رداً
        self.praise_keywords = [
            "رائع", "ممتاز", "جميل", "برافو", "تحية", "شكراً", "شكرا", "أحسنتم",
            "ربنا يوفقكم", "بالتوفيق", "تسلم", "أدعم", "واو", "براڤو", "ممتاز"
        ]
        
        # الكلمات غير المرغوب فيها التي قد تظهر في التعليقات
        self.unwanted_keywords = [
            "سخيف", "فاشل", "سيء", "زبالة", "نصب", "محتال", "كذاب", "غش",
            "احتيال", "فشل", "لا أنصح", "ابتعدوا", "هراء", "خدعة"
        ]
        
        logger.info("تم تهيئة معالج تعليقات الفيسبوك بنجاح")
    
    def should_respond_to_comment(self, comment_text: str) -> bool:
        """
        تحديد ما إذا كان التعليق يستحق الرد
        
        :param comment_text: نص التعليق
        :return: True إذا كان التعليق يستحق الرد
        """
        comment_text = comment_text.lower()
        
        # تجاهل التعليقات القصيرة جداً (أقل من 3 أحرف)
        if len(comment_text.strip()) < 3:
            return False
        
        # تجاهل التعليقات التي تحتوي على كلمات غير مرغوب فيها
        for keyword in self.unwanted_keywords:
            if keyword in comment_text:
                logger.info(f"تجاهل تعليق يحتوي على كلمة غير مرغوب فيها: {keyword}")
                return False
        
        # تجاهل تعليقات الإشادة التي لا تحتوي على استفسار
        contains_praise = any(keyword in comment_text for keyword in self.praise_keywords)
        if contains_praise and len(comment_text.strip()) < 20:
            logger.info(f"تجاهل تعليق إشادة قصير: {comment_text[:20]}...")
            return False
        
        # التحقق من وجود كلمات مفتاحية تستحق الرد
        contains_job_keyword = any(keyword in comment_text for keyword in self.job_keywords)
        contains_investor_keyword = any(keyword in comment_text for keyword in self.investor_keywords)
        contains_media_keyword = any(keyword in comment_text for keyword in self.media_keywords)
        
        # التحقق من وجود علامة استفهام
        contains_question = "؟" in comment_text or "?" in comment_text
        
        # الرد على التعليقات التي تحتوي على كلمات مفتاحية أو علامة استفهام
        should_respond = contains_job_keyword or contains_investor_keyword or contains_media_keyword or contains_question
        
        if should_respond:
            logger.info(f"تقرر الرد على التعليق: {comment_text[:50]}...")
        else:
            logger.info(f"تقرر تجاهل التعليق: {comment_text[:50]}...")
        
        return should_respond
    
    def get_comment_category(self, comment_text: str) -> str:
        """
        تحديد فئة التعليق لتوجيه الرد المناسب
        
        :param comment_text: نص التعليق
        :return: فئة التعليق (وظائف، استثمار، إعلام، عام)
        """
        comment_text = comment_text.lower()
        
        # التحقق من وجود كلمات مفتاحية للوظائف
        if any(keyword in comment_text for keyword in self.job_keywords):
            logger.debug(f"تصنيف التعليق كاستفسار عن وظائف: {comment_text[:30]}...")
            return "باحث عن عمل"
        
        # التحقق من وجود كلمات مفتاحية للاستثمار
        if any(keyword in comment_text for keyword in self.investor_keywords):
            logger.debug(f"تصنيف التعليق كاستفسار عن الاستثمار: {comment_text[:30]}...")
            return "مستثمر"
        
        # التحقق من وجود كلمات مفتاحية للإعلام
        if any(keyword in comment_text for keyword in self.media_keywords):
            logger.debug(f"تصنيف التعليق كاستفسار إعلامي: {comment_text[:30]}...")
            return "صحفي"
        
        # إذا لم يتم تحديد فئة محددة
        logger.debug(f"لم يتم تحديد فئة محددة للتعليق: {comment_text[:30]}...")
        return ""
    
    def generate_comment_response(self, comment_text: str) -> str:
        """
        توليد رد مناسب على تعليق الفيسبوك
        
        :param comment_text: نص التعليق
        :return: الرد المناسب
        """
        if not self.should_respond_to_comment(comment_text):
            return ""
        
        # تحديد فئة التعليق
        comment_category = self.get_comment_category(comment_text)
        
        # استخدام الشات بوت لتوليد رد مناسب
        response = self.chatbot.generate_response(comment_text)
        
        # تأكد من أن الرد لا يشير إلى أن المجيب هو ذكاء اصطناعي
        response = self._sanitize_response(response)
        
        logger.info(f"تم توليد رد على تعليق الفيسبوك من فئة {comment_category}")
        
        return response
    
    def _sanitize_response(self, response: str) -> str:
        """
        تنقية الرد من أي إشارات إلى الذكاء الاصطناعي
        
        :param response: الرد الأصلي
        :return: الرد المنقى
        """
        # استبدال أي إشارات للذكاء الاصطناعي
        ai_terms = ["ذكاء اصطناعي", "روبوت", "بوت", "AI", "bot", "شات بوت", "chatbot"]
        sanitized_response = response
        
        for term in ai_terms:
            sanitized_response = re.sub(
                r'\b' + re.escape(term) + r'\b', 
                "المساعد الرسمي لمجمع عمال مصر", 
                sanitized_response, 
                flags=re.IGNORECASE
            )
        
        return sanitized_response
    
    def process_comments_batch(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        معالجة مجموعة من التعليقات وتوليد ردود لها
        
        :param comments: قائمة بالتعليقات كل منها كقاموس يحتوي على معرف التعليق ونصه
        :return: قائمة بالردود كل منها كقاموس يحتوي على معرف التعليق والرد المناسب
        """
        responses = []
        
        for comment in comments:
            comment_id = comment.get("id")
            comment_text = comment.get("text", "")
            
            if not comment_id or not comment_text:
                continue
            
            response_text = self.generate_comment_response(comment_text)
            
            if response_text:
                responses.append({
                    "comment_id": comment_id,
                    "response": response_text
                })
        
        logger.info(f"تمت معالجة {len(comments)} تعليق، وتوليد {len(responses)} رد")
        
        return responses
    
    def save_responses_to_file(self, responses: List[Dict[str, Any]], filename: str = "facebook_responses.json") -> bool:
        """
        حفظ الردود على التعليقات في ملف JSON
        
        :param responses: قائمة بالردود
        :param filename: اسم الملف
        :return: True إذا تم الحفظ بنجاح
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(responses, f, ensure_ascii=False, indent=4)
            logger.info(f"تم حفظ {len(responses)} رد على تعليقات الفيسبوك في الملف: {filename}")
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ ردود تعليقات الفيسبوك: {e}")
            return False


# نموذج لاستخدام معالج تعليقات الفيسبوك
def main():
    """
    دالة رئيسية لاختبار معالج تعليقات الفيسبوك
    """
    print("جاري تهيئة معالج تعليقات الفيسبوك لمجمع عمال مصر...")
    
    # إنشاء كائن من الشات بوت
    chatbot = ChatBot()
    
    # إنشاء كائن من معالج التعليقات
    comments_handler = FacebookCommentsHandler(chatbot)
    
    # أمثلة لتعليقات مختلفة للاختبار
    test_comments = [
        {"id": "comment1", "text": "كيف يمكنني التقديم للوظائف لديكم؟"},
        {"id": "comment2", "text": "أنا مستثمر وأرغب في معرفة المزيد عن فرص الاستثمار"},
        {"id": "comment3", "text": "رائع جداً ما تقدمونه"},
        {"id": "comment4", "text": "أريد عقد مقابلة صحفية مع مسؤولي المجمع"},
        {"id": "comment5", "text": "ما هي مجالات التدريب المتاحة؟"}
    ]
    
    # معالجة التعليقات
    responses = comments_handler.process_comments_batch(test_comments)
    
    print("\nالردود المولدة:")
    for response in responses:
        print(f"\nرد على تعليق #{response['comment_id']}:")
        print(f"{response['response']}")
    
    # حفظ الردود في ملف
    comments_handler.save_responses_to_file(responses)
    
    print("\nتم حفظ الردود في ملف facebook_responses.json")


if __name__ == "__main__":
    main()