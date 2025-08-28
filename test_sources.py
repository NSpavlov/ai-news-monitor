#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('/home/ubuntu/ai_news_system')

from ai_news_monitor import AINewsMonitor
import json

def test_individual_sources():
    """Тестуємо кожне джерело окремо"""
    print("🧪 Тестування джерел новин...")
    print("=" * 60)
    
    monitor = AINewsMonitor()
    
    # Завантажуємо список джерел
    sources = monitor.ai_config['sources']['blogs']
    
    for i, source in enumerate(sources, 1):
        print(f"\n{i}. Тестую: {source}")
        print("-" * 40)
        
        try:
            # Тестуємо парсинг
            news_items = monitor.scrape_blog_news(source)
            print(f"📰 Знайдено новин: {len(news_items)}")
            
            if news_items:
                for j, news in enumerate(news_items[:2], 1):
                    print(f"   {j}. {news['title'][:60]}...")
                    url_works = monitor.check_url_validity(news['url'])
                    print(f"      URL працює: {'✅' if url_works else '❌'}")
            else:
                print("   ❌ Новини не знайдено")
                
        except Exception as e:
            print(f"   ❌ Помилка: {e}")
        
        print()

def test_translation():
    """Тестуємо переклад"""
    print("\n🌍 Тестування перекладу...")
    print("=" * 40)
    
    monitor = AINewsMonitor()
    
    test_texts = [
        "OpenAI releases GPT-4 Turbo with enhanced capabilities",
        "Google announces breakthrough in quantum AI computing",
        "Microsoft integrates AI into Office 365 suite"
    ]
    
    for text in test_texts:
        print(f"🇺🇸 Оригінал: {text}")
        translation = monitor.translate_to_ukrainian(text)
        print(f"🇺🇦 Переклад: {translation}")
        print()

def main():
    """Основна функція тестування"""
    choice = input("Що тестувати?\n1. Джерела новин\n2. Переклад\n3. Все\nВибір (1-3): ")
    
    if choice == "1":
        test_individual_sources()
    elif choice == "2":
        test_translation()
    elif choice == "3":
        test_individual_sources()
        test_translation()
    else:
        print("Невірний вибір")

if __name__ == "__main__":
    main()