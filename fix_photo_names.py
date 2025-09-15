#!/usr/bin/env python3
"""
Скрипт для исправления имен фотографий с символом '+' в номерах телефонов
"""
import os
from pathlib import Path

def fix_photo_names():
    """Переименовывает файлы, заменяя '+' в именах файлов"""
    photos_dir = Path("uploads/photos")
    
    if not photos_dir.exists():
        print("❌ Папка uploads/photos не существует")
        return
    
    print("🔍 Поиск файлов с '+' в именах...")
    
    files_to_rename = []
    for file_path in photos_dir.glob("*+*.jpg"):
        files_to_rename.append(file_path)
    
    if not files_to_rename:
        print("✅ Файлы с '+' в именах не найдены")
        return
    
    print(f"📋 Найдено {len(files_to_rename)} файлов для переименования:")
    
    for file_path in files_to_rename:
        old_name = file_path.name
        new_name = old_name.replace('+', '')
        new_path = file_path.parent / new_name
        
        try:
            file_path.rename(new_path)
            print(f"✅ {old_name} → {new_name}")
        except Exception as e:
            print(f"❌ Ошибка переименования {old_name}: {e}")
    
    print("🎉 Переименование файлов завершено!")
    
    # Информируем о необходимости перезапуска сервера
    print("\n⚠️ ВАЖНО: Перезапустите сервер, чтобы обновить пути в памяти!")
    print("   Или удалите текущие заявки и загрузите фотографии заново.")

if __name__ == "__main__":
    fix_photo_names()
