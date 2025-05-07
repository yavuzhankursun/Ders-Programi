@echo off
echo Haftalik Ders Programi Uygulamasi baslatiliyor...

REM Gerekli paketleri kontrol et ve yükle
pip install tabulate colorama pandas sqlalchemy openpyxl xlsxwriter > nul 2>&1

python main.py
pause 