#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import schedule
import time
from datetime import datetime, timedelta
from ai_news_monitor import AINewsMonitor

class AdaptiveScheduler:
    def __init__(self):
        self.monitor = AINewsMonitor()
        self.peak_hours = [(9, 12), (14, 18)]  # UTC: 9-12, 14-18
        self.weekend_modifier = 0.5  # Менше активності на вихідних
        
    def get_current_priority(self):
        """Визначає пріоритет моніторингу залежно від часу"""
        now = datetime.utcnow()
        hour = now.hour
        weekday = now.weekday()
        
        # Базовий пріоритет
        priority = 1.0
        
        # Пікові години (робочий час в US/EU)
        for start, end in self.peak_hours:
            if start <= hour <= end:
                priority *= 2.0
                break
        
        # Вихідні дні (субота=5, неділя=6)
        if weekday >= 5:
            priority *= self.weekend_modifier
            
        # Нічні години (0-6 UTC)
        if 0 <= hour <= 6:
            priority *= 0.3
            
        return priority
    
    def get_adaptive_interval(self):
        """Повертає інтервал в хвилинах залежно від пріоритету"""
        priority = self.get_current_priority()
        
        # Базовий інтервал - 120 хвилин (2 години)
        base_interval = 120
        
        # Адаптивний інтервал
        adaptive_interval = int(base_interval / priority)
        
        # Мінімум 30 хвилин, максимум 8 годин
        adaptive_interval = max(30, min(adaptive_interval, 480))
        
        return adaptive_interval
    
    def run_monitor_adaptive(self):
        """Запуск моніторингу з логуванням пріоритету"""
        priority = self.get_current_priority()
        next_interval = self.get_adaptive_interval()
        
        print(f"Запуск моніторингу (пріоритет: {priority:.1f}, наступний запуск через {next_interval} хв)")
        
        try:
            self.monitor.run_once()
        except Exception as e:
            print(f"Помилка: {e}")
        
        # Очищаємо старий розклад та встановлюємо новий
        schedule.clear('adaptive')
        schedule.every(next_interval).minutes.do(self.run_monitor_adaptive).tag('adaptive')
    
    def schedule_conference_boost(self, start_date, end_date):
        """Режим підвищеної активності під час конференцій"""
        # Під час конференцій - кожні 15 хвилин
        now = datetime.now()
        if start_date <= now <= end_date:
            schedule.clear('adaptive')
            schedule.every(15).minutes.do(self.run_monitor_adaptive).tag('adaptive')
            print("Увімкнено режим конференції - моніторинг кожні 15 хвилин")
    
    def start_adaptive_scheduling(self):
        """Запуск адаптивного планувальника"""
        print("Запуск адаптивного планувальника AI News")
        
        # Приклад: підвищена активність під час NeurIPS
        # neurips_start = datetime(2024, 12, 10)
        # neurips_end = datetime(2024, 12, 16)
        # self.schedule_conference_boost(neurips_start, neurips_end)
        
        # Перший запуск
        self.run_monitor_adaptive()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Перевіряємо кожну хвилину

def main():
    scheduler = AdaptiveScheduler()
    scheduler.start_adaptive_scheduling()

if __name__ == "__main__":
    main()