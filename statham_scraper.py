import urllib.request
import json
import time
import re

# Настройки
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}
OUTPUT_FILE = 'statham_quotes.json'

# Список собранных цитат
quotes_collection = set()

def clean_quote(text):
    """Очистка текста от мусора и лишних пробелов"""
    text = text.strip()
    # Убираем кавычки по краям если они есть
    text = re.sub(r'^["«»\']+|["«»\']+$', '', text)
    # Убираем (с) Стэтхем и подобное
    text = re.sub(r'(?i)\(?\s*[cс]\s*\)?\s*ст[эе]тх[эе]м.*', '', text)
    text = re.sub(r'(?i)-\s*Джейсон.*', '', text)
    # Убираем html теги если зацепили
    text = re.sub(r'<[^>]+>', '', text)
    # Декодируем html сущности простейшие
    text = text.replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&')
    return text.strip()

def scrape_citaty_info():
    """Парсинг сайта citaty.info (чистый python без bs4)"""
    print("Парсинг citaty.info...")
    url = "https://citaty.info/selection/citaty-stethema"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # На этом сайте цитаты обычно в тегах <p>
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
            
            for p in paragraphs:
                text = clean_quote(p)
                # Фильтруем слишком длинные абзацы и короткие
                if 10 < len(text) < 150 and not text.startswith(('Цитаты Стетхема', 'Часто цитаты', 'Все эти мемные')):
                    quotes_collection.add(text)
    except Exception as e:
        print(f"Ошибка при парсинге citaty.info: {e}")

def scrape_reddit_json():
    """Парсинг Reddit через публичный JSON API"""
    print("Парсинг Reddit (r/rusAskReddit)...")
    url = "https://www.reddit.com/r/rusAskReddit/comments/16omboo/.json"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        # Обход дерева комментариев
        def extract_comments(comment_list):
            for item in comment_list:
                if item['kind'] == 't1': # t1 = comment
                    body = item['data'].get('body', '')
                    # Разбиваем на строки
                    for line in body.split('\n'):
                        cleaned = clean_quote(line)
                        if 10 < len(cleaned) < 150 and "http" not in cleaned and "deleted" not in cleaned:
                            quotes_collection.add(cleaned)
                    
                    # Рекурсивно обходим ответы
                    replies = item['data'].get('replies')
                    if isinstance(replies, dict) and 'data' in replies:
                        extract_comments(replies['data'].get('children', []))
                        
        # Первый элемент - сам пост, второй - комментарии
        if len(data) > 1 and 'data' in data[1]:
            extract_comments(data[1]['data'].get('children', []))
            
    except Exception as e:
        print(f"Ошибка при парсинге Reddit: {e}")

def save_to_json():
    """Сохранение результатов в JSON файл"""
    result_list = []
    # Фильтрация короткого мусора
    valid_quotes = [q for q in quotes_collection if len(q) > 10 and not q.startswith('[')]
    
    for i, quote in enumerate(sorted(list(valid_quotes)), 1):
        result_list.append({
            "id": i,
            "text": quote,
            "author": "Jason Statham (Internet meme)"
        })
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result_list, f, ensure_ascii=False, indent=4)
    
    print(f"\nУспешно собрано {len(result_list)} уникальных цитат.")
    print(f"Данные сохранены в файл: {OUTPUT_FILE}")

if __name__ == "__main__":
    print("Запуск комбайна по сбору цитат...")
    scrape_citaty_info()
    time.sleep(1)
    scrape_reddit_json()
    save_to_json()
    print("Готово!")
