#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime

# Додаємо шлях до нашої системи
sys.path.append('./')

from ai_news_monitor import AINewsMonitor

def main():
    """Запуск AI News Monitor для daemon task"""
    
    # Налаштування логування
    log_file = f'./logs/ai_news_{datetime.now().strftime("%Y%m%d")}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info("=" * 60)
    logging.info("🤖 Запуск AI News Monitor (Daemon Task)")
    logging.info(f"⏰ Час запуску: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 60)
    
    try:
        # Створюємо та запускаємо монітор
        monitor = AINewsMonitor()
        monitor.run_once()
        
        logging.info("✅ AI News Monitor завершив роботу успішно")
        
    except Exception as e:
        logging.error(f"❌ Критична помилка в AI News Monitor: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()