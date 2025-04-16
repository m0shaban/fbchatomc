"""
ملف لعرض إحصائيات وتحليلات شات بوت مجمع عمال مصر
يقوم بتحليل سجلات المحادثات وعرض إحصائيات مفيدة
"""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
from tabulate import tabulate

from config import BOT_SETTINGS, APP_SETTINGS, setup_log_directory, setup_conversations_directory

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=APP_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

class ChatBotAnalytics:
    """
    صنف لتحليل بيانات الشات بوت وعرض الإحصائيات
    """
    
    def __init__(self, conversations_dir: str = None, analytics_file: str = None):
        """
        تهيئة محلل البيانات
        
        :param conversations_dir: مجلد المحادثات
        :param analytics_file: ملف الإحصائيات من معالج تعليقات الفيسبوك
        """
        self.conversations_dir = conversations_dir or BOT_SETTINGS.get("CONVERSATIONS_DIR", "conversations")
        self.analytics_file = analytics_file or os.path.join(self.conversations_dir, "facebook_analytics.json")
        
        # تأكد من وجود المجلدات اللازمة
        setup_log_directory()
        setup_conversations_directory()
        
        # بيانات المحادثات
        self.messenger_conversations = {}
        self.facebook_comments = {}
        self.facebook_analytics = {}
        
        # قراءة البيانات
        self._load_data()
    
    def _load_data(self) -> None:
        """
        تحميل بيانات المحادثات والإحصائيات
        """
        # قراءة ملفات المحادثات
        for filename in os.listdir(self.conversations_dir):
            filepath = os.path.join(self.conversations_dir, filename)
            
            if not os.path.isfile(filepath) or not filename.endswith('.json'):
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if filename.startswith('messenger_'):
                    self.messenger_conversations[filename] = data
                elif filename.startswith('facebook_comment_'):
                    self.facebook_comments[filename] = data
                elif filename == "facebook_analytics.json":
                    self.facebook_analytics = data
            except Exception as e:
                logger.error(f"خطأ في قراءة ملف {filename}: {e}")
        
        logger.info(f"تم تحميل {len(self.messenger_conversations)} ملف محادثات ماسنجر")
        logger.info(f"تم تحميل {len(self.facebook_comments)} ملف تعليقات فيسبوك")
        
        if self.facebook_analytics:
            logger.info("تم تحميل بيانات تحليلية للفيسبوك")
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات المحادثات
        
        :return: قاموس بالإحصائيات
        """
        stats = {
            "messenger": {
                "total_conversations": len(self.messenger_conversations),
                "total_messages": 0,
                "avg_messages_per_conversation": 0,
                "unique_users": set()
            },
            "facebook_comments": {
                "total_conversations": len(self.facebook_comments),
                "total_comments": 0,
                "responded_comments": 0,
                "unique_commenters": set()
            }
        }
        
        # حساب إحصائيات ماسنجر
        for filename, conversation in self.messenger_conversations.items():
            if isinstance(conversation, list):
                stats["messenger"]["total_messages"] += len(conversation)
                
                for message in conversation:
                    if isinstance(message, dict) and "user_id" in message:
                        stats["messenger"]["unique_users"].add(message["user_id"])
        
        # حساب إحصائيات تعليقات الفيسبوك
        for filename, comments in self.facebook_comments.items():
            if isinstance(comments, list):
                stats["facebook_comments"]["total_comments"] += len(comments)
                
                for comment in comments:
                    if isinstance(comment, dict):
                        if "user_id" in comment:
                            stats["facebook_comments"]["unique_commenters"].add(comment["user_id"])
                        if "response" in comment:
                            stats["facebook_comments"]["responded_comments"] += 1
        
        # حساب المتوسطات
        if stats["messenger"]["total_conversations"] > 0:
            stats["messenger"]["avg_messages_per_conversation"] = (
                stats["messenger"]["total_messages"] / stats["messenger"]["total_conversations"]
            )
        
        # تحويل المجموعات إلى أرقام
        stats["messenger"]["unique_users"] = len(stats["messenger"]["unique_users"])
        stats["facebook_comments"]["unique_commenters"] = len(stats["facebook_comments"]["unique_commenters"])
        
        # إضافة إحصائيات الفيسبوك إذا كانت متوفرة
        if self.facebook_analytics:
            stats["facebook_analytics"] = self.facebook_analytics
        
        return stats
    
    def get_response_categories(self) -> Dict[str, int]:
        """
        الحصول على إحصائيات فئات الردود
        
        :return: قاموس بعدد الردود لكل فئة
        """
        if not self.facebook_analytics or "responses_by_category" not in self.facebook_analytics:
            return {}
        
        return self.facebook_analytics["responses_by_category"]
    
    def print_stats_report(self) -> None:
        """
        طباعة تقرير بالإحصائيات
        """
        stats = self.get_conversation_stats()
        
        print("\n===== تقرير إحصائيات شات بوت مجمع عمال مصر =====\n")
        
        # إحصائيات عامة
        print("إحصائيات عامة:")
        print(f"• عدد محادثات الماسنجر: {stats['messenger']['total_conversations']}")
        print(f"• عدد مستخدمي الماسنجر الفريدين: {stats['messenger']['unique_users']}")
        print(f"• عدد محادثات تعليقات الفيسبوك: {stats['facebook_comments']['total_conversations']}")
        print(f"• عدد المعلقين الفريدين على الفيسبوك: {stats['facebook_comments']['unique_commenters']}")
        
        # إحصائيات التعليقات
        if "facebook_analytics" in stats:
            fb_analytics = stats["facebook_analytics"]
            print("\nإحصائيات تعليقات الفيسبوك:")
            print(f"• إجمالي التعليقات المعالجة: {fb_analytics.get('total_comments_processed', 0)}")
            print(f"• إجمالي الردود المولدة: {fb_analytics.get('total_responses_generated', 0)}")
            print(f"• التعليقات المتجاهلة: {fb_analytics.get('ignored_comments', 0)}")
            print(f"• أخطاء API: {fb_analytics.get('api_errors', 0)}")
            
            # إحصائيات فئات الردود
            categories = self.get_response_categories()
            if categories:
                print("\nتوزيع الردود حسب الفئة:")
                for category, count in categories.items():
                    if count > 0:
                        print(f"• {category}: {count}")
        
        print("\n===============================================\n")
    
    def generate_charts(self, output_dir: str = None) -> None:
        """
        إنشاء رسوم بيانية للإحصائيات
        
        :param output_dir: مجلد الإخراج للرسوم البيانية
        """
        if output_dir is None:
            output_dir = os.path.join(self.conversations_dir, "analytics")
        
        os.makedirs(output_dir, exist_ok=True)
        
        stats = self.get_conversation_stats()
        categories = self.get_response_categories()
        
        # رسم بياني لفئات الردود
        if categories:
            plt.figure(figsize=(10, 6))
            categories_data = {k: v for k, v in categories.items() if v > 0}
            plt.bar(categories_data.keys(), categories_data.values())
            plt.title('توزيع الردود حسب الفئة', fontsize=14)
            plt.xlabel('الفئة', fontsize=12)
            plt.ylabel('عدد الردود', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'categories_distribution.png'))
            plt.close()
        
        # رسم بياني للتعليقات المعالجة مقابل الردود
        if "facebook_analytics" in stats:
            fb_analytics = stats["facebook_analytics"]
            plt.figure(figsize=(10, 6))
            fb_data = [
                fb_analytics.get('total_comments_processed', 0),
                fb_analytics.get('total_responses_generated', 0),
                fb_analytics.get('ignored_comments', 0)
            ]
            fb_labels = ['التعليقات المعالجة', 'الردود المولدة', 'التعليقات المتجاهلة']
            plt.bar(fb_labels, fb_data)
            plt.title('إحصائيات معالجة تعليقات الفيسبوك', fontsize=14)
            plt.ylabel('العدد', fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'facebook_comments_stats.png'))
            plt.close()
        
        print(f"تم حفظ الرسوم البيانية في المجلد: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='عرض إحصائيات شات بوت مجمع عمال مصر')
    parser.add_argument('--conversations-dir', type=str, help='مجلد المحادثات')
    parser.add_argument('--analytics-file', type=str, help='ملف الإحصائيات')
    parser.add_argument('--charts', action='store_true', help='إنشاء رسوم بيانية')
    parser.add_argument('--output-dir', type=str, help='مجلد الإخراج للرسوم البيانية')
    
    args = parser.parse_args()
    
    analytics = ChatBotAnalytics(
        conversations_dir=args.conversations_dir,
        analytics_file=args.analytics_file
    )
    
    analytics.print_stats_report()
    
    if args.charts:
        analytics.generate_charts(output_dir=args.output_dir)