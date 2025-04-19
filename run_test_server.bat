@echo off
echo ======================================================
echo      تشغيل خادم اختبار شات بوت مجمع عمال مصر
echo ======================================================

echo تهيئة البيئة...

REM تفعيل البيئة الافتراضية إذا كانت موجودة
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo تشغيل خادم الاختبار...
python test_server.py

pause