#!/bin/bash
echo "Haftalik Ders Programi Uygulamasi baslatiliyor..."

# Gerekli paketleri kontrol et ve yükle
pip install tabulate colorama pandas sqlalchemy openpyxl xlsxwriter > /dev/null 2>&1

python main.py 