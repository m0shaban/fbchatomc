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
                    # إذا لم يكن هناك قائمة فرعية، أعد معلومات عن الخدمة نفسها
                    response = f"📌 {item['title']}\n\n"
                    response += f"{item['description']}\n\n"
                    response += f"للتسجيل: {item['link']}\n\n"
                    response += "للعودة للقائمة الرئيسية، اكتب 'القائمة الرئيسية'."
                    return response
        
        # البحث في القوائم الفرعية
        for main_key, main_item in self.main_menu.items():
            if "submenu" in main_item:
                for sub_key, sub_item in main_item["submenu"].items():
                    if user_message in [sub_key.lower(), sub_item["title"].lower()]:
                        response = f"📌 {sub_item['title']}\n\n"
                        response += f"{sub_item['description']}\n\n"
                        
                        if "links" in sub_item:
                            response += "روابط منصات التواصل الاجتماعي:\n"
                            for platform, link in sub_item["links"].items():
                                response += f"- {platform}: {link}\n"
                        else:
                            response += f"للتسجيل: {sub_item['link']}\n\n"
                        
                        response += f"\nللعودة لقائمة {main_item['title']}، اكتب '{main_item['title']}'.\n"
                        response += "للعودة للقائمة الرئيسية، اكتب 'القائمة الرئيسية'."
                        return response
        
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
                    # إذا كانت كلمة مفتاحية لقائمة رئيسية
                    if "submenu" in self.main_menu[menu_key]:
                        return self.generate_menu_buttons(menu_type="submenu", submenu_key=menu_key)
                    else:
                        item = self.main_menu[menu_key]
                        response = f"📌 {item['title']}\n\n"
                        response += f"{item['description']}\n\n"
                        response += f"للتسجيل: {item['link']}\n\n"
                        response += "للعودة للقائمة الرئيسية، اكتب 'القائمة الرئيسية'."
                        return response
        
        # لم يتم العثور على طلب قائمة
        return None

    def _detect_user_category(self, message: str) -> str:
        """
        محاولة تحديد فئة المستخدم من رسالته
        
        :param message: رسالة المستخدم
        :return: فئة المستخدم المحتملة
        """
        message = message.lower()
        
        # كلمات مفتاحية للباحثين عن عمل
        job_seekers_keywords = [
            "وظيفة", "عمل", "توظيف", "شغل", "مرتب", "راتب", "تقديم", "سيرة ذاتية", 
            "خبرة", "خريج", "تدريب", "تعيين", "مؤهل", "cv", "فرصة"
        ]
        
        # كلمات مفتاحية للمستثمرين
        investors_keywords = [
            "استثمار", "مشروع", "تمويل", "شراكة", "رأس مال", "ربح", "عائد", "فرصة استثمارية",
            "تعاون", "رجل أعمال", "مستثمر", "مشروع"
        ]
        
        # كلمات مفتاحية للصحفيين
        media_keywords = [
            "صحفي", "إعلام", "مقابلة", "تصريح", "خبر", "تقرير", "مجلة", "جريدة", "تلفزيون", 
            "راديو", "إذاعة", "تغطية", "صحافة", "نشر", "مقال"
        ]
        
        # كلمات مفتاحية للشركات والجهات
        companies_keywords = [
            "شركة", "مؤسسة", "جهة", "مصنع", "تعاون", "شراكة", "تفاهم", "بروتوكول", 
            "اتفاقية", "مذكرة", "تنسيق", "جامعة", "معهد", "مدرسة"
        ]
        
        # البحث عن الكلمات المفتاحية في الرسالة
        for keyword in job_seekers_keywords:
            if keyword in message:
                logger.debug(f"تم تصنيف المستخدم كـ 'باحث عن عمل' بناءً على الكلمة المفتاحية: {keyword}")
                return "باحث عن عمل"
        
        for keyword in investors_keywords:
            if keyword in message:
                logger.debug(f"تم تصنيف المستخدم كـ 'مستثمر' بناءً على الكلمة المفتاحية: {keyword}")
                return "مستثمر"
        
        for keyword in media_keywords:
            if keyword in message:
                logger.debug(f"تم تصنيف المستخدم كـ 'صحفي' بناءً على الكلمة المفتاحية: {keyword}")
                return "صحفي"
        
        for keyword in companies_keywords:
            if keyword in message:
                logger.debug(f"تم تصنيف المستخدم كـ 'شركة' بناءً على الكلمة المفتاحية: {keyword}")
                return "شركة"
        
        # إذا لم يتم تحديد الفئة، أعد فئة افتراضية
        logger.debug("لم يتم تحديد فئة محددة للمستخدم")
        return ""