import urllib.request
import json
import time
import re
import os

# Настройки
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}
OUTPUT_FILE = 'statham_quotes.json'

# Попытка загрузить переменные из .env (ручной парсер, чтобы не зависеть от dotenv)
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip("'\"")

# Список собранных цитат
quotes_collection = set()

# При запуске скрипта сначала загружаем старые цитаты, чтобы не потерять их
def load_existing():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    quotes_collection.add(item['text'])
            print(f"Загружено {len(quotes_collection)} существующих цитат из {OUTPUT_FILE}")
        except Exception as e:
            print(f"Ошибка при чтении существующего файла: {e}")

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

def scrape_vk():
    """Парсинг ВКонтакте по API"""
    print("Парсинг VK...")
    vk_token = os.environ.get('VK_TOKEN')
    if not vk_token:
        print("ВНИМАНИЕ: VK_TOKEN не найден в переменных окружения или .env файле. Пропускаем VK.")
        return
        
    vk_version = '5.131'
    # Список коротких имен пабликов (можно дополнять)
    domains = ['jason_statham46', 'public96954008', 'jason_stathams']
    
    for domain in domains:
        print(f"Запрос постов из {domain}...")
        # count=100 - максимум за 1 запрос к API
        url = f"https://api.vk.com/method/wall.get?domain={domain}&count=100&v={vk_version}&access_token={vk_token}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if 'error' in data:
                print(f"VK API Ошибка ({domain}): {data['error'].get('error_msg')}")
                continue
                
            items = data.get('response', {}).get('items', [])
            added_count = 0
            for item in items:
                text = item.get('text', '')
                if not text:
                    continue
                # Разбиваем пост на строки, так как в одном посте может быть несколько мыслей, 
                # либо мусор внизу
                for line in text.split('\n'):
                    cleaned = clean_quote(line)
                    # Фильтруем ссылки, хэштеги и мусор
                    if (10 < len(cleaned) < 200 and 
                        "http" not in cleaned and 
                        "vk.com" not in cleaned and 
                        "#" not in cleaned and
                        not cleaned.startswith('[')):
                        quotes_collection.add(cleaned)
                        added_count += 1
            print(f"Из {domain} успешно обработано постов. Найдено потенциальных цитат: {added_count}")
            time.sleep(1.5) # Задержка между запросами по лимитам ВК (3 запроса в секунду макс)
        except Exception as e:
            print(f"Ошибка при парсинге VK ({domain}): {e}")

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
    
    print(f"\nУспешно собрано {len(result_list)} уникальных цитат (с учетом старых и новых).")
    print(f"Данные сохранены в файл: {OUTPUT_FILE}")

if __name__ == "__main__":
    print("Запуск комбайна по сбору цитат...")
    load_existing()
    scrape_citaty_info()
    time.sleep(1)
    scrape_reddit_json()
    time.sleep(1)
    scrape_vk()
    
    save_to_json()
    print("Готово!")
