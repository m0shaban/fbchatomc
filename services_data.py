"""
ملف بيانات خدمات شركة مجمع عمال مصر
يحتوي على قوائم الخدمات والروابط الخاصة بكل خدمة
"""

# القائمة الرئيسية للخدمات
MAIN_SERVICES = [
    {
        "id": "find_job",
        "title": "أبحث عن عمل",
        "description": "سجل معنا لتجد وظيفتك المناسبة",
        "url": "https://omalmisrservices.com/ar/jobs",
        "icon": "💼"
    },
    {
        "id": "find_workers",
        "title": "أبحث عن موظفين و عمال",
        "description": "سجل بياناتك للحصول على موظفيين",
        "url": "https://omalmisrservices.com/ar/workers",
        "icon": "👥"
    },
    {
        "id": "company_services",
        "title": "خدمات الشركات",
        "description": "خدمات الاسثمار الصناعي و الزراعي",
        "url": "https://omalmisrservices.com/ar/companies",
        "icon": "🏢"
    },
    {
        "id": "dispute_resolution",
        "title": "بوابة فض و تسوية المنازاعات",
        "description": "هي بوابة إلكترنية لفض و تسوية المنازاعات الناتجية بين مؤسستين أو أكثر أو بين المؤسسات و العاملين بها بوسطة خبراء و مستشارين قانونين متخصصين دون اللجوء إلى الجهات القضائية",
        "url": "https://omalmisrservices.com/ar/dispute",
        "icon": "⚖️"
    }
]

# الخدمات الفرعية تحت كل قسم رئيسي

# خدمات "أبحث عن عمل"
FIND_JOB_SERVICES = [
    {
        "id": "job_registration",
        "title": "تسجيل للبحث عن عمل",
        "description": "سجل بياناتك للحصول على وظيفة مناسبة",
        "url": "https://omalmisrservices.com/ar/jobs",
        "icon": "📝"
    }
]

# خدمات "أبحث عن موظفين و عمال"
FIND_WORKERS_SERVICES = [
    {
        "id": "worker_registration",
        "title": "تسجيل طلب موظفين",
        "description": "سجل بياناتك للحصول على موظفيين وعمال مدربين",
        "url": "https://omalmisrservices.com/ar/workers",
        "icon": "👥"
    }
]

# خدمات "بوابة فض و تسوية المنازاعات"
DISPUTE_RESOLUTION_SERVICES = [
    {
        "id": "facility_dispute",
        "title": "نزاع المنشأت",
        "description": "تسوية المنازعات بين المنشآت",
        "url": "https://omalmisrservices.com/ar/dispute/facility",
        "icon": "🏭"
    },
    {
        "id": "worker_dispute",
        "title": "نزاع العمال",
        "description": "تسوية المنازعات بين العمال والمنشآت",
        "url": "https://omalmisrservices.com/ar/dispute/worker",
        "icon": "👷"
    }
]

# خدمات "خدمات الشركات"
COMPANY_SERVICES = [
    {
        "id": "investment_opportunities",
        "title": "طرح الفرص الإستثمارية",
        "description": "يختص هذا القسم بطرح الفرص االستثمارية المميزة في المجال الصناعي و المجال الزراعي بناء على دراسة السوق الحالي",
        "url": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=2&title=%D8%B7%D8%B1%D8%AD%20%D8%A7%D9%84%D9%81%D8%B1%D8%B5%20%D8%A7%D9%84%D8%A5%D8%B3%D8%AA%D8%AB%D9%85%D8%A7%D8%B1%D9%8A%D8%A9",
        "icon": "💰"
    },
    {
        "id": "economic_feasibility",
        "title": "دراسات الجدوى الإقتصادية",
        "description": "تأتي مهمة هذا القسم في عمل الدراسات الالزمة للمشروع ويخدم تحت مظلة هذا القسم عدد 6 شركات محلية ودولية متخصصة في دراسات الجدوى للمشروعات الصغيرة والكبيرة",
        "url": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=3&title=%D8%AF%D8%B1%D8%A7%D8%B3%D8%A7%D8%AA%20%D8%A7%D9%84%D8%AC%D8%AF%D9%88%D9%89%20%D8%A7%D9%84%D8%A5%D8%AC%D8%AA%D8%B5%D8%A7%D8%AF%D9%8A%D8%A9",
        "icon": "📊"
    },
    {
        "id": "strategic_partnership",
        "title": "الشراكة الإستراتيجية",
        "description": "تتكون مهمة هذا القسم في عمل الدراسات الالزمة إلقامة المشروع إما من خالل توفير شريك محلي او شريك اجنبي وأيضا من خالل المحافظ والصناديق اإلستثمارية",
        "url": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=4&title=%D8%A7%D9%84%D8%B4%D8%B1%D8%A7%D9%83%D8%A9%20%D8%A7%D9%84%D8%A5%D8%B3%D8%AA%D8%B1%D8%A7%D8%AA%D9%8A%D8%AC%D9%8A%D8%A9",
        "icon": "🤝"
    },
    {
        "id": "industrial_real_estate",
        "title": "الإنشاءات والعقارات الصناعية",
        "description": "يختص هذا القسم بعمل الرسومات والتصميمات الهندسية للمنشأة الصناعية بما يتناسب مع إحتياجات وبيئة العمل وتوفير المواقع الالزمة إلقامة المشاريع الصناعية و الزراعية",
        "url": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=5&title=%D8%A7%D9%84%D8%A5%D9%86%D8%B4%D8%A7%D8%A1%D8%A7%D8%AA%20%D9%88%D8%A7%D9%84%D8%B9%D9%82%D8%A7%D8%B1%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B5%D9%86%D8%A7%D8%B9%D9%8A%D8%A9",
        "icon": "🏗️"
    },
    {
        "id": "raw_materials",
        "title": "الخامات ومستلزمات الإنتاج",
        "description": "يختص هذا القسم بتوفير الخامات ومستلزمات اإلنتاج طبقاً للمعايير و المواصفات المطلوبة حسب معايير الجودة العالمية",
        "url": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=6&title=%D8%A7%D9%84%D8%AE%D8%A7%D9%85%D8%A7%D8%AA%20%D9%88%D9%85%D8%B3%D8%AA%D9%84%D8%B2%D9%85%D8%A7%D8%AA%20%D8%A7%D9%84%D8%A5%D9%86%D8%AA%D8%A7%D8%AC",
        "icon": "🧰"
    },
    {
        "id": "local_marketing",
        "title": "التسويق المحلي للمنتجات الصناعية و الزراعية",
        "description": "يختص هذا القسم بإجراء تحليل للسوق تمهيدا لدخول منتج جديد في السوق وبناء وخلق الافكار التسويقية لاستهداف المستهلك من خلال كافة القنوات الدعائية والخطط التسوقية",
        "url": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=7&title=%D8%A7%D9%84%D8%AA%D8%B3%D9%88%D9%8A%D9%82%20%D8%A7%D9%84%D9%85%D8%AD%D9%84%D9%8A%20%D9%84%D9%84%D9%85%D9%86%D8%AA%D8%AC%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B5%D9%86%D8%A7%D8%B9%D9%8A%D8%A9%20%D9%88%20%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A%D8%A9",
        "icon": "🏪"
    },
    {
        "id": "international_marketing",
        "title": "التسويق الدولي للمنتجات الصناعية و الزراعية",
        "description": "يختص هذا القسم بإجراء تحليل للسوق تمهيدا لتصدير المنتجات الصناعية و الزراعية في دول الخليج العربي و دول افريقيا و دول االتحاد االوروبي",
        "url": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=8&title=%D8%A7%D9%84%D8%AA%D8%B3%D9%88%D9%8A%D9%82%20%D8%A7%D9%84%D8%AF%D9%88%D9%84%D9%8A%20%D9%84%D9%84%D9%85%D9%86%D8%AA%D8%AC%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B5%D9%86%D8%A7%D8%B9%D9%8A%D8%A9%20%D9%88%20%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A%D8%A9",
        "icon": "🌍"
    },
    {
        "id": "governmental_services",
        "title": "الخدمات الحكومية",
        "description": "هذا القسم يختص بوضع حلول لكافة العقبات للمستثمرين في القطاع الصناعي وفقا لقوانين اإلستثمار الدولية والمحلية",
        "url": "https://omalmisrservices.com/ar/companies/formView?type=1&media_id=9&title=%D8%A7%D9%84%D8%AE%D8%AF%D9%85%D8%A7%D8%AA%20%D8%A7%D9%84%D8%AD%D9%83%D9%88%D9%85%D9%8A%D8%A9",
        "icon": "🏛️"
    },
    {
        "id": "education_research",
        "title": "خدمات التعليم والبحث العلمي",
        "description": "تقديم الدورات التدريبة للكوادر البشرية الفنية والادارية تقديم الاستشارات الفنية والادارية",
        "url": "https://omalmisrservices.com/ar/companies?type=7",
        "icon": "🎓"
    },
    {
        "id": "financial_services",
        "title": "خدمة الشؤون المالية",
        "description": "تقديم خدمة إدارة الشئون المالية للمنشآت تقديم الاستشارات المالية ادارة الملف الضريبي",
        "url": "https://omalmisrservices.com/ar/companies?type=8",
        "icon": "💲"
    },
    {
        "id": "it_services",
        "title": "خدمة تكنولوجيا المعلومات",
        "description": "يقدم هذا القطاع خدمات إنشاء المواقع الالكترونية والتطبيقات ادارة المواقع الالكترونية",
        "url": "https://omalmisrservices.com/ar/companies?type=6",
        "icon": "💻"
    },
    {
        "id": "legal_services",
        "title": "خدمات الاستشارات القانونية",
        "description": "هو قطاع مسئول عن جميع الاستشارات القانونية الخاصة بالشركات (العقود والتراخيص-إدارة",
        "url": "https://omalmisrservices.com/ar/companies?type=5",
        "icon": "⚖️"
    },
    {
        "id": "media_services",
        "title": "الخدمات الاعلامية",
        "description": "يوفر الأفكار الإعلانية والحملات الدعائية ويوفر خدمات الجرافيك والمونتاج إدارة السوشيال مديا",
        "url": "https://omalmisrservices.com/ar/companies?type=4",
        "icon": "📺"
    },
    {
        "id": "hr_marketing",
        "title": "خدمات تسويق الموارد البشرية",
        "description": "يختص هذا القطاع بتوفير الكوادر البشرية المدربة والمؤهلة (الفنية والإدارية)",
        "url": "https://omalmisrservices.com/ar/companies?type=3",
        "icon": "👥"
    },
    {
        "id": "job_marketing",
        "title": "خدمات تسويق فرص العمل",
        "description": "هذا القطاع يختص في التواصل مع المتقدمين على الوظائف و تشغيلهم حسب المعايير",
        "url": "https://omalmisrservices.com/ar/companies?type=2",
        "icon": "💼"
    },
    {
        "id": "industrial_agricultural_investment",
        "title": "خدمة الإستثمار الصناعي والزراعي",
        "description": "يتم تقديم الخدمات الاستثمارية على ثلاث مراحل: الاولى : طرح الفرص والانشاء",
        "url": "https://omalmisrservices.com/ar/companies?type=1",
        "icon": "🏭"
    }
]

# معلومات عن الشركة
COMPANY_INFO = {
    "about": {
        "title": "من نحن",
        "description": "الريادة في صناعة الخدمات محليًا وعالميًا للسوق الصناعي من خال توحيد باب الخدمة للمستثمر الصناعي باستخدام أحدث الأساليب والأدوات التكنولوجية وفقًا لاستراتيجية التنمية المستدامة العالمية ونشر الوعي بالثقافة الصناعية وأهميتها وزيادة الإنتاج مع التمسك بعقيدة عمل مؤسسة والنهوض بأعضائها ومستثمريها."
    },
    "mission": {
        "title": "الرسالة",
        "description": "الريادة في صناعة الخدمات محليًا وعالميًا للسوق الصناعي من خال توحيد باب الخدمة للمستثمر الصناعي باستخدام أحدث الأساليب والأدوات التكنولوجية وفقًا لاستراتيجية التنمية المستدامة العالمية ونشر الوعي بالثقافة الصناعية وأهميتها وزيادة الإنتاج مع التمسك بعقيدة عمل مؤسسة والنهوض بأعضائها ومستثمريها."
    },
    "goals": {
        "title": "أهدافنا",
        "description": """
توحيد باب الخدمة للمستثمر الصناعي.
أن نكون البوابة الرائدة للمستثمرين الصناعيين والكوادر البشرية لدخولهم سوق العمل الصناعي.
أن نصبح منظومة إقتصادية تؤثر في سوق العمل العالمي.
إنشاء مراكز تدريب وتأهيل ومدارس تكنولوجيا تطبيقية في كل منطقة صناعية.
نطمح للوصول لتدريب 500 ألف شاب سعودى على القطاع الصناعى، وأيضا توفير 500 ألف فرصة عمل فى البيئة الصناعية. تخرج وتدريب 100 ألف رجل أعمال جديد فى ريادة الأعمال الصناعية طبقاً لرؤية المملكة 2030
"""
    },
    "vision": {
        "title": "رؤيتنا",
        "description": "نعمل برؤية مستدامة حتي تصبح منظومة عمال مصر كيان خدمي صناعي تعليمى زراعى يؤثر فى منظومة الاقتصاد الدولى وأن تقود عمال مصر أكبر تكتل صناعى ومحفظة إستثمارية صناعية هي الاولى من نوعها إفريقيا وعربياً."
    },
    "social_media": {
        "youtube": "https://www.youtube.com/channel/UCAkYTIf30ypaEE5gfrMhdUw",
        "instagram": "https://www.instagram.com/omalmisr/",
        "linkedin": "https://www.linkedin.com/company/79479037/admin/feed/posts/",
        "twitter": "https://twitter.com/omalmisr1",
        "facebook": "https://www.facebook.com/Omal.Misr.Foundation/"
    }
}

# دالة للحصول على قائمة الخدمات حسب الفئة
def get_services_by_category(category_id):
    """
    الحصول على الخدمات حسب الفئة المطلوبة
    
    :param category_id: معرف الفئة
    :return: قائمة بالخدمات
    """
    if category_id == "find_job":
        return FIND_JOB_SERVICES
    elif category_id == "find_workers":
        return FIND_WORKERS_SERVICES
    elif category_id == "company_services":
        return COMPANY_SERVICES
    elif category_id == "dispute_resolution":
        return DISPUTE_RESOLUTION_SERVICES
    else:
        return []

# دالة للحصول على الخدمة حسب المعرف
def get_service_by_id(service_id):
    """
    الحصول على تفاصيل خدمة بناءً على المعرف
    
    :param service_id: معرف الخدمة
    :return: تفاصيل الخدمة
    """
    # البحث في كل الفئات
    all_services = (
        FIND_JOB_SERVICES + 
        FIND_WORKERS_SERVICES + 
        COMPANY_SERVICES + 
        DISPUTE_RESOLUTION_SERVICES
    )
    
    for service in all_services:
        if service["id"] == service_id:
            return service
    
    # البحث في القائمة الرئيسية
    for service in MAIN_SERVICES:
        if service["id"] == service_id:
            return service
    
    return None

# دالة لتجميع كل الخدمات في قائمة واحدة
def get_all_services():
    """
    الحصول على جميع الخدمات المتاحة
    
    :return: قائمة بجميع الخدمات
    """
    return (
        MAIN_SERVICES + 
        FIND_JOB_SERVICES + 
        FIND_WORKERS_SERVICES + 
        COMPANY_SERVICES + 
        DISPUTE_RESOLUTION_SERVICES
    )