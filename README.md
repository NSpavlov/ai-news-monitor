# AI News Monitor System

Автоматична система моніторингу AI новин з перекладом на українську та надсиланням у Telegram.

## 🚀 Особливості

- ✅ **Реальний пошук новин** з офіційних блогів AI компаній
- ✅ **Перевірка працездатності посилань** перед надсиланням
- ✅ **Автоматичний переклад** на українську мову
- ✅ **Уникнення дублікатів** - система запам'ятовує надіслані новини
- ✅ **Автоматичний запуск** кожні 2 години
- ✅ **Детальне логування** всіх операцій

## 📁 Структура файлів

```
/home/ubuntu/ai_news_system/
├── ai_news_monitor.py      # Основний скрипт
├── run_monitor.py          # Скрипт для daemon task
├── test_monitor.py         # Тестування системи
├── test_sources.py         # Тестування джерел
├── ai_news_config.json     # Конфігурація джерел та фільтрів
├── telegram_config.json    # Налаштування Telegram
├── sent_news.json          # База надісланих новин
├── ai_news.log            # Логи роботи
└── news_*.md              # Збережені новини
```

## 🔧 Джерела новин

Система моніторить наступні офіційні блоги:

- **OpenAI Blog** - https://openai.com/blog/
- **Microsoft AI Blog** - https://blogs.microsoft.com/ai/
- **Anthropic News** - https://www.anthropic.com/news
- **Google AI Blog** - https://ai.googleblog.com/
- **Google Technology Blog** - https://blog.google/technology/ai/
- **Meta Research** - https://research.facebook.com/blog/
- **DeepMind Blog** - https://deepmind.com/blog
- **Hugging Face Blog** - https://huggingface.co/blog
- **Stability AI News** - https://stability.ai/news
- **NVIDIA AI Insights** - https://www.nvidia.com/en-us/ai-data-science/ai-insights/
- **AWS ML Blog** - https://aws.amazon.com/blogs/machine-learning/
- **Azure AI Blog** - https://azure.microsoft.com/en-us/blog/topics/artificial-intelligence/

## 🎯 Критерії фільтрації

Система шукає новини, що містять ключові слова:
- Нові продукти та релізи
- Прориви та революційні рішення
- Приклади використання
- Бізнес впровадження
- Популярні та цікаві новини

## 🤖 Автоматичний запуск

Система налаштована як daemon task, що запускається кожні 2 години:
- **Інтервал**: 7200 секунд (2 години)
- **Статус**: АКТИВНИЙ
- **Наступний запуск**: автоматично

## 📱 Telegram інтеграція

- **Група**: @novyni_hi
- **Формат**: Markdown з емодзі
- **Перевірка посилань**: Так
- **Уникнення дублікатів**: Так

## 🧪 Тестування

### Повний тест системи:
```bash
cd /home/ubuntu/ai_news_system
python test_monitor.py
```

### Тест окремих джерел:
```bash
python test_sources.py
```

### Ручний запуск:
```bash
python ai_news_monitor.py
```

## 📊 Моніторинг

### Перегляд логів:
```bash
tail -f /home/ubuntu/ai_news_system/ai_news.log
```

### Перевірка надісланих новин:
```bash
cat /home/ubuntu/ai_news_system/sent_news.json
```

### Перегляд збережених новин:
```bash
ls -la /home/ubuntu/ai_news_system/news_*.md
```

## ⚙️ Налаштування

### Зміна інтервалу запуску:
Відредагуйте daemon task через систему управління завданнями.

### Додавання нових джерел:
Відредагуйте `ai_news_config.json`, секцію `sources.blogs`.

### Зміна критеріїв фільтрації:
Відредагуйте `ai_news_config.json`, секцію `filter_criteria.keywords`.

## 🔍 Усунення проблем

### Якщо новини не надсилаються:
1. Перевірте логи: `tail -f ai_news.log`
2. Перевірте Telegram токен у конфігурації
3. Запустіть тест: `python test_monitor.py`

### Якщо посилання не працюють:
1. Система автоматично перевіряє посилання
2. Неробочі посилання відфільтровуються
3. Перевірте логи для деталей

### Якщо переклад не працює:
1. Перевірте OpenAI API ключ
2. Перевірте квоти API
3. Запустіть тест перекладу: `python test_sources.py`

## 📈 Статистика

Система веде детальну статистику:
- Кількість знайдених новин
- Кількість відфільтрованих новин
- Кількість надісланих повідомлень
- Помилки та попередження

## 🔄 Оновлення

Для оновлення системи:
1. Зупиніть daemon task
2. Оновіть файли
3. Запустіть тест
4. Перезапустіть daemon task

---

**Система готова до роботи!** 🎉

Автоматичний моніторинг AI новин працює кожні 2 години та надсилає свіжі новини у вашу Telegram групу.