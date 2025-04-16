"""
محاكاة استجابة API بدون الاتصال بالخدمة الخارجية
يستخدم لتوليد ردود محلية عندما يكون الاتصال بالخدمة الخارجية غير متاح
"""

import random
import json
import logging
from typing import Dict, Any, List

# إعداد التسجيل
logger = logging.getLogger(__name__)

class LocalResponseGenerator:
    """
    مولد استجابات محلي يستخدم عندما يفشل الاتصال بـ API
    """
    
    def __init__(self, data_file: str = "data.json"):
        """
        تهيئة مولد الاستجابات المحلي
        
        :param data_file: ملف البيانات المحلي
        """
        self.data_file = data_file
        self.knowledge_base = []
        self.greetings = []
        self.job_responses = []
        self.investor_responses = []
        self.general_responses = []
        self.contact_info = {}
        
        # تحميل البيانات
        self._load_data()
        
        logger.info("تم تهيئة مولد الاستجابات المحلي بنجاح")
    
    def _load_data(self):
        """تحميل البيانات من ملف JSON"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # تحميل قاعدة المعرفة
                self.knowledge_base = data.get("prompts", [])
                
                # تحميل التعبيرات البشرية
                expressions = data.get("human_expressions", {})
                self.greetings = expressions.get("greetings", [])
                self.job_responses = expressions.get("job_seekers_response", [])
                self.investor_responses = expressions.get("investors_response", [])
                
                # تحميل معلومات الاتصال
                self.contact_info = data.get("contact_info", {})
                
                # إنشاء ردود عامة افتراضية إذا لم تكن موجودة
                self._create_default_responses()
                
            logger.info(f"تم تحميل {len(self.knowledge_base)} عنصر من قاعدة المعرفة بنجاح")
        except Exception as e:
            logger.error(f"خطأ في تحميل ملف البيانات: {e}")
            # إنشاء ردود افتراضية في حالة الفشل
            self._create_default_responses()
    
    def _create_default_responses(self):
        """إنشاء ردود افتراضية للاستخدام عند الحاجة"""
        # الترحيبات الافتراضية
        if not self.greetings:
            self.greetings = [
                "أهلاً وسهلاً!",
                "مرحباً بك!",
                "يسعدنا تواصلك معنا!",
                "شكراً لتواصلك مع مجمع عمال مصر!",
                "أهلاً بك في خدمة عملاء مجمع عمال مصر!"
            ]
        
        # ردود الباحثين عن عمل
        if not self.job_responses:
            self.job_responses = [
                "يسعدنا اهتمامك بالالتحاق بفرص العمل لدينا!",
                "نرحب بك للانضمام لفريق العمل في مجمع عمال مصر!",
                "نحن دائماً نبحث عن الكفاءات المتميزة للعمل معنا!",
                "فرص العمل متنوعة في مجمع عمال مصر لمختلف التخصصات!"
            ]
        
        # ردود المستثمرين
        if not self.investor_responses:
            self.investor_responses = [
                "نقدم للمستثمرين كل سبل الدعم لإنجاح مشروعاتهم!",
                "مجمع عمال مصر يرحب بالمستثمرين الراغبين في تطوير أعمالهم!",
                "نسعى دائماً لتوفير بيئة استثمارية مناسبة لشركائنا!",
                "الاستثمار في مجمع عمال مصر فرصة للنمو والتوسع!"
            ]
        
        # ردود عامة
        self.general_responses = [
            "مجمع عمال مصر هو منظومة صناعية واقتصادية بدأت عام 2010 برؤية وطنية، وتطورت لتصبح شركة مساهمة مصرية بقيمة سوقية تتجاوز 1.5 مليار جنيه مصري.",
            "يقوم المجمع بإدارة وتشغيل المنشآت الصناعية من خلال توفير وتدريب الكوادر البشرية، وتقديم خدمات للمستثمرين، وتنفيذ مشروعات صناعية متنوعة.",
            "يرأس مجمع عمال مصر المهندس هيثم حسين حلم، المؤسس والرئيس التنفيذي للمجمع.",
            "نهتم في مجمع عمال مصر بتحقيق التنمية المستدامة من خلال توفير فرص عمل وتدريب للشباب، ودعم المستثمرين والشركات."
        ]
        
        # معلومات الاتصال الافتراضية
        if not self.contact_info:
            self.contact_info = {
                "phone": "01100901200",
                "email": "info@omalmisr.com",
                "website": "www.omalmisr.com"
            }

    def generate_response(self, user_message: str, user_category: str = "", user_name: str = "") -> str:
        """
        توليد رد محلي بناءً على رسالة المستخدم وفئته
        
        :param user_message: رسالة المستخدم
        :param user_category: فئة المستخدم (باحث عن عمل، مستثمر، إلخ)
        :param user_name: اسم المستخدم (اختياري)
        :return: الرد المولد
        """
        # البحث عن كلمات مفتاحية في رسالة المستخدم
        message_lower = user_message.lower()
        
        # تحديد نوع الرد المناسب
        if any(keyword in message_lower for keyword in ["وظيفة", "عمل", "توظيف", "شغل"]):
            return self._generate_job_response(user_name)
        
        elif any(keyword in message_lower for keyword in ["استثمار", "مشروع", "شراكة", "فرصة"]):
            return self._generate_investor_response(user_name)
        
        elif any(keyword in message_lower for keyword in ["من هو", "مين", "المؤسس", "هيثم", "المدير"]):
            return self._generate_about_founder_response(user_name)
        
        elif any(keyword in message_lower for keyword in ["من انتم", "ايه", "مجمع", "شركة", "منظمة"]):
            return self._generate_about_company_response(user_name)
        
        # في حال عدم تطابق الكلمات المفتاحية، عد رد عام
        return self._generate_general_response(user_name)
    
    def _generate_job_response(self, user_name: str = "") -> str:
        """توليد رد للباحثين عن عمل"""
        greeting = f"{random.choice(self.job_responses)}\n\n"
        
        name_greeting = f"أهلاً بك{' يا ' + user_name if user_name else ''}! "
        
        content = """
نحن في *مجمع عمال مصر* نوفر فرص عمل متنوعة في عدة قطاعات، منها:

1️⃣ قطاع *الصناعات الغذائية*
2️⃣ قطاع *الملابس والنسيج*
3️⃣ قطاع *خدمات البترول*
4️⃣ قطاع *الثروة الداجنة* (مشروع دواجن مصر)
5️⃣ قطاع *الخدمات الإدارية والدعم الفني*

يمكنك التقديم للوظائف من خلال:
✅ إرسال سيرتك الذاتية على البريد الإلكتروني: jobs@omalmisr.com
✅ زيارة مقر المجمع وملء استمارة التقديم
✅ التسجيل عبر موقعنا الإلكتروني: www.omalmisr.com/jobs

تصل المرتبات في بعض القطاعات إلى 7000 جنيه شهرياً، مع توفير مزايا أخرى مثل التأمين الصحي والاجتماعي.
"""
        
        contact = f"""
• *للتواصل المباشر*:
📞 تليفون/واتساب: {self.contact_info.get('phone', '01100901200')}
✉️ بريد إلكتروني: {self.contact_info.get('email', 'info@omalmisr.com')}
🌐 الموقع الرسمي: [www.omalmisr.com](https://{self.contact_info.get('website', 'www.omalmisr.com')})
"""

        # روابط سريعة
        quick_links = """
• *روابط سريعة قد تهمك*:
🔗 [رابط التسجيل للوظائف](https://omalmisrservices.com/en/jobs) - سجل الآن مباشرة للتقدم للوظائف المتاحة
"""
        
        # سؤال للمتابعة
        follow_up = random.choice([
            "هل يمكنني مساعدتك بمعلومات إضافية عن الوظائف المتاحة؟",
            "هل لديك خبرة سابقة في أي من مجالات عملنا؟",
            "هل تبحث عن وظيفة في تخصص معين؟ أستطيع مساعدتك."
        ])
        
        return greeting + name_greeting + content + contact + quick_links + "\n\n" + follow_up
    
    def _generate_investor_response(self, user_name: str = "") -> str:
        """توليد رد للمستثمرين"""
        greeting = f"{random.choice(self.investor_responses)}\n\n"
        
        name_greeting = f"أهلاً وسهلاً بك{' يا ' + user_name if user_name else ''}! "
        
        content = """
نحن في *مجمع عمال مصر* بنقدم دعم كامل للمستثمرين ورجال الأعمال، علشان نسهل عليك تنفيذ مشروعاتك الصناعية والاستثمارية بنجاح.

• *خدمات متكاملة للمستثمرين*:
✅ *تأسيس وإدارة المشروعات*: من التخطيط حتى التشغيل.
✅ *توفير الكوادر المدربة*: عمالة مؤهلة بمعايير عالمية.
✅ *شراكات استراتيجية*: مع جهات محلية ودولية لضمان نجاح المشروع.
✅ *مشروعات مربحة*: زي *مشروع دواجن مصر* (مدينة الثروة الداجنة) اللي بيحقق عائد استثمار يصل لـ *39% سنوياً*!

يمكننا ترتيب لقاء معك لمناقشة الفرص الاستثمارية المتاحة وتقديم دراسة جدوى واضحة لأي مشروع.
"""
        
        contact = f"""
• *للتواصل المباشر*:
📞 تليفون/واتساب: {self.contact_info.get('phone', '01100901200')}
✉️ بريد إلكتروني: {self.contact_info.get('email', 'info@omalmisr.com')}
🌐 الموقع الرسمي: [www.omalmisr.com](https://{self.contact_info.get('website', 'www.omalmisr.com')})
"""

        # روابط سريعة
        quick_links = """
• *روابط سريعة قد تهمك*:
🔗 [خدمات المستثمرين](https://omalmisrservices.com/en/companies) - تعرف على الفرص الاستثمارية وخدمات الشركات
"""
        
        # سؤال للمتابعة
        follow_up = random.choice([
            "هل تهتم بقطاع صناعي محدد؟",
            "هل لديك استفسار عن أي من الفرص الاستثمارية لدينا؟",
            "هل ترغب في معرفة المزيد عن عائد الاستثمار في مشاريعنا؟"
        ])
        
        return greeting + name_greeting + content + contact + quick_links + "\n\n" + follow_up
    
    def _generate_about_founder_response(self, user_name: str = "") -> str:
        """توليد رد عن مؤسس المجمع"""
        greeting = f"{random.choice(self.greetings)}\n\n"
        
        name_greeting = f"أهلاً {user_name if user_name else ''}! "
        
        content = """
المهندس هيثم حسين هو المؤسس والرئيس التنفيذي ل*مجمع عمال مصر*، وهو قائد صناعي ورجل أعمال متميز قاد المنظومة منذ تأسيسها عام 2010 وحتى أصبحت شركة مساهمة مصرية كبرى بقيمة سوقية تتجاوز 1.5 مليار جنيه مصري.

• *أبرز أدواره وإنجازاته*:
✅ قيادة تطوير مجمع عمال مصر ليشمل مشروعات صناعية متنوعة مثل *دواجن مصر، مصانع الملابس، والصناعات الغذائية*.
✅ بناء شراكات محلية ودولية لتعزيز الاقتصاد المصري وتوفير فرص عمل.
✅ الاهتمام بتدريب وتأهيل الكوادر البشرية لرفع كفاءة القطاع الصناعي.

يحمل رؤية وطنية واضحة لتطوير الصناعة المصرية ودعم المستثمرين والعمال على حد سواء.
"""
        
        contact = f"""
• *للتواصل مع مجمع عمال مصر*:
📞 تليفون/واتساب: {self.contact_info.get('phone', '01100901200')}
✉️ بريد إلكتروني: {self.contact_info.get('email', 'info@omalmisr.com')}
🌐 الموقع الرسمي: [www.omalmisr.com](https://{self.contact_info.get('website', 'www.omalmisr.com')})
"""
        
        # سؤال للمتابعة
        follow_up = random.choice([
            "هل تحتاج لمعلومات إضافية عن المهندس هيثم أو مجمع عمال مصر؟",
            "هل ترغب في معرفة المزيد عن أنشطة المجمع وإنجازاته؟",
            "هل يمكنني مساعدتك بأي معلومات أخرى؟"
        ])
        
        return greeting + name_greeting + content + contact + "\n\n" + follow_up
    
    def _generate_about_company_response(self, user_name: str = "") -> str:
        """توليد رد عن الشركة"""
        greeting = f"{random.choice(self.greetings)}\n\n"
        
        name_greeting = f"مرحباً{' ' + user_name if user_name else ''}! "
        
        content = """
*مجمع عمال مصر* هو منظومة صناعية واقتصادية بدأت عام 2010 برؤية وطنية، تطوّرت لتصبح شركة مساهمة مصرية بقيمة سوقية تتجاوز 1.5 مليار جنيه مصري.

• *تقوم المنظومة بإدارة وتشغيل المنشآت الصناعية من خلال*:
1️⃣ توفير وتدريب وتأهيل الكوادر البشرية للعمل بالأنشطة المختلفة.
2️⃣ خدمات للمستثمرين وأصحاب المصانع لمساعدتهم على تنفيذ مشاريعهم.
3️⃣ تنفيذ مشروعات صناعية متنوعة مثل مشروع دواجن مصر، ومصانع الملابس، والصناعات الغذائية.
4️⃣ عقد شراكات محلية ودولية لتعزيز الاقتصاد المصري.

يرأس المجمع المهندس هيثم حسين حلم (المؤسس والرئيس التنفيذي).
"""
        
        contact = f"""
• *للتواصل معنا*:
📞 تليفون/واتساب: {self.contact_info.get('phone', '01100901200')}
✉️ بريد إلكتروني: {self.contact_info.get('email', 'info@omalmisr.com')}
🌐 الموقع الرسمي: [www.omalmisr.com](https://{self.contact_info.get('website', 'www.omalmisr.com')})
"""
        
        # سؤال للمتابعة
        follow_up = random.choice([
            "كيف يمكنني مساعدتك اليوم؟",
            "هل لديك استفسار محدد عن أنشطة المجمع؟",
            "هل ترغب في معرفة المزيد عن خدماتنا؟"
        ])
        
        return greeting + name_greeting + content + contact + "\n\n" + follow_up
    
    def _generate_general_response(self, user_name: str = "") -> str:
        """توليد رد عام"""
        greeting = f"{random.choice(self.greetings)}\n\n"
        
        name_greeting = f"أهلاً{' ' + user_name if user_name else ''}! "
        
        content = random.choice(self.general_responses) + "\n\n"
        content += """
• *خدماتنا الرئيسية*:
✅ توفير فرص عمل للباحثين عن عمل في قطاعات مختلفة.
✅ تقديم خدمات استثمارية للمستثمرين وأصحاب المشاريع.
✅ توفير عمالة مدربة للشركات والمصانع.
✅ تنفيذ مشروعات صناعية متنوعة.
✅ التدريب المهني وتأهيل الكوادر البشرية.

يمكنك زيارة موقعنا الإلكتروني للاطلاع على كافة الخدمات والمشروعات.
"""
        
        contact = f"""
• *للتواصل المباشر*:
📞 تليفون/واتساب: {self.contact_info.get('phone', '01100901200')}
✉️ بريد إلكتروني: {self.contact_info.get('email', 'info@omalmisr.com')}
🌐 الموقع الرسمي: [www.omalmisr.com](https://{self.contact_info.get('website', 'www.omalmisr.com')})
"""
        
        # روابط سريعة
        quick_links = """
• *روابط سريعة قد تهمك*:
🔗 [رابط التسجيل للوظائف](https://omalmisrservices.com/en/jobs) - سجل الآن للتقدم للوظائف المتاحة
🔗 [خدمات المستثمرين](https://omalmisrservices.com/en/companies) - الفرص الاستثمارية وخدمات الشركات
🔗 [توفير العمالة](https://omalmisrservices.com/en/workers) - للشركات الباحثة عن عمالة مدربة
"""
        
        # سؤال للمتابعة
        follow_up = random.choice([
            "كيف يمكننا مساعدتك اليوم؟",
            "هل هناك خدمة محددة تبحث عنها؟",
            "هل تود معرفة المزيد عن أي من خدماتنا؟"
        ])
        
        return greeting + name_greeting + content + contact + quick_links + "\n\n" + follow_up