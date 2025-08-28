#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('/home/ubuntu/ai_news_system')

from ai_news_monitor import AINewsMonitor
import logging

def test_monitor():
    """Тестуємо AI News Monitor"""
    print("🧪 Запускаю тест AI News Monitor...")
    print("=" * 60)
    
    try:
        monitor = AINewsMonitor()
        
        # Тестуємо завантаження конфігурації
        print("✅ Конфігурація завантажена успішно")
        print(f"📊 Джерел блогів: {len(monitor.ai_config['sources']['blogs'])}")
        print(f"🔑 Ключових слів: {len(monitor.ai_config['filter_criteria']['keywords'])}")
        
        # Тестуємо пошук новин
        print("\n🔍 Тестую пошук новин...")
        news_list = monitor.search_ai_news()
        print(f"📰 Знайдено новин: {len(news_list)}")
        
        if news_list:
            print("\n📋 Приклади знайдених новин:")
            for i, news in enumerate(news_list[:3]):
                print(f"{i+1}. {news['title'][:80]}...")
                print(f"   Джерело: {news['source']}")
                print(f"   URL працює: {'✅' if monitor.check_url_validity(news['url']) else '❌'}")
        
        # Тестуємо фільтрацію
        print("\n🎯 Тестую фільтрацію...")
        filtered_news = monitor.filter_news(news_list)
        print(f"✅ Релевантних новин: {len(filtered_news)}")
        
        if filtered_news:
            # Тестуємо переклад та форматування
            print("\n🌍 Тестую переклад та форматування...")
            test_news = filtered_news[0]
            message = monitor.format_news_message(test_news)
            
            print("📝 Приклад відформатованого повідомлення:")
            print("-" * 40)
            print(message[:500] + "..." if len(message) > 500 else message)
            print("-" * 40)
            
            # Зберігаємо тестове повідомлення
            filename = monitor.save_news_to_file(message, test_news)
            print(f"💾 Тестове повідомлення збережено: {filename}")
            
            # Питаємо чи надсилати у Telegram
            response = input("\n❓ Надіслати тестове повідомлення у Telegram? (y/n): ")
            if response.lower() == 'y':
                if monitor.send_to_telegram(message):
                    print("✅ Тестове повідомлення надіслано успішно!")
                    monitor.sent_news.append(test_news['hash'])
                    monitor.save_sent_news()
                else:
                    print("❌ Помилка надсилання тестового повідомлення")
        
        print("\n🎉 ТЕСТ ЗАВЕРШЕНО УСПІШНО!")
        print("Система готова до автоматичної роботи кожні 2 години")
        
    except Exception as e:
        print(f"❌ Помилка тестування: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monitor()