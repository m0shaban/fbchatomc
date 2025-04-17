"""
الشات بوت الرسمي لمجمع عمال مصر - محمد سلامة
يقوم بالرد على استفسارات زوار صفحة مجمع عمال مصر على فيسبوك
سواء عبر الماسنجر أو تعليقات المنشورات
"""

import json
import re
import os
import random
import logging
import datetime
from typing import Dict, List, Tuple, Optional, Any
from api import DeepSeekAPI
from config import BOT_SETTINGS, APP_SETTINGS

# إعداد التسجيل
logging.basicConfig(
    level=getattr(logging, APP_SETTINGS["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=BOT_SETTINGS.get("LOG_FILE")
)
logger = logging.getLogger(__name__)

class ChatBot:
    """
    شات بوت ذكي للرد على استفسارات زوار صفحة مجمع عمال مصر على فيسبوك
    سواء عبر الماسنجر أو التعليقات
    """
    
    def __init__(self, data_file: str = None, api_key: Optional[str] = None):
        """
        تهيئة الشات بوت وتحميل البيانات من ملف JSON
        
        :param data_file: مسار ملف البيانات بصيغة JSON
        :param api_key: مفتاح API لخدمة DeepSeek (اختياري)
        """
        self.bot_name = "محمد سلامة"  # اسم الشات بوت
        self.data_file = data_file or BOT_SETTINGS.get("DATA_FILE", "data.json")
        self.prompts = []
        self.human_expressions = {}
        self.contact_info = {}
        self.requires_human_contact = []
        self.user_categories = []
        self.job_sectors = []
        self.personalize_response = BOT_SETTINGS.get("PERSONALIZE_RESPONSE", True)
        self.similarity_threshold = BOT_SETTINGS.get("SIMILARITY_THRESHOLD", 0.4)
        
        # بيانات الخدمات والروابط
        self.service_links = {}
        self.service_categories = {}
        
        # تحميل البيانات من ملف JSON
        self.load_data()
        
        # تهيئة واجهة API
        self.api = DeepSeekAPI(api_key)
        
        # تاريخ المحادثات السابقة يتضمن الآن أسماء المستخدمين
        self.conversation_history = {}
        
        # حالة المحادثة الحالية
        self.conversation_state = {}
        
        # تعيين مصدر المحادثة الحالي
        self.conversation_source = "messenger"  # messenger أو facebook_comment

        # إعدادات الاستمرارية في المحادثة
        self.continue_conversation = BOT_SETTINGS.get("CONTINUE_CONVERSATION", True)
        self.continue_phrases = [
            "هل تحتاج مزيداً من المعلومات؟",
            "هل لديك أسئلة أخرى؟",
            "هل ترغب في معرفة المزيد؟",
            "هل تريد الاستمرار في المحادثة؟",
            "هل أستطيع مساعدتك في شيء آخر؟"
        ]
        
        # خيارات التواصل مع ممثل خدمة العملاء (محمد سلامة)
        self.customer_service_phrases = [
            "للتواصل المباشر مع ممثل خدمة العملاء، أرسل كلمة 'ممثل خدمة العملاء'",
            "إذا كنت ترغب في التحدث مباشرة مع أحد ممثلي خدمة العملاء، أرسل 'تحدث مع ممثل'",
            "للاتصال بممثل خدمة العملاء، أرسل 'اتصال بممثل'"
        ]
        
        # وقت انتظار الممثل البشري (بالثواني)
        self.human_rep_wait_time = 90
        
        # معلومات الاتصال بالممثل البشري (محمد سلامة)
        self.human_rep_contact_info = {
            "name": "محمد سلامة",
            "title": "مدير خدمة العملاء - مجمع عمال مصر",
            "phone": "+201234567890",  # رقم افتراضي، يجب تغييره
            "email": "muhammad.salama@omalmisr.com",  # بريد افتراضي، يجب تغييره
            "whatsapp": "https://wa.me/201234567890",  # رابط واتساب افتراضي، يجب تغييره
            "messenger": "https://m.me/Omal.Misr.Foundation"
        }
        
        # كلمات مفتاحية للتحويل إلى ممثل خدمة العملاء
        self.customer_service_keywords = [
            "ممثل خدمة العملاء", "تحدث مع ممثل", "اتصال بممثل", "توصيل بشخص حقيقي", 
            "شخص حقيقي", "تحويل", "انسان", "موظف", "متابعة", "محمد سلامة", "سلامة",
            "خدمة عملاء", "مندوب", "مساعدة شخصية"
        ]
        
        # أسئلة للحصول على اسم المستخدم
        self.name_questions = [
            "مرحباً! أنا محمد سلامة، المساعد الرسمي لمجمع عمال مصر. ما هو اسمك الكريم؟",
            "أهلاً وسهلاً! أنا محمد سلامة من مجمع عمال مصر. قبل أن نبدأ، ممكن أعرف اسم حضرتك؟",
            "السلام عليكم! معك محمد سلامة من مجمع عمال مصر. يشرفني التعرف على اسمك الكريم.",
            "مرحباً بك في مجمع عمال مصر! أنا محمد سلامة مساعدك الشخصي. ما هو اسمك؟"
        ]
        
        # تعريف هيكل القائمة الرئيسية للخدمات
        self.main_menu = {
            "أبحث عن عمل": {
                "title": "أبحث عن عمل",
                "description": "سجل معنا لتجد وظيفتك المناسبة",
                "link": "https://omalmisrservices.com/ar/jobs"
            },
            "أبحث عن موظفين وعمال": {
                "title": "أبحث عن موظفين و عمال",
                "description": "سجل بياناتك للحصول على موظفيين",
                "link": "https://omalmisrservices.com/ar/workers"
            },
            "خدمات الشركات": {
                "title": "خدمات الشركات",
                "description": "خدمات الاسثمار الصناعي و الزراعي",
                "link": "https://omalmisrservices.com/ar/companies",
                "submenu": {
                    "طرح الفرص الإستثمارية": {
                        "title": "طرح الفرص الإستثمارية",
                        "description": "يختص هذا القسم بطرح الفرص االستثمارية المميزة في المجال الصناعي و المجال الزراعي بناء على دراسة السوق الحالي",
                        "link": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=2&title=%D8%B7%D8%B1%D8%AD%20%D8%A7%D9%84%D9%81%D8%B1%D8%B5%20%D8%A7%D9%84%D8%A5%D8%B3%D8%AA%D8%AB%D9%85%D8%A7%D8%B1%D9%8A%D8%A9"
                    },
                    "دراسات الجدوى الإقتصادية": {
                        "title": "دراسات الجدوى الإقتصادية",
                        "description": "تأتي مهمة هذا القسم في عمل الدراسات الالزمة للمشروع ويخدم تحت مظلة هذا القسم عدد 6 شركات محلية ودولية متخصصة في دراسات الجدوى للمشروعات الصغيرة والكبيرة",
                        "link": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=3&title=%D8%AF%D8%B1%D8%A7%D8%B3%D8%A7%D8%AA%20%D8%A7%D9%84%D8%AC%D8%AF%D9%88%D9%89%20%D8%A7%D9%84%D8%A5%D8%AF%D8%A7%D8%B1%D9%8A%D8%A9"
                    },
                    "الشراكة الإستراتيجية": {
                        "title": "الشراكة الإستراتيجية",
                        "description": "تتكون مهمة هذا القسم في عمل الدراسات الالزمة إلقامة المشروع إما من خالل توفير شريك محلي او شريك اجنبي وأيضا من خالل المحافظ والصناديق اإلستثمارية",
                        "link": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=4&title=%D8%A7%D9%84%D8%B4%D8%B1%D8%A7%D9%83%D8%A9%20%D8%A7%D9%84%D8%A5%D8%B3%D8%AA%D8%B1%D8%A7%D8%AA%D9%8A%D8%AC%D9%8A%D8%A9"
                    },
                    "الإنشاءات والعقارات الصناعية": {
                        "title": "الإنشاءات والعقارات الصناعية",
                        "description": "يختص هذا القسم بعمل الرسومات والتصميمات الهندسية للمنشأة الصناعية بما يتناسب مع إحتياجات وبيئة العمل وتوفير المواقع الالزمة إلقامة المشاريع الصناعية و الزراعية",
                        "link": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=5&title=%D8%A7%D9%84%D8%A5%D9%86%D8%B4%D8%A7%D8%A1%D8%A7%D8%AA%20%D9%88%D8%A7%D9%84%D8%B9%D9%82%D8%A7%D8%B1%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B5%D9%86%D8%A7%D8%B9%D9%8A%D8%A9"
                    },
                    "الخامات ومستلزمات الإنتاج": {
                        "title": "الخامات ومستلزمات الإنتاج",
                        "description": "ختص هذا القسم بتوفير الخامات ومستلزمات اإلنتاج طبقً الالزمة بالمعايير و المواصفات المطلوبة ا لمعايير الجودة العالمية",
                        "link": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=6&title=%D8%A7%D9%84%D8%AE%D8%A7%D9%85%D8%A7%D8%AA%20%D9%88%D9%85%D8%B3%D8%AA%D9%84%D8%B2%D9%85%D8%A7%D8%AA%20%D8%A7%D9%84%D8%A5%D9%86%D8%AA%D8%A7%D8%AC"
                    },
                    "التسويق المحلي للمنتجات": {
                        "title": "التسويق المحلي للمنتجات الصناعية و الزراعية",
                        "description": "يختص هذا القسم بإجراء تحليل للسوق تمهيدا لدخول منتج جديد في السوق وبناء وخلق الافكار التسويقية لاستهداف المستهلك من خلال كافة القنوات الدعائية والخطط التسوقية وترويج المنتج طبا لاحتياجات الاسواق المختلفة المحلية",
                        "link": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=7&title=%D8%A7%D9%84%D8%AA%D8%B3%D9%88%D9%8A%D9%82%20%D8%A7%D9%84%D9%85%D8%AD%D9%84%D9%8A%20%D9%84%D9%84%D9%85%D9%86%D8%AA%D8%AC%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B5%D9%86%D8%A7%D8%B9%D9%8A%D8%A9%20%D9%88%20%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A%D8%A9"
                    },
                    "التسويق الدولي للمنتجات": {
                        "title": "التسويق الدولي للمنتجات الصناعية و الزراعية",
                        "description": "يختص هذا القسم بإجراء تحليل للسوق تمهيدا لتصدير المنتجات الصناعية و الزراعية في دول الخليج العربي و دول افريقيا و دول االتحاد االوروبي وبناء وخلق األفكار التسويقية إلستهداف المستهلك من خالل كافة القنوات الدعائية والخطط",
                        "link": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=8&title=%D8%A7%D9%84%D8%AA%D8%B3%D9%88%D9%8A%D9%82%20%D8%A7%D9%84%D8%AF%D9%88%D9%84%D9%8A%20%D9%84%D9%84%D9%85%D9%86%D8%AA%D8%AC%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B5%D9%86%D8%A7%D8%B9%D9%8A%D8%A9%20%D9%88%20%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A%D8%A9"
                    },
                    "الخدمات الحكومية": {
                        "title": "الخدمات الحكومية",
                        "description": "هذا القسم يختص بوضع حلول لكافة العقبات للمستثمرين في القطاع الصناعي وفقا لقوانين اإلستثمار الدولية والمحلية وتوفير كافة الخدمات التي تحتاجها المنشآت الصناعية من الوزارات والجهات الحكومية.",
                        "link": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=9&title=%D8%A7%D9%84%D8%AE%D8%AF%D9%85%D8%A7%D8%AA%20%D8%A7%D9%84%D8%AD%D9%83%D9%88%D9%85%D9%8A%D8%A9"
                    },
                    "خدمات التعليم والبحث العلمي": {
                        "title": "خدمات التعليم والبحث العلمي",
                        "description": "تقديم الدورات التدريبة للكوادر البشرية الفنية والادارية تقديم الاستشارات الفنية والادارية",
                        "link": "https://omalmisrservices.com/ar/companies?type=7"
                    },
                    "خدمة الشؤون المالية": {
                        "title": "خدمة الشؤون المالية",
                        "description": "تقديم خدمة إدارة الشئون المالية للمنشآت تقديم الاستشارات المالية ادارة الملف الضريبي",
                        "link": "https://omalmisrservices.com/ar/companies?type=8"
                    },
                    "خدمة تكنولوجيا المعلومات": {
                        "title": "خدمة تكنولوجيا المعلومات",
                        "description": "يقدم هذا القطاع خدمات إنشاء المواقع الالكترونية والتطبيقات  ادارة المواقع الالكترونية",
                        "link": "https://omalmisrservices.com/ar/companies?type=6"
                    },
                    "خدمات الاستشارات القانونية": {
                        "title": "خدمات الاستشارات القانونية",
                        "description": "هو قطاع مسئول عن جميع الاستشارات القانونية الخاصة بالشركات (العقود والتراخيص-إدارة",
                        "link": "https://omalmisrservices.com/ar/companies?type=5"
                    },
                    "الخدمات الاعلامية": {
                        "title": "الخدمات الاعلامية",
                        "description": "يوفر الأفكار الإعلانية والحملات الدعائية ويوفر خدمات الجرافيك والمونتاج إدارة السوشيال مديا",
                        "link": "https://omalmisrservices.com/ar/companies?type=4"
                    },
                    "خدمات تسويق الموارد البشرية": {
                        "title": "خدمات تسويق الموارد البشرية",
                        "description": "يختص هذا القطاع بتوفير الكوادر البشرية المدربة والمؤهلة (الفنية والإدارية)",
                        "link": "https://omalmisrservices.com/ar/companies?type=3"
                    },
                    "خدمات تسويق فرص العمل": {
                        "title": "خدمات تسويق فرص العمل",
                        "description": "هذا القطاع يختص في التواصل مع المتقدمين على الوظائف و تشغيلهم  حسب المعايير",
                        "link": "https://omalmisrservices.com/ar/companies?type=2"
                    },
                    "خدمة الإستثمار الصناعي والزراعي": {
                        "title": "خدمة الإستثمار الصناعي والزراعي",
                        "description": "يتم تقديم الخدمات الاستثمارية على ثلاث مراحل: الاولى : طرح الفرص والانشاء",
                        "link": "https://omalmisrservices.com/ar/companies?type=1"
                    }
                }
            },
            "بوابة فض المنازعات": {
                "title": "بوابة فض و تسوية المنازاعات",
                "description": "هي بوابة إلكترنية لفض و تسوية المنازاعات الناتجية بين مؤسستين أو أكثر أو بين المؤسسات و العاملين بها بوسطة خبراء و مستشارين قانونين متخصصين دون اللجوء إلى الجهات القضائية و هي تتبع مؤسسة عمال مصر",
                "link": "https://omalmisrservices.com/ar/dispute",
                "submenu": {
                    "نزاع المنشأت": {
                        "title": "نزاع المنشأت",
                        "description": "خدمة فض المنازعات بين المنشآت",
                        "link": "https://omalmisrservices.com/ar/dispute/facility"
                    },
                    "نزاع العمال": {
                        "title": "نزاع العمال",
                        "description": "خدمة فض المنازعات بين العمال والمنشآت",
                        "link": "https://omalmisrservices.com/ar/dispute/worker"
                    }
                }
            },
            "من نحن": {
                "title": "من نحن",
                "description": "الريادة في صناعة الخدمات محليًا وعالميًا للسوق الصناعي من خال توحيد باب الخدمة للمستثمر الصناعي باستخدام أحدث الأساليب والأدوات التكنولوجية وفقًا لاستراتيجية التنمية المستدامة العالمية ونشر الوعي بالثقافة الصناعية وأهميتها وزيادة الإنتاج مع التمسك بعقيدة عمل مؤسسة والنهوض بأعضائها ومستثمريها.",
                "link": "https://www.omalmisr.com/about",
                "submenu": {
                    "رؤيتنا": {
                        "title": "رؤيتنا",
                        "description": "نعمل برؤية مستدامة حتي تصبح منظومة عمال مصر كيان خدمي صناعي تعليمى زراعى يؤثر فى منظومة الاقتصاد الدولى وأن تقود عمال مصر أكبر تكتل صناعى ومحفظة إستثمارية صناعية هي الاولى من نوعها إفريقيا وع",
                        "link": "https://www.omalmisr.com/about"
                    },
                    "رسالتنا": {
                        "title": "الرسالة",
                        "description": "الريادة في صناعة الخدمات محليًا وعالميًا للسوق الصناعي من خال توحيد باب الخدمة للمستثمر الصناعي باستخدام أحدث الأساليب والأدوات التكنولوجية وفقًا لاستراتيجية التنمية المستدامة العالمية ونشر الوعي بالثقافة الصناعية وأهميتها وزيادة الإنتاج مع التمسك بعقيدة عمل مؤسسة والنهوض بأعضائها ومستثمريها.",
                        "link": "https://www.omalmisr.com/about"
                    },
                    "أهدافنا": {
                        "title": "اهدافنا",
                        "description": "توحيد باب الخدمة للمستثمر الصناعي. أن نكون البوابة الرائدة للمستثمرين الصناعيين والكوادر البشرية لدخولهم سوق العمل الصناعي. أن نصبح منظومة إقتصادية تؤثر في سوق العمل العالمي.",
                        "link": "https://www.omalmisr.com/about"
                    }
                }
            },
            "تواصل معنا": {
                "title": "تواصل معنا",
                "description": "تواصل مع مجمع عمال مصر",
                "link": "https://www.omalmisr.com/contact",
                "submenu": {
                    "السوشيال ميديا": {
                        "title": "تابعنا على السوشيال ميديا",
                        "description": "تابع صفحاتنا على منصات التواصل الاجتماعي",
                        "links": {
                            "يوتيوب": "https://www.youtube.com/channel/UCAkYTIf30ypaEE5gfrMhdUw",
                            "انستغرام": "https://www.instagram.com/omalmisr/",
                            "لينكد إن": "https://www.linkedin.com/company/79479037/admin/feed/posts/",
                            "تويتر": "https://twitter.com/omalmisr1",
                            "فيسبوك": "https://www.facebook.com/Omal.Misr.Foundation/"
                        }
                    }
                }
            }
        }
        
        logger.info(f"تم تهيئة ChatBot بنجاح. اسم الشات بوت: {self.bot_name}، ملف البيانات: {self.data_file}")
    
    def load_data(self) -> None:
        """
        تحميل البيانات من ملف JSON
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.prompts = data.get("prompts", [])
                self.human_expressions = data.get("human_expressions", {})
                self.contact_info = data.get("contact_info", {})
                self.requires_human_contact = data.get("requires_human_contact", [])
                self.user_categories = data.get("user_categories", [])
                self.job_sectors = data.get("job_sectors", [])
                self.personalize_response = data.get("personalize_response", self.personalize_response)
                
                # تحميل بيانات الخدمات والروابط
                self.service_links = data.get("service_links", {})
                self.service_categories = data.get("service_categories", {})
                
            logger.info(f"تم تحميل {len(self.prompts)} سؤال وجواب من قاعدة البيانات")
            
            if self.human_expressions:
                logger.info(f"تم تحميل تعبيرات بشرية لـ {len(self.human_expressions)} فئة مختلفة")
            
            if self.user_categories:
                logger.info(f"تم تحميل {len(self.user_categories)} فئة من المستخدمين")
            
            if self.service_links:
                logger.info(f"تم تحميل {len(self.service_links)} رابط لخدمات المجمع")
            
        except FileNotFoundError:
            error_msg = f"خطأ: لم يتم العثور على ملف البيانات '{self.data_file}'"
            logger.error(error_msg)
            print(error_msg)
        except json.JSONDecodeError:
            error_msg = f"خطأ: ملف البيانات '{self.data_file}' ليس بصيغة JSON صالحة"
            logger.error(error_msg)
            print(error_msg)
        except Exception as e:
            error_msg = f"خطأ غير متوقع أثناء تحميل البيانات: {e}"
            logger.error(error_msg)
            print(error_msg)
    
    def set_conversation_source(self, source: str) -> None:
        """
        تعيين مصدر المحادثة (ماسنجر أو تعليق فيسبوك)
        
        :param source: مصدر المحادثة ("messenger" أو "facebook_comment")
        """
        if source in ["messenger", "facebook_comment"]:
            self.conversation_source = source
            logger.debug(f"تم تعيين مصدر المحادثة: {source}")
        else:
            logger.warning(f"مصدر محادثة غير صالح: {source}. استخدام الافتراضي: messenger")
            self.conversation_source = "messenger"

    def _get_random_expression(self, category: str) -> str:
        """
        الحصول على تعبير عشوائي من فئة معينة
        
        :param category: فئة التعبير (greetings, positive_responses, إلخ)
        :return: تعبير عشوائي أو نص فارغ إذا لم تكن الفئة موجودة
        """
        expressions = self.human_expressions.get(category, [])
        
        if expressions and len(expressions) > 0:
            return random.choice(expressions)
        
        return ""

    def generate_menu_buttons(self, menu_type: str = "main", submenu_key: str = None) -> str:
        """
        توليد قائمة الأزرار لعرضها في المحادثة
        
        :param menu_type: نوع القائمة ("main" للقائمة الرئيسية أو "submenu" للقائمة الفرعية)
        :param submenu_key: مفتاح القائمة الفرعية المطلوبة (مثلاً "خدمات الشركات")
        :return: نص يحتوي على القائمة المطلوبة
        """
        menu_text = "🔍 اختر من الخدمات التالية:\n\n"
        
        if menu_type == "main":
            # عرض القائمة الرئيسية
            for key, item in self.main_menu.items():
                menu_text += f"▫️ {item['title']}\n"
                menu_text += f"  {item['description']}\n"
                menu_text += f"  {item['link']}\n\n"
            
            menu_text += "يمكنك اختيار أي من الخدمات أعلاه أو الاستفسار عنها بالتفصيل."
        
        elif menu_type == "submenu" and submenu_key and submenu_key in self.main_menu:
            menu_item = self.main_menu[submenu_key]
            if "submenu" in menu_item:
                menu_text = f"🔍 خدمات {menu_item['title']}:\n\n"
                for key, subitem in menu_item["submenu"].items():
                    menu_text += f"▫️ {subitem['title']}\n"
                    menu_text += f"  {subitem['description']}\n"
                    
                    if key == "السوشيال ميديا" and "links" in subitem:
                        menu_text += "  منصات التواصل الاجتماعي:\n"
                        for platform, link in subitem["links"].items():
                            menu_text += f"  - {platform}: {link}\n"
                    else:
                        menu_text += f"  {subitem['link']}\n"
                    
                    menu_text += "\n"
                
                menu_text += f"للعودة للقائمة الرئيسية، اكتب 'القائمة الرئيسية'."
        
        return menu_text
    
    def process_menu_request(self, user_message: str) -> Optional[str]:
        """
        معالجة طلبات المستخدم المتعلقة بالقوائم
        
        :param user_message: رسالة المستخدم
        :return: رد القائمة المطلوبة أو None إذا لم تكن الرسالة متعلقة بالقوائم
        """
        user_message = user_message.strip().lower()
        
        # طلب القائمة الرئيسية
        if user_message in ["القائمة", "القائمة الرئيسية", "الخدمات", "خدمات", "الخيارات", "قائمة", "menu", "services"]:
            return self.generate_menu_buttons(menu_type="main")
        
        # طلب قائمة فرعية
        for key, item in self.main_menu.items():
            if user_message in [key.lower(), item["title"].lower()]:
                if "submenu" in item:
                    return self.generate_menu_buttons(menu_type="submenu", submenu_key=key)
                else:
                    service_info = f"📋 {item['title']}\n\n{item['description']}\n\n🔗 الرابط: {item['link']}"
                    return service_info
        
        # البحث في القوائم الفرعية
        for main_key, main_item in self.main_menu.items():
            if "submenu" in main_item:
                for sub_key, sub_item in main_item["submenu"].items():
                    if user_message in [sub_key.lower(), sub_item["title"].lower()]:
                        service_info = f"📋 {sub_item['title']}\n\n{sub_item['description']}\n\n🔗 الرابط: {sub_item['link']}"
                        return service_info
        
        # البحث في القائمة باستخدام كلمات مفتاحية
        keywords_map = {
            "وظائف": "أبحث عن عمل",
            "توظيف": "أبحث عن عمل",
            "عمل": "أبحث عن عمل",
            "وظيفة": "أبحث عن عمل",
            "فرصة عمل": "أبحث عن عمل",
            "باحث عن عمل": "أبحث عن عمل",
            "سيرة ذاتية": "أبحث عن عمل",
            
            "موظفين": "أبحث عن موظفين وعمال",
            "عمال": "أبحث عن موظفين وعمال",
            "عمالة": "أبحث عن موظفين وعمال",
            "توفير عمال": "أبحث عن موظفين وعمال",
            
            "شركات": "خدمات الشركات",
            "استثمار": "خدمات الشركات",
            "فرص استثمارية": "خدمات الشركات",
            "جدوى": "خدمات الشركات",
            "منتجات": "خدمات الشركات",
            "خامات": "خدمات الشركات",
            "تسويق": "خدمات الشركات",
            "مالية": "خدمات الشركات",
            "قانونية": "خدمات الشركات",
            "تعليم": "خدمات الشركات",
            
            "نزاع": "بوابة فض المنازعات",
            "منازعات": "بوابة فض المنازعات",
            "مشكلة": "بوابة فض المنازعات",
            "تسوية": "بوابة فض المنازعات",
            "شكوى": "بوابة فض المنازعات",
            
            "تواصل": "تواصل معنا",
            "اتصل": "تواصل معنا",
            "هاتف": "تواصل معنا",
            "عنوان": "تواصل معنا",
            "سوشيال": "تواصل معنا",
            "فيسبوك": "تواصل معنا",
            "يوتيوب": "تواصل معنا",
            
            "معلومات": "من نحن",
            "من هم": "من نحن",
            "رؤية": "من نحن",
            "رسالة": "من نحن",
            "هدف": "من نحن",
            "أهداف": "من نحن"
        }
        
        # البحث عن كلمات مفتاحية في رسالة المستخدم
        for keyword, menu_key in keywords_map.items():
            if keyword in user_message:
                if menu_key in self.main_menu:
                    item = self.main_menu[menu_key]
                    if "submenu" in item:
                        return self.generate_menu_buttons(menu_type="submenu", submenu_key=menu_key)
                    else:
                        service_info = f"📋 {item['title']}\n\n{item['description']}\n\n🔗 الرابط: {item['link']}"
                        return service_info
        
        # لم يتم العثور على طلب قائمة
        return None

    def generate_messenger_response(self, user_id: str, message: str) -> str:
        """
        توليد رد للمستخدم عبر ماسنجر فيسبوك
        
        :param user_id: معرف المستخدم
        :param message: رسالة المستخدم
        :return: الرد المولد
        """
        self.set_conversation_source("messenger")
        
        # التحقق مما إذا كان المستخدم يطلب التحدث مع ممثل خدمة العملاء
        for keyword in self.customer_service_keywords:
            if keyword in message.lower():
                return self._generate_human_representative_response(user_id)
        
        # التحقق من طلبات القائمة
        menu_response = self.process_menu_request(message)
        if menu_response:
            logger.info(f"تم إرسال قائمة للمستخدم {user_id}")
            return menu_response
        
        # بناء المحادثة السابقة للمستخدم
        conversation_history = self._get_user_conversation_history(user_id)
        
        # إنشاء سياق المحادثة
        context = self._build_conversation_context(user_id, conversation_history)
        
        # توليد رد باستخدام DeepSeek API
        try:
            response = self.api.generate_response(message, context=context)
            
            # تنقية الرد من أي إشارات للذكاء الاصطناعي
            response = self._filter_ai_references(response)
            
            # إضافة عبارة استمرارية للمحادثة إذا كانت مفعلة
            if self.continue_conversation and random.random() < 0.7:  # 70% من الوقت
                response += f"\n\n{random.choice(self.continue_phrases)}"
            
            # تخزين المحادثة
            self._save_conversation(user_id, message, response)
            
            return response
            
        except Exception as e:
            error_msg = f"حدث خطأ أثناء توليد الرد: {str(e)}"
            logger.error(error_msg)
            
            # استخدام رد احتياطي
            fallback_response = """
أهلاً وسهلاً!

للأسف، هناك مشكلة في الاتصال بنظام الذكاء الاصطناعي. يمكنك التواصل معنا مباشرة على رقم الهاتف: 01012345678 أو عبر البريد الإلكتروني: info@omalmisrservices.com وسيقوم فريقنا بالرد على استفسارك في أقرب وقت.

سنتأكد من حل استفسارك بأسرع وقت!

هل ترغب في معرفة المزيد؟
            """
            return fallback_response
    
    def generate_comment_response(self, comment_id: str, comment_text: str, user_id: str = None) -> str:
        """
        توليد رد لتعليق على منشور فيسبوك
        
        :param comment_id: معرف التعليق
        :param comment_text: نص التعليق
        :param user_id: معرف المستخدم (اختياري)
        :return: الرد المولد
        """
        self.set_conversation_source("facebook_comment")
        
        # تحقق من نص التعليق للتأكد من أنه ليس ثناءً فقط
        praise_expressions = [
            "شكرا", "جزاكم الله خيرا", "ما شاء الله", "رائع", "تمام", "جميل", "احسنتم", 
            "تسلم", "بارك الله فيكم", "جزاكم الله", "thank", "thanks", "❤"
        ]
        
        # فحص إذا كان التعليق مجرد ثناء ولا يحتاج إلى رد
        if len(comment_text.strip().split()) <= 3:  # تعليق قصير جداً
            is_praise_only = False
            for expr in praise_expressions:
                if expr in comment_text.lower():
                    is_praise_only = True
                    break
                    
            if is_praise_only:
                logger.info(f"تم تجاهل تعليق ثناء قصير: {comment_text}")
                return "IGNORE_PRAISE_COMMENT"
        
        # التحقق من طلبات القائمة
        menu_response = self.process_menu_request(comment_text)
        if menu_response:
            logger.info(f"تم إرسال قائمة لتعليق {comment_id}")
            return menu_response
        
        # إنشاء سياق محادثة محدود لتعليقات الفيسبوك
        context = f"""أنت 'محمد سلامة'، المساعد الرسمي لمجمع عمال مصر. تقوم بالرد على تعليقات الفيسبوك بأسلوب ودود واحترافي.
مهمتك هي فهم استفسار العميل وتوجيهه للخدمة المناسبة من خدمات مجمع عمال مصر.

معلومات مهمة:
- لا تذكر أبداً أنك ذكاء اصطناعي، بل اظهر نفسك كممثل خدمة عملاء محترف.
- كن مختصراً في ردودك على التعليقات (2-4 أسطر بحد أقصى).
- قدم رابط صفحة الخدمة المناسبة عند الرد.
- شجع المستخدم على طلب المزيد من المعلومات في نهاية الرد.
- تعامل بأسلوب رسمي لكن ودود مع المستفسرين.

استفسار المستخدم في تعليق على فيسبوك: {comment_text}
"""
        
        # توليد رد باستخدام DeepSeek API
        try:
            response = self.api.generate_response(comment_text, context=context)
            
            # تنقية الرد من أي إشارات للذكاء الاصطناعي
            response = self._filter_ai_references(response)
            
            # اختصار الرد للتعليقات حتى لا يكون طويلاً
            if len(response.split()) > 80:  # إذا كان الرد طويلاً جداً
                # محاولة تقصير الرد مع الحفاظ على الروابط والمعلومات المهمة
                lines = response.split("\n")
                shortened_response = []
                link_found = False
                
                for line in lines:
                    if "http" in line and not link_found:
                        shortened_response.append(line)
                        link_found = True
                    elif len(shortened_response) < 4 and len(line.strip()) > 0:
                        shortened_response.append(line)
                
                # إضافة عبارة تشجيع في النهاية
                shortened_response.append("\nهل لديك أسئلة أخرى؟")
                response = "\n".join(shortened_response)
            
            logger.info(f"تم توليد رد لتعليق {comment_id}: {response[:50]}...")
            return response
            
        except Exception as e:
            error_msg = f"حدث خطأ أثناء توليد الرد لتعليق {comment_id}: {str(e)}"
            logger.error(error_msg)
            
            # استخدام رد احتياطي
            with open('facebook_responses.json', 'r', encoding='utf-8') as f:
                fallback_responses = json.load(f)
            
            default_response = """
أهلاً وسهلاً!

للأسف، هناك مشكلة في الاتصال بنظام الذكاء الاصطناعي. يمكنك التواصل معنا مباشرة على رقم الهاتف: 01012345678 أو عبر البريد الإلكتروني: info@omalmisrservices.com وسيقوم فريقنا بالرد على استفسارك في أقرب وقت.

سنتأكد من حل استفسارك بأسرع وقت!

هل ترغب في معرفة المزيد؟
            """
            
            # البحث عن رد احتياطي مناسب
            for response in fallback_responses:
                if response.get("comment_id") == "comment4":  # رد الخطأ الافتراضي
                    return response.get("response", default_response)
            
            return default_response
    
    def _filter_ai_references(self, text: str) -> str:
        """
        تنقية النص من أي إشارات للذكاء الاصطناعي
        
        :param text: النص المراد تنقيته
        :return: النص بعد التنقية
        """
        ai_references = [
            "كنموذج للذكاء الاصطناعي", "كذكاء اصطناعي", "كمساعد ذكاء اصطناعي",
            "نموذج لغوي", "نموذج لغة كبير", "ذكاء اصطناعي", "deepseek", "deep seek",
            "ai assistant", "ai model", "language model", "gpt", "llm", "ذكاء الاصطناعي",
            "artificial intelligence", "ai", "تم تطويري", "as an ai", "كمساعد افتراضي"
        ]
        
        # استبدال الإشارات بتعبيرات بديلة
        replacements = {
            "كنموذج للذكاء الاصطناعي": "كمساعد لخدمة العملاء",
            "كذكاء اصطناعي": "كمساعد لخدمة العملاء",
            "كمساعد ذكاء اصطناعي": "كمساعد لخدمة العملاء",
            "نموذج لغوي": "مساعد خدمة العملاء",
            "نموذج لغة كبير": "مساعد خدمة العملاء",
            "ذكاء اصطناعي": "مساعد خدمة العملاء",
            "deepseek": "مجمع عمال مصر",
            "deep seek": "مجمع عمال مصر",
            "ai assistant": "مساعد خدمة العملاء",
            "ai model": "مساعد خدمة العملاء",
            "language model": "مساعد خدمة العملاء",
            "gpt": "مساعد خدمة العملاء",
            "llm": "مساعد خدمة العملاء",
            "ذكاء الاصطناعي": "فريق خدمة العملاء",
            "artificial intelligence": "فريق خدمة العملاء",
            "ai": "مساعد",
            "تم تطويري": "تم تدريبي",
            "as an ai": "كمساعد لخدمة العملاء",
            "كمساعد افتراضي": "كمساعد لخدمة العملاء"
        }
        
        filtered_text = text
        for ref, replacement in replacements.items():
            filtered_text = re.sub(re.escape(ref), replacement, filtered_text, flags=re.IGNORECASE)
        
        # تنقية العبارات التي تبدأ بـ "أنا مساعد" أو "أنا لست"
        statements_to_remove = [
            r"أنا مساعد ذكاء اصطناعي.*?\.",
            r"أنا لست إنسانًا حقيقيًا.*?\.",
            r"I'm an AI.*?\.",
            r"I am an AI.*?\.",
            r"As an AI.*?\.",
            r"كنموذج ذكاء اصطناعي.*?\.",
        ]
        
        for statement in statements_to_remove:
            filtered_text = re.sub(statement, "", filtered_text, flags=re.IGNORECASE | re.DOTALL)
        
        return filtered_text.strip()
    
    def _build_conversation_context(self, user_id: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        بناء سياق المحادثة للمستخدم
        
        :param user_id: معرف المستخدم
        :param conversation_history: تاريخ المحادثة مع المستخدم
        :return: نص السياق المبني
        """
        # الاسم المستعار للمستخدم إذا كان موجوداً في حالة المحادثة
        user_name = self.conversation_state.get(user_id, {}).get('user_name', 'عزيزي الزائر')
        
        # بناء سياق المحادثة
        context = f"""أنت 'محمد سلامة'، المساعد الرسمي لمجمع عمال مصر. تتحدث مع {user_name} على ماسنجر فيسبوك.
مهمتك هي فهم احتياجات العميل وتوجيهه للخدمة المناسبة من خدمات مجمع عمال مصر.

معلومات مهمة:
- لا تذكر أبداً أنك ذكاء اصطناعي، بل اظهر نفسك كممثل خدمة عملاء محترف.
- كن ودوداً ومهنياً في ردودك.
- شجع المستخدم على طلب المزيد من المعلومات عند الاقتضاء.
- تجنب الكتابة بطريقة رسمية جداً، اكتب بشكل طبيعي مثل شخص حقيقي.
- تأكد من إعطاء رابط الخدمة المناسبة عند الإجابة.
- لا تستخدم مصطلحات أجنبية إذا كانت لها بديل عربي شائع.

الخدمات الرئيسية لمجمع عمال مصر:
1. بوابة التوظيف للباحثين عن عمل: https://omalmisrservices.com/ar/jobs
2. بوابة توفير الموظفين للشركات: https://omalmisrservices.com/ar/workers
3. خدمات الشركات والمستثمرين: https://omalmisrservices.com/ar/companies
4. بوابة فض وتسوية المنازعات: https://omalmisrservices.com/ar/dispute

"""
        
        # إضافة تاريخ المحادثة إذا كان موجوداً
        if conversation_history:
            context += "\nتاريخ المحادثة السابق:\n"
            for i, exchange in enumerate(conversation_history[-5:]):  # آخر 5 تبادلات فقط
                context += f"المستخدم: {exchange.get('user_message', '')}\n"
                context += f"محمد سلامة: {exchange.get('bot_response', '')}\n"
        
        return context
    
    def _get_user_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """
        الحصول على تاريخ المحادثة لمستخدم معين
        
        :param user_id: معرف المستخدم
        :return: قائمة بمحادثات المستخدم السابقة
        """
        return self.conversation_history.get(user_id, [])
    
    def _save_conversation(self, user_id: str, user_message: str, bot_response: str) -> None:
        """
        حفظ المحادثة في تاريخ المحادثات
        
        :param user_id: معرف المستخدم
        :param user_message: رسالة المستخدم
        :param bot_response: رد البوت
        """
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # إضافة المحادثة الحالية إلى تاريخ المحادثات
        self.conversation_history[user_id].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'user_message': user_message,
            'bot_response': bot_response,
            'source': self.conversation_source
        })
        
        # حفظ المحادثات في ملف إذا كان التخزين مفعل
        if BOT_SETTINGS.get("SAVE_CONVERSATIONS", True):
            self._save_conversation_to_file(user_id)
    
    def _save_conversation_to_file(self, user_id: str) -> None:
        """
        حفظ محادثة المستخدم في ملف JSON
        
        :param user_id: معرف المستخدم
        """
        if not BOT_SETTINGS.get("SAVE_CONVERSATIONS", True):
            return
        
        try:
            # إنشاء مجلد للمحادثات إذا لم يكن موجوداً
            conversations_dir = BOT_SETTINGS.get("CONVERSATIONS_DIR", "conversations")
            os.makedirs(conversations_dir, exist_ok=True)
            
            # اسم الملف يعتمد على مصدر المحادثة
            filename_prefix = "messenger_" if self.conversation_source == "messenger" else "facebook_comment_"
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # استخدام اختصار معرف المستخدم
            user_id_short = user_id[-8:] if len(user_id) > 8 else user_id
            
            filename = f"{conversations_dir}/{filename_prefix}{user_id_short}_{current_time}.json"
            
            # تنسيق البيانات للحفظ
            conversation_data = {
                'user_id': user_id,
                'source': self.conversation_source,
                'timestamp': datetime.datetime.now().isoformat(),
                'conversation': self.conversation_history[user_id]
            }
            
            # يمكن إضافة بيانات إضافية لتعليقات الفيسبوك
            if self.conversation_source == "facebook_comment":
                conversation_data['platform'] = "facebook"
                conversation_data['type'] = "comment"
            
            # حفظ البيانات في ملف JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"تم حفظ المحادثة في الملف: {filename}")
            
        except Exception as e:
            logger.error(f"خطأ أثناء حفظ المحادثة للمستخدم {user_id}: {str(e)}")
    
    def _generate_human_representative_response(self, user_id: str) -> str:
        """
        توليد رد لطلب التواصل مع ممثل خدمة العملاء البشري
        
        :param user_id: معرف المستخدم
        :return: رد بمعلومات الاتصال بممثل خدمة العملاء
        """
        # تكوين نص الرد
        greeting = self._get_random_expression("greetings")
        if not greeting:
            greeting = "مرحباً بك!"
        
        user_name = self.conversation_state.get(user_id, {}).get('user_name', 'عزيزي العميل')
        
        response = f"{greeting} {user_name},\n\n"
        response += "سيتم تحويلك للتواصل مع أحد ممثلي خدمة العملاء.\n\n"
        
        rep_name = self.human_rep_contact_info.get("name", "محمد سلامة")
        rep_title = self.human_rep_contact_info.get("title", "مدير خدمة العملاء - مجمع عمال مصر")
        
        response += f"معلومات التواصل مع {rep_name}:\n"
        
        if "phone" in self.human_rep_contact_info:
            response += f"📞 هاتف: {self.human_rep_contact_info['phone']}\n"
        
        if "email" in self.human_rep_contact_info:
            response += f"📧 بريد إلكتروني: {self.human_rep_contact_info['email']}\n"
        
        if "whatsapp" in self.human_rep_contact_info:
            response += f"📱 واتساب: {self.human_rep_contact_info['whatsapp']}\n"
        
        if "messenger" in self.human_rep_contact_info:
            response += f"💬 ماسنجر: {self.human_rep_contact_info['messenger']}\n"
        
        response += f"\nسيقوم {rep_name} ({rep_title}) بالرد عليك في أقرب وقت ممكن، عادةً خلال ساعات العمل (9 صباحاً - 5 مساءً).\n\n"
        response += "نشكرك على تواصلك مع مجمع عمال مصر."
        
        return response

# تعريف دالة رئيسية لاختبار الشات بوت
def test_chatbot():
    """اختبار الشات بوت في وضع سطر الأوامر"""
    chatbot = ChatBot()
    print("مرحباً بك في شات بوت مجمع عمال مصر!")
    print("اكتب 'خروج' للخروج من المحادثة.")
    
    user_id = f"test_user_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    while True:
        user_input = input("\nأنت: ")
        if user_input.lower() in ["خروج", "exit", "quit"]:
            print("شكراً لاستخدامك شات بوت مجمع عمال مصر. إلى اللقاء!")
            break
        
        response = chatbot.generate_messenger_response(user_id, user_input)
        print(f"\n{chatbot.bot_name}: {response}")

# تشغيل الاختبار عند تشغيل هذا الملف مباشرة
if __name__ == "__main__":
    test_chatbot()