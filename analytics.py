"""
أداة تحليل محادثات ومراقبة أداء الشات بوت
تستخدم لتحليل محادثات الماسنجر وتعليقات الفيسبوك لقياس أداء الشات بوت
"""

import os
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Tuple, Optional
import seaborn as sns
from wordcloud import WordCloud
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np
from collections import Counter
from config import BOT_SETTINGS, FACEBOOK_SETTINGS, setup_log_directory

# إعداد التسجيل
logger = logging.getLogger(__name__)

class ChatbotAnalytics:
    """
    محلل أداء الشات بوت لمجمع عمال مصر
    يوفر تحليلات ورؤى حول أداء الشات بوت ومحادثاته
    """
    
    def __init__(self, conversations_dir: str = None):
        """
        تهيئة محلل أداء الشات بوت
        
        :param conversations_dir: مسار مجلد المحادثات (اختياري)
        """
        self.conversations_dir = conversations_dir or BOT_SETTINGS.get("CONVERSATIONS_DIR", "conversations")
        self.analytics_dir = "analytics"
        
        # إنشاء مجلد التحليلات إذا لم يكن موجودًا
        os.makedirs(self.analytics_dir, exist_ok=True)
        
        # تهيئة البيانات
        self.messenger_conversations = []
        self.facebook_comments = []
        self.all_conversations = []
        
        # مقاييس الأداء
        self.total_messages = 0
        self.total_comments = 0
        self.avg_response_length = 0
        self.common_topics = {}
        self.topic_distribution = {}
        self.hourly_distribution = {}
        self.daily_distribution = {}
        self.user_categories = {}
        
        # لوحة معلومات اليوم
        self.today_stats = {
            "total_messages": 0,
            "total_comments": 0,
            "avg_response_time": 0,
            "common_topics": {},
            "user_categories": {}
        }
        
        logger.info("تم تهيئة محلل أداء الشات بوت")
    
    def load_conversations(self) -> bool:
        """
        تحميل جميع بيانات المحادثات من مجلد المحادثات
        
        :return: True إذا تم التحميل بنجاح
        """
        try:
            # التأكد من وجود المجلد
            if not os.path.exists(self.conversations_dir):
                logger.error(f"مجلد المحادثات غير موجود: {self.conversations_dir}")
                return False
            
            # إعادة تعيين البيانات
            self.messenger_conversations = []
            self.facebook_comments = []
            self.all_conversations = []
            
            # قراءة جميع ملفات المحادثات
            conversation_files = [f for f in os.listdir(self.conversations_dir) if f.endswith(".json")]
            
            if not conversation_files:
                logger.warning("لم يتم العثور على ملفات محادثات")
                return False
            
            for file_name in conversation_files:
                file_path = os.path.join(self.conversations_dir, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        conversations = json.load(f)
                        
                        # فرز المحادثات حسب النوع
                        if file_name.startswith("messenger_"):
                            self.messenger_conversations.extend(conversations)
                        elif file_name.startswith("facebook_comment_"):
                            self.facebook_comments.extend(conversations)
                        
                        # إضافة جميع المحادثات
                        self.all_conversations.extend(conversations)
                except Exception as e:
                    logger.error(f"خطأ في قراءة ملف المحادثة {file_name}: {e}")
            
            logger.info(f"تم تحميل {len(self.messenger_conversations)} محادثة ماسنجر و {len(self.facebook_comments)} تعليق فيسبوك")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في تحميل المحادثات: {e}")
            return False
    
    def analyze_conversations(self) -> Dict[str, Any]:
        """
        تحليل بيانات المحادثات وتوليد الإحصائيات المختلفة
        
        :return: قاموس يحتوي على نتائج التحليل
        """
        try:
            # التأكد من وجود بيانات للتحليل
            if not self.all_conversations:
                if not self.load_conversations():
                    logger.error("لا توجد بيانات للتحليل")
                    return {}
            
            # إحصائيات عامة
            self.total_messages = len(self.messenger_conversations)
            self.total_comments = len(self.facebook_comments)
            
            # متوسط طول الرد
            if self.all_conversations:
                response_lengths = [len(conv["response"]) for conv in self.all_conversations if "response" in conv]
                self.avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
            
            # تحليل المواضيع الشائعة
            self._analyze_common_topics()
            
            # تحليل توزيع المحادثات حسب الوقت
            self._analyze_time_distribution()
            
            # تحليل فئات المستخدمين
            self._analyze_user_categories()
            
            # إحصائيات اليوم
            self._generate_today_stats()
            
            # إنشاء قاموس النتائج
            results = {
                "total_messages": self.total_messages,
                "total_comments": self.total_comments,
                "avg_response_length": self.avg_response_length,
                "common_topics": self.common_topics,
                "topic_distribution": self.topic_distribution,
                "hourly_distribution": self.hourly_distribution,
                "daily_distribution": self.daily_distribution,
                "user_categories": self.user_categories,
                "today_stats": self.today_stats
            }
            
            logger.info("تم تحليل المحادثات بنجاح")
            return results
        
        except Exception as e:
            logger.error(f"خطأ في تحليل المحادثات: {e}")
            return {}
    
    def _analyze_common_topics(self) -> None:
        """
        تحليل المواضيع الشائعة في المحادثات
        """
        # الكلمات المفتاحية للمواضيع المختلفة
        topic_keywords = {
            "وظائف": ["وظيفة", "عمل", "توظيف", "شغل", "مرتب", "راتب", "تقديم", "سيرة ذاتية", "فرصة"],
            "استثمار": ["استثمار", "مشروع", "تمويل", "شراكة", "رأس مال", "ربح", "عائد", "فرصة استثمارية"],
            "خدمات شركات": ["خدمات شركات", "تأسيس شركة", "استشارات", "دراسة جدوى", "عقارات صناعية", "مواد خام"],
            "فض منازعات": ["شكوى", "منازعة", "خلاف", "مشكلة قانونية", "نزاع", "تسوية", "قضية"],
            "تدريب": ["تدريب", "كورس", "دورة", "تعليم", "تأهيل", "مهارات", "تطوير"],
            "معلومات عامة": ["معلومات", "عنوان", "موقع", "مجمع", "هاتف", "تواصل", "إيميل"]
        }
        
        # عدد المحادثات لكل موضوع
        topic_counts = {topic: 0 for topic in topic_keywords}
        
        # فحص كل محادثة
        for conv in self.all_conversations:
            message = conv.get("message", "").lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in message for keyword in keywords):
                    topic_counts[topic] += 1
        
        # ترتيب المواضيع حسب التكرار
        self.common_topics = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True))
        
        # حساب توزيع المواضيع كنسب مئوية
        total = sum(topic_counts.values())
        self.topic_distribution = {topic: (count / total * 100) if total > 0 else 0 for topic, count in topic_counts.items()}
    
    def _analyze_time_distribution(self) -> None:
        """
        تحليل توزيع المحادثات حسب الوقت
        """
        # التوزيع حسب الساعة
        hourly_counts = {i: 0 for i in range(24)}
        
        # التوزيع حسب اليوم
        days = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        daily_counts = {day: 0 for day in days}
        
        # فحص كل محادثة
        for conv in self.all_conversations:
            if "timestamp" in conv:
                try:
                    # تحويل الطابع الزمني إلى كائن تاريخ
                    timestamp = datetime.fromisoformat(conv["timestamp"])
                    
                    # زيادة عداد الساعة المناسبة
                    hourly_counts[timestamp.hour] += 1
                    
                    # زيادة عداد اليوم المناسب
                    day_name = days[timestamp.weekday()]
                    daily_counts[day_name] += 1
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"خطأ في تحليل الطابع الزمني: {e}")
        
        self.hourly_distribution = hourly_counts
        self.daily_distribution = daily_counts
    
    def _analyze_user_categories(self) -> None:
        """
        تحليل فئات المستخدمين استنادًا إلى محتوى المحادثات
        """
        # الكلمات المفتاحية لفئات المستخدمين
        user_categories = {
            "باحث عن عمل": ["وظيفة", "عمل", "توظيف", "شغل", "مرتب", "راتب", "تقديم", "سيرة ذاتية", "خريج", "خبرة"],
            "مستثمر": ["استثمار", "مشروع", "تمويل", "شراكة", "رأس مال", "ربح", "عائد", "فرصة استثمارية", "مستثمر"],
            "صحفي": ["صحفي", "إعلام", "مقابلة", "تصريح", "خبر", "تقرير", "مجلة", "جريدة", "صحافة"],
            "شركة": ["شركة", "مؤسسة", "جهة", "مصنع", "تعاون", "شراكة", "تفاهم", "بروتوكول", "اتفاقية"],
            "عام": []
        }
        
        # عدد المستخدمين لكل فئة
        category_counts = {category: 0 for category in user_categories}
        
        # فحص كل محادثة
        for conv in self.all_conversations:
            message = conv.get("message", "").lower()
            categorized = False
            
            for category, keywords in user_categories.items():
                if category != "عام" and any(keyword in message for keyword in keywords):
                    category_counts[category] += 1
                    categorized = True
                    break
            
            # إذا لم يتم تصنيف المحادثة، أضفها إلى الفئة العامة
            if not categorized:
                category_counts["عام"] += 1
        
        # ترتيب الفئات حسب التكرار
        self.user_categories = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _generate_today_stats(self) -> None:
        """
        توليد إحصائيات اليوم الحالي
        """
        today = datetime.now().date()
        today_conversations = []
        
        # فلترة محادثات اليوم
        for conv in self.all_conversations:
            if "timestamp" in conv:
                try:
                    timestamp = datetime.fromisoformat(conv["timestamp"]).date()
                    if timestamp == today:
                        today_conversations.append(conv)
                except (ValueError, TypeError):
                    pass
        
        # إحصائيات عامة لهذا اليوم
        today_messages = [conv for conv in today_conversations if conv.get("source") == "messenger"]
        today_comments = [conv for conv in today_conversations if conv.get("source") == "facebook_comment"]
        
        self.today_stats["total_messages"] = len(today_messages)
        self.today_stats["total_comments"] = len(today_comments)
        
        # تحليل المواضيع الشائعة لهذا اليوم
        topic_keywords = {
            "وظائف": ["وظيفة", "عمل", "توظيف", "شغل", "مرتب", "راتب", "تقديم", "سيرة ذاتية", "فرصة"],
            "استثمار": ["استثمار", "مشروع", "تمويل", "شراكة", "رأس مال", "ربح", "عائد", "فرصة استثمارية"],
            "خدمات شركات": ["خدمات شركات", "تأسيس شركة", "استشارات", "دراسة جدوى", "عقارات صناعية", "مواد خام"],
            "فض منازعات": ["شكوى", "منازعة", "خلاف", "مشكلة قانونية", "نزاع", "تسوية", "قضية"],
            "تدريب": ["تدريب", "كورس", "دورة", "تعليم", "تأهيل", "مهارات", "تطوير"],
            "معلومات عامة": ["معلومات", "عنوان", "موقع", "مجمع", "هاتف", "تواصل", "إيميل"]
        }
        
        topic_counts = {topic: 0 for topic in topic_keywords}
        
        for conv in today_conversations:
            message = conv.get("message", "").lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in message for keyword in keywords):
                    topic_counts[topic] += 1
        
        self.today_stats["common_topics"] = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True))
        
        # تحليل فئات المستخدمين لهذا اليوم
        user_categories = {
            "باحث عن عمل": ["وظيفة", "عمل", "توظيف", "شغل", "مرتب", "راتب", "تقديم", "سيرة ذاتية", "خريج", "خبرة"],
            "مستثمر": ["استثمار", "مشروع", "تمويل", "شراكة", "رأس مال", "ربح", "عائد", "فرصة استثمارية", "مستثمر"],
            "صحفي": ["صحفي", "إعلام", "مقابلة", "تصريح", "خبر", "تقرير", "مجلة", "جريدة", "صحافة"],
            "شركة": ["شركة", "مؤسسة", "جهة", "مصنع", "تعاون", "شراكة", "تفاهم", "بروتوكول", "اتفاقية"],
            "عام": []
        }
        
        category_counts = {category: 0 for category in user_categories}
        
        for conv in today_conversations:
            message = conv.get("message", "").lower()
            categorized = False
            
            for category, keywords in user_categories.items():
                if category != "عام" and any(keyword in message for keyword in keywords):
                    category_counts[category] += 1
                    categorized = True
                    break
            
            if not categorized:
                category_counts["عام"] += 1
        
        self.today_stats["user_categories"] = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))
    
    def generate_report(self, output_format: str = "json") -> str:
        """
        توليد تقرير بالتحليلات
        
        :param output_format: صيغة التقرير (json أو text)
        :return: التقرير بالصيغة المطلوبة
        """
        # تأكد من تحليل البيانات
        results = self.analyze_conversations()
        
        if not results:
            return "لم يتم العثور على بيانات كافية لتوليد التقرير"
        
        if output_format == "json":
            try:
                report_file = f"{self.analytics_dir}/chatbot_analytics_{datetime.now().strftime('%Y%m%d')}.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
                
                logger.info(f"تم توليد تقرير JSON بنجاح: {report_file}")
                return f"تم توليد التقرير بنجاح. مسار الملف: {report_file}"
            
            except Exception as e:
                logger.error(f"خطأ في توليد تقرير JSON: {e}")
                return f"حدث خطأ أثناء توليد التقرير: {e}"
                
        else:  # "text"
            try:
                report_file = f"{self.analytics_dir}/chatbot_analytics_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write("تقرير تحليل أداء الشات بوت\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("إحصائيات عامة:\n")
                    f.write(f"عدد محادثات الماسنجر: {results['total_messages']}\n")
                    f.write(f"عدد تعليقات الفيسبوك: {results['total_comments']}\n")
                    f.write(f"متوسط طول الرد: {results['avg_response_length']:.2f} حرف\n\n")
                    
                    f.write("المواضيع الشائعة:\n")
                    for topic, count in results['common_topics'].items():
                        f.write(f"{topic}: {count} محادثة ({results['topic_distribution'].get(topic, 0):.1f}%)\n")
                    f.write("\n")
                    
                    f.write("فئات المستخدمين:\n")
                    for category, count in results['user_categories'].items():
                        f.write(f"{category}: {count} مستخدم\n")
                    f.write("\n")
                    
                    f.write("إحصائيات اليوم:\n")
                    f.write(f"عدد محادثات الماسنجر اليوم: {results['today_stats']['total_messages']}\n")
                    f.write(f"عدد تعليقات الفيسبوك اليوم: {results['today_stats']['total_comments']}\n")
                    f.write("المواضيع الشائعة اليوم:\n")
                    for topic, count in results['today_stats']['common_topics'].items():
                        if count > 0:
                            f.write(f"{topic}: {count} محادثة\n")
                    f.write("\n")
                
                logger.info(f"تم توليد تقرير نصي بنجاح: {report_file}")
                return f"تم توليد التقرير بنجاح. مسار الملف: {report_file}"
            
            except Exception as e:
                logger.error(f"خطأ في توليد تقرير نصي: {e}")
                return f"حدث خطأ أثناء توليد التقرير: {e}"
    
    def generate_visualizations(self) -> bool:
        """
        توليد رسومات بيانية للتحليلات
        
        :return: True إذا تم التوليد بنجاح
        """
        try:
            # تأكد من تحليل البيانات
            results = self.analyze_conversations()
            
            if not results:
                logger.warning("لم يتم العثور على بيانات كافية لتوليد الرسومات")
                return False
            
            # إنشاء مجلد للرسومات البيانية
            viz_dir = f"{self.analytics_dir}/visualizations"
            os.makedirs(viz_dir, exist_ok=True)
            
            # تحديد نمط الرسومات البيانية
            plt.style.use('seaborn-v0_8-darkgrid')
            
            # 1. رسم بياني للمواضيع الشائعة
            self._plot_common_topics(viz_dir)
            
            # 2. رسم بياني لتوزيع المحادثات حسب الساعة
            self._plot_hourly_distribution(viz_dir)
            
            # 3. رسم بياني لتوزيع المحادثات حسب اليوم
            self._plot_daily_distribution(viz_dir)
            
            # 4. رسم بياني لفئات المستخدمين
            self._plot_user_categories(viz_dir)
            
            # 5. سحابة الكلمات المستخدمة في الأسئلة
            self._generate_word_cloud(viz_dir)
            
            logger.info(f"تم توليد الرسومات البيانية بنجاح في المجلد: {viz_dir}")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في توليد الرسومات البيانية: {e}")
            return False
    
    def _plot_common_topics(self, viz_dir: str) -> None:
        """
        رسم بياني للمواضيع الشائعة
        
        :param viz_dir: مسار مجلد الرسومات البيانية
        """
        # التأكد من وجود بيانات
        if not self.common_topics:
            return
        
        plt.figure(figsize=(10, 6))
        topics = list(self.topic_distribution.keys())
        percentages = [self.topic_distribution[topic] for topic in topics]
        
        # ترتيب المواضيع حسب النسبة
        sorted_indices = np.argsort(percentages)[::-1]
        topics = [topics[i] for i in sorted_indices]
        percentages = [percentages[i] for i in sorted_indices]
        
        # رسم المخطط
        plt.bar(topics, percentages, color=sns.color_palette("viridis", len(topics)))
        plt.title("توزيع المواضيع الشائعة", fontsize=16)
        plt.xlabel("الموضوع", fontsize=12)
        plt.ylabel("النسبة المئوية (%)", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # حفظ المخطط
        plt.savefig(f"{viz_dir}/common_topics.png", dpi=300, bbox_inches="tight")
        plt.close()
    
    def _plot_hourly_distribution(self, viz_dir: str) -> None:
        """
        رسم بياني لتوزيع المحادثات حسب الساعة
        
        :param viz_dir: مسار مجلد الرسومات البيانية
        """
        # التأكد من وجود بيانات
        if not self.hourly_distribution:
            return
        
        plt.figure(figsize=(12, 6))
        hours = list(self.hourly_distribution.keys())
        counts = list(self.hourly_distribution.values())
        
        # رسم المخطط
        plt.bar(hours, counts, color=sns.color_palette("viridis", 24))
        plt.title("توزيع المحادثات حسب الساعة", fontsize=16)
        plt.xlabel("الساعة", fontsize=12)
        plt.ylabel("عدد المحادثات", fontsize=12)
        plt.xticks(hours)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # حفظ المخطط
        plt.savefig(f"{viz_dir}/hourly_distribution.png", dpi=300, bbox_inches="tight")
        plt.close()
    
    def _plot_daily_distribution(self, viz_dir: str) -> None:
        """
        رسم بياني لتوزيع المحادثات حسب اليوم
        
        :param viz_dir: مسار مجلد الرسومات البيانية
        """
        # التأكد من وجود بيانات
        if not self.daily_distribution:
            return
        
        plt.figure(figsize=(10, 6))
        days = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        counts = [self.daily_distribution.get(day, 0) for day in days]
        
        # رسم المخطط
        plt.bar(days, counts, color=sns.color_palette("viridis", 7))
        plt.title("توزيع المحادثات حسب اليوم", fontsize=16)
        plt.xlabel("اليوم", fontsize=12)
        plt.ylabel("عدد المحادثات", fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # حفظ المخطط
        plt.savefig(f"{viz_dir}/daily_distribution.png", dpi=300, bbox_inches="tight")
        plt.close()
    
    def _plot_user_categories(self, viz_dir: str) -> None:
        """
        رسم بياني لفئات المستخدمين
        
        :param viz_dir: مسار مجلد الرسومات البيانية
        """
        # التأكد من وجود بيانات
        if not self.user_categories:
            return
        
        plt.figure(figsize=(10, 6))
        categories = list(self.user_categories.keys())
        counts = list(self.user_categories.values())
        
        # ترتيب الفئات حسب العدد
        sorted_indices = np.argsort(counts)[::-1]
        categories = [categories[i] for i in sorted_indices]
        counts = [counts[i] for i in sorted_indices]
        
        # حساب النسب المئوية
        total = sum(counts)
        percentages = [(count / total * 100) if total > 0 else 0 for count in counts]
        
        # رسم المخطط
        plt.pie(percentages, labels=categories, autopct="%1.1f%%", startangle=90, 
                colors=sns.color_palette("viridis", len(categories)))
        plt.title("توزيع فئات المستخدمين", fontsize=16)
        plt.axis("equal")
        plt.tight_layout()
        
        # حفظ المخطط
        plt.savefig(f"{viz_dir}/user_categories.png", dpi=300, bbox_inches="tight")
        plt.close()
    
    def _generate_word_cloud(self, viz_dir: str) -> None:
        """
        توليد سحابة الكلمات المستخدمة في الأسئلة
        
        :param viz_dir: مسار مجلد الرسومات البيانية
        """
        # جمع جميع الرسائل
        messages = [conv.get("message", "") for conv in self.all_conversations if "message" in conv]
        
        if not messages:
            return
        
        # دمج جميع الرسائل في نص واحد
        text = " ".join(messages)
        
        # قائمة الكلمات التي يجب استبعادها
        stopwords = [
            "هل", "في", "على", "من", "إلى", "عن", "مع", "كيف", "لماذا", "متى", "أين", "هذا", "هذه", "ذلك", "تلك",
            "ما", "ماذا", "يا", "أي", "أية", "أنا", "نحن", "هو", "هي", "هم", "أنت", "أنتم", "أنتما", "أنتن"
        ]
        
        # إعادة تشكيل النص العربي
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        
        # إنشاء سحابة الكلمات
        wordcloud = WordCloud(
            width=800, height=400,
            background_color="white",
            stopwords=set(stopwords),
            font_path="arial.ttf" if os.path.exists("arial.ttf") else None,
            max_words=100
        ).generate(bidi_text)
        
        # رسم سحابة الكلمات
        plt.figure(figsize=(10, 6))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title("الكلمات الأكثر استخداماً في الأسئلة", fontsize=16)
        plt.tight_layout()
        
        # حفظ المخطط
        plt.savefig(f"{viz_dir}/word_cloud.png", dpi=300, bbox_inches="tight")
        plt.close()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        الحصول على مقاييس أداء الشات بوت
        
        :return: قاموس بمقاييس الأداء
        """
        # تأكد من تحليل البيانات
        self.analyze_conversations()
        
        # حساب نسبة المحادثات لكل مصدر
        total_interactions = self.total_messages + self.total_comments
        messenger_percentage = (self.total_messages / total_interactions * 100) if total_interactions > 0 else 0
        comments_percentage = (self.total_comments / total_interactions * 100) if total_interactions > 0 else 0
        
        # حساب متوسط عدد المحادثات اليومية
        if self.all_conversations:
            # استخراج جميع التواريخ
            dates = []
            for conv in self.all_conversations:
                if "timestamp" in conv:
                    try:
                        date = datetime.fromisoformat(conv["timestamp"]).date()
                        dates.append(date)
                    except (ValueError, TypeError):
                        pass
            
            # حساب عدد الأيام الفريدة
            unique_dates = len(set(dates)) if dates else 1
            
            # حساب متوسط المحادثات اليومية
            avg_daily_interactions = len(self.all_conversations) / unique_dates
        else:
            avg_daily_interactions = 0
        
        # إنشاء قاموس مقاييس الأداء
        metrics = {
            "total_interactions": total_interactions,
            "messenger_percentage": messenger_percentage,
            "comments_percentage": comments_percentage,
            "avg_response_length": self.avg_response_length,
            "avg_daily_interactions": avg_daily_interactions,
            "most_common_topic": next(iter(self.common_topics), ""),
            "most_common_user_category": next(iter(self.user_categories), ""),
            "today_interactions": self.today_stats["total_messages"] + self.today_stats["total_comments"]
        }
        
        return metrics


def main():
    """
    الدالة الرئيسية لتحليل أداء الشات بوت
    """
    print("جاري تحليل أداء الشات بوت...")
    
    # إنشاء محلل أداء الشات بوت
    analytics = ChatbotAnalytics()
    
    # تحميل وتحليل المحادثات
    if analytics.load_conversations():
        # توليد التقرير
        report_path = analytics.generate_report(output_format="text")
        print(f"تم توليد التقرير: {report_path}")
        
        # توليد الرسومات البيانية
        if analytics.generate_visualizations():
            print("تم توليد الرسومات البيانية بنجاح")
        
        # عرض مقاييس الأداء الأساسية
        metrics = analytics.get_performance_metrics()
        
        print("\nمقاييس أداء الشات بوت:")
        print(f"إجمالي التفاعلات: {metrics['total_interactions']}")
        print(f"نسبة محادثات الماسنجر: {metrics['messenger_percentage']:.1f}%")
        print(f"نسبة تعليقات الفيسبوك: {metrics['comments_percentage']:.1f}%")
        print(f"متوسط طول الرد: {metrics['avg_response_length']:.1f} حرف")
        print(f"متوسط التفاعلات اليومية: {metrics['avg_daily_interactions']:.1f}")
        print(f"الموضوع الأكثر شيوعاً: {metrics['most_common_topic']}")
        print(f"فئة المستخدمين الأكثر شيوعاً: {metrics['most_common_user_category']}")
        print(f"تفاعلات اليوم: {metrics['today_interactions']}")
    
    else:
        print("لم يتم العثور على ملفات محادثات. تأكد من وجود ملفات المحادثات في المجلد المحدد.")


if __name__ == "__main__":
    main()