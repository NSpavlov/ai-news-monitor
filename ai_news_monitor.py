#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
from datetime import datetime, timedelta
import openai
import re
import feedparser
from bs4 import BeautifulSoup
import hashlib
import os
import sys
from urllib.parse import urljoin, urlparse
import logging
import aiohttp
import asyncio

# Виправлення кодування для Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/ai_news.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AINewsMonitor:
    def __init__(self):
        self.secrets, self.ai_config, self.telegram_config = self.load_config()
        self.openai_client = openai.OpenAI(api_key=self.secrets['OPENAI']['secrets']['API_KEY'])
        self.sent_news_file = './data/sent_news.json'
        self.sent_news = self.load_sent_news()
        
    def load_config(self):
        """Завантажуємо всі конфігурації"""
        # Шляхи для API ключів
        if os.path.exists('./config/api_secrets.json'):
            secrets_path = './config/api_secrets.json'
        elif os.path.exists('../.api_secret_infos/api_secrets.json'):
            secrets_path = '../.api_secret_infos/api_secrets.json'
        else:
            raise FileNotFoundError("API secrets file not found")
        # Шляхи для конфігурацій - перевіряємо різні локації
        config_locations = [
            './telegram_config.json',
            './config/telegram_config.json',
            '../telegram_config.json'
        ]
        telegram_config_path = None
        for path in config_locations:
            if os.path.exists(path):
                telegram_config_path = path
                break
        ai_config_locations = [
            './ai_news_config.json',
            './config/ai_news_config.json',
            '../ai_news_config.json'
        ]
        ai_config_path = None
        for path in ai_config_locations:
            if os.path.exists(path):
                ai_config_path = path
                break
        if not telegram_config_path:
            raise FileNotFoundError("telegram_config.json not found")
        if not ai_config_path:
            raise FileNotFoundError("ai_news_config.json not found")
        # Завантажуємо файли
        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = json.load(f)
        with open(ai_config_path, 'r', encoding='utf-8') as f:
            ai_config = json.load(f)
        with open(telegram_config_path, 'r', encoding='utf-8') as f:
            telegram_config = json.load(f)
        return secrets, ai_config, telegram_config
    
    def load_sent_news(self):
        """Завантажуємо список вже надісланих новин"""
        if os.path.exists(self.sent_news_file):
            with open(self.sent_news_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_sent_news(self):
        """Зберігаємо список надісланих новин"""
        # Зберігаємо тільки останні 1000 записів
        if len(self.sent_news) > 1000:
            self.sent_news = self.sent_news[-1000:]
        
        with open(self.sent_news_file, 'w') as f:
            json.dump(self.sent_news, f, indent=2)
    
    def get_news_hash(self, title, url):
        """Створюємо хеш для новини"""
        return hashlib.md5(f"{title}{url}".encode()).hexdigest()
    
    def check_url_validity(self, url, timeout=10):
        """Перевіряємо чи працює посилання"""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
        except:
            try:
                response = requests.get(url, timeout=timeout, allow_redirects=True)
                return response.status_code < 400
            except:
                return False
    
    def scrape_blog_news(self, url):
        """Парсимо новини з блогів"""
        news_items = []
        
        try:
            # Спочатку пробуємо RSS
            rss_urls = [
                f"{url.rstrip('/')}/feed/",
                f"{url.rstrip('/')}/rss/",
                f"{url.rstrip('/')}/feed.xml",
                f"{url.rstrip('/')}/rss.xml"
            ]
            
            for rss_url in rss_urls:
                try:
                    feed = feedparser.parse(rss_url)
                    if feed.entries:
                        for entry in feed.entries[:5]:  # Беремо останні 5
                            # Перевіряємо чи новина свіжа (не старше 7 днів)
                            if hasattr(entry, 'published_parsed'):
                                pub_date = datetime(*entry.published_parsed[:6])
                                if datetime.now() - pub_date > timedelta(days=7):
                                    continue
                            
                            news_items.append({
                                'title': entry.title,
                                'content': BeautifulSoup(entry.summary, 'html.parser').get_text()[:500],
                                'url': entry.link,
                                'source': urlparse(url).netloc,
                                'published': getattr(entry, 'published', 'Unknown')
                            })
                        break
                except:
                    continue
            
            # Якщо RSS не спрацював, пробуємо парсити HTML
            if not news_items:
                response = requests.get(url, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Шукаємо статті за типовими селекторами
                articles = soup.find_all(['article', 'div'], class_=re.compile(r'post|article|entry|blog'))
                
                for article in articles[:5]:
                    title_elem = article.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|heading'))
                    link_elem = article.find('a', href=True)
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text().strip()
                        link = urljoin(url, link_elem['href'])
                        
                        # Отримуємо короткий опис
                        content_elem = article.find(['p', 'div'], class_=re.compile(r'excerpt|summary|content'))
                        content = content_elem.get_text().strip()[:500] if content_elem else title
                        
                        news_items.append({
                            'title': title,
                            'content': content,
                            'url': link,
                            'source': urlparse(url).netloc,
                            'published': 'Recent'
                        })
        
        except Exception as e:
            logging.error(f"Помилка парсингу {url}: {e}")
        
        return news_items
    
    async def scrape_blog_news_async(self, session, url):
        """Асинхронний парсинг блогу"""
        try:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    # Використовуємо той же код парсингу
                    return self.parse_blog_content(content, url)
        except Exception as e:
            logging.error(f"Async error {url}: {e}")
        return []

    def parse_blog_content(self, content, url):
        """Виділений код парсингу контенту (з scrape_blog_news)"""
        news_items = []
        try:
            # RSS спочатку
            import feedparser
            feed = feedparser.parse(content)
            if feed.entries:
                for entry in feed.entries[:5]:
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                        if datetime.now() - pub_date > timedelta(days=7):
                            continue
                    news_items.append({
                        'title': entry.title,
                        'content': BeautifulSoup(entry.summary, 'html.parser').get_text()[:500],
                        'url': entry.link,
                        'source': urlparse(url).netloc,
                        'published': getattr(entry, 'published', 'Unknown')
                    })
            # Якщо RSS не працює, парсимо HTML
            if not news_items:
                soup = BeautifulSoup(content, 'html.parser')
                articles = soup.find_all(['article', 'div'], class_=re.compile(r'post|article|entry|blog'))
                for article in articles[:5]:
                    title_elem = article.find(['h1', 'h2', 'h3'])
                    link_elem = article.find('a', href=True)
                    if title_elem and link_elem:
                        title = title_elem.get_text().strip()
                        link = urljoin(url, link_elem['href'])
                        content_elem = article.find(['p', 'div'])
                        content = content_elem.get_text().strip()[:500] if content_elem else title
                        news_items.append({
                            'title': title,
                            'content': content,
                            'url': link,
                            'source': urlparse(url).netloc,
                            'published': 'Recent'
                        })
        except Exception as e:
            logging.error(f"Parse error {url}: {e}")
        return news_items

    def fetch_reddit_posts(self):
        """Парсинг топових постів з AI subreddit'ів"""
        subreddits = self.ai_config['sources']['reddit']
        posts = []
        
        for subreddit in subreddits:
            try:
                url = f"https://www.reddit.com/{subreddit}/hot.json?limit=5"
                headers = {'User-Agent': 'AI News Monitor 1.0'}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for post in data['data']['children']:
                        post_data = post['data']
                        # Фільтруємо тільки пости з текстом/посиланнями
                        if post_data.get('selftext') or post_data.get('url'):
                            posts.append({
                                'title': post_data['title'],
                                'content': post_data.get('selftext', '')[:500],
                                'url': post_data.get('url', f"https://reddit.com{post_data['permalink']}"),
                                'source': f"reddit-{subreddit.replace('r/', '')}"
                            })
                time.sleep(1)  # Пауза між запитами
            except Exception as e:
                logging.error(f"Помилка Reddit {subreddit}: {e}")
                continue
        
        return posts
    
    def search_ai_news(self):
        """Пошук AI новин з різних джерел"""
        logging.info("Searching for latest AI news...")
        all_news = []
        # Парсимо блоги
        for blog_url in self.ai_config['sources']['blogs']:
            logging.info(f"Парсю {blog_url}")
            news_items = self.scrape_blog_news(blog_url)
            all_news.extend(news_items)
            time.sleep(2)  # Пауза між запитами
        # Додаємо Reddit
        reddit_posts = self.fetch_reddit_posts()
        all_news.extend(reddit_posts)
        # Додаємо пошук через веб-пошук для додаткових новин
        try:
            # Використовуємо requests для пошуку новин через Google News API або інші джерела
            search_queries = [
                "OpenAI new release",
                "Google AI breakthrough",
                "Microsoft AI news",
                "Anthropic Claude update",
                "AI product launch"
            ]
            # Тут можна додати додаткові джерела новин
        except Exception as e:
            logging.error(f"Помилка веб-пошуку: {e}")
        logging.info(f"Found {len(all_news)} news items")
        return all_news
    
    async def search_ai_news_async(self):
        """Асинхронний пошук всіх новин"""
        logging.info("Starting async news search...")
        async with aiohttp.ClientSession() as session:
            # Асинхронно парсимо всі блоги
            blog_tasks = [self.scrape_blog_news_async(session, url)
                          for url in self.ai_config['sources']['blogs']]
            blog_results = await asyncio.gather(*blog_tasks, return_exceptions=True)
            all_news = []
            for result in blog_results:
                if isinstance(result, list):
                    all_news.extend(result)
        # Reddit все ще синхронно (їх API не любить багато паралельних запитів)
        reddit_posts = self.fetch_reddit_posts()
        all_news.extend(reddit_posts)
        logging.info(f"Found {len(all_news)} total news items (async)")
        return all_news
    
    def filter_news(self, news_list):
        """Фільтруємо новини за критеріями та перевіряємо унікальність"""
        logging.info("Filtering news by criteria...")
        filtered = []
        keywords = self.ai_config['filter_criteria']['keywords']
        exclude_keywords = self.ai_config['filter_criteria'].get('exclude_keywords', [])
        for news in news_list:
            # Перевірка на виключені слова
            text_to_check = f"{news['title']} {news['content']}".lower()
            if any(exclude_word.lower() in text_to_check for exclude_word in exclude_keywords):
                logging.info(f"Excluded: {news['title'][:50]}...")
                continue
            # Пропускаємо занадто короткий контент
            if len(news['content']) < 100:
                continue
            # Перевіряємо чи новина вже була надіслана
            news_hash = self.get_news_hash(news['title'], news['url'])
            if news_hash in self.sent_news:
                continue
            # Перевіряємо чи працює посилання
            if not self.check_url_validity(news['url']):
                logging.warning(f"Посилання не працює: {news['url']}")
                continue
            # Перевіряємо релевантність за ключовими словами
            if any(keyword.lower() in text_to_check for keyword in keywords):
                news['hash'] = news_hash
                filtered.append(news)
        logging.info(f"Found {len(filtered)} new relevant news")
        return filtered
    
    def translate_to_ukrainian(self, text):
        """Переклад тексту на українську"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ти професійний перекладач технічних текстів. Переклади текст на українську мову, зберігаючи технічні терміни та назви продуктів. Переклад має бути природним та зрозумілим."},
                    {"role": "user", "content": f"Переклади цей текст на українську: {text}"}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Помилка перекладу: {e}")
            return text
    
    def format_news_message(self, news):
        """Форматуємо новину для Telegram"""
        
        # Перекладаємо заголовок та контент
        title_ua = self.translate_to_ukrainian(news['title'])
        content_ua = self.translate_to_ukrainian(news['content'])
        
        # Форматуємо повідомлення
        message = f"🚀 {title_ua}\n\n"
        
        # Додаємо основний контент
        sentences = content_ua.split('. ')
        for sentence in sentences[:5]:  # Беремо перші 5 речення
            if sentence.strip():
                message += f"• {sentence.strip()}.\n"
        
        message += "\n😶😶😶\n\n"
        message += f"🔗 Детальніше: {news['url']}\n"
        message += f"📰 Джерело: {news['source']}\n\n"
        message += "👍 [Група](https://t.me/novyni_hi)"
        
        return message
    
    def send_to_telegram(self, message):
        """Надсилаємо повідомлення у Telegram"""
        bot_token = self.secrets['TELEGRAM']['secrets']['BOT_TOKEN']
        chat_id = self.telegram_config['target_group']['chat_id']
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': False
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logging.info("Message sent successfully!")
                return True
            else:
                logging.error(f"❌ Помилка надсилання: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logging.error(f"❌ Помилка підключення до Telegram: {e}")
            return False
    
    def save_news_to_file(self, message, news):
        """Зберігаємо новину у файл"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f"./data/news_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# AI News - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(message)
            f.write(f"\n\n---\n")
            f.write(f"Original Title: {news['title']}\n")
            f.write(f"Source: {news['source']}\n")
            f.write(f"URL: {news['url']}\n")
        
        return filename
    
    def run_once(self):
        """Виконуємо один цикл пошуку та надсилання новин"""
        logging.info("Starting AI News Monitor...")
        
        try:
            # Запускаємо асинхронний пошук
            news_list = asyncio.run(self.search_ai_news_async())
            if not news_list:
                logging.info("No news found")
                return
            
            # Фільтруємо
            filtered_news = self.filter_news(news_list)
            
            if not filtered_news:
                logging.info("No new relevant news found")
                return
            
            # Обробляємо кожну новину (максимум 3 за раз)
            sent_count = 0
            for news in filtered_news[:3]:
                try:
                    # Форматуємо повідомлення
                    message = self.format_news_message(news)
                    
                    # Зберігаємо у файл
                    filename = self.save_news_to_file(message, news)
                    logging.info(f"Message saved: {filename}")
                    
                    # Надсилаємо у Telegram
                    if self.send_to_telegram(message):
                        # Додаємо до списку надісланих
                        self.sent_news.append(news['hash'])
                        sent_count += 1
                        
                        # Пауза між повідомленнями
                        time.sleep(self.telegram_config['rate_limits']['delay_between_messages'])
                    
                except Exception as e:
                    logging.error(f"Error processing news: {e}")
                    continue
            
            # Зберігаємо список надісланих новин
            self.save_sent_news()
            
            logging.info(f"Successfully sent {sent_count} news items")
            
        except Exception as e:
            logging.error(f"Critical error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Основна функція"""
    monitor = AINewsMonitor()
    monitor.run_once()

if __name__ == "__main__":
    main()