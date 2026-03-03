import urllib.request
import urllib.parse
import json
import time
import re
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}
OUTPUT_FILE = 'statham_quotes.json'

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip("'\"")

quotes_collection = set()

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

def is_statham_quote(text):
    """Строгая проверка на наличие упоминания Стетхема в тексте поста/статьи"""
    pattern = r'(?i)(стетхем|стэтхэм|стэйтем|стетхэм|statham|джейсон)'
    return bool(re.search(pattern, text))

def clean_quote(text):
    """Очистка текста: удаление мусора, подписей и тегов"""
    text = text.strip()
    
    # Сначала убираем html теги и декодируем сущности
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&').replace('&nbsp;', ' ')
    
    # Убираем подписи, которые обычно идут в конце (с дефисом, тире, копирайтом)
    text = re.sub(r'(?i)[\n\r—\-~—]?\s*\(?[cс©]\)?\s*(джейсон\s+)?(ст[эе]тх[эе]м|стэйтем|statham).*$', '', text)
    text = re.sub(r'(?i)[\n\r—\-~—]?\s*(джейсон\s+)?(ст[эе]тх[эе]м|стэйтем|statham).*$', '', text)
    text = re.sub(r'(?i)^\s*\[?[cс©]\]?\s*(джейсон\s+)?(ст[эе]тх[эе]м|стэйтем|statham)[\]:]?\s*', '', text)
    
    # Убираем кавычки по краям
    text = re.sub(r'^["«»\']+|["«»\']+$', '', text.strip())
    
    # Для текстовых мемов: очищаем блоки типа "[Описание: ...]" 
    text = re.sub(r'(?i)\[описание:.*?\]', '', text)
    text = re.sub(r'(?i)текст:\s*', '', text)
    
    return text.strip()

def filter_and_add(text):
    """Фильтрация и добавление очищенной цитаты в коллекцию"""
    cleaned = clean_quote(text)
    
    # Проверка на адекватную длину, отсутствие ссылок и хештегов
    if 10 < len(cleaned) < 250 and "http" not in cleaned and "vk.com" not in cleaned and "#" not in cleaned:
        # Убеждаемся, что мы не сохранили саму подпись Джейсона как цитату
        if not re.fullmatch(r'(?i)(джейсон\s+)?(ст[эе]тх[эе]м|стэйтем|statham)', cleaned):
            quotes_collection.add(cleaned)
            return True
    return False

def scrape_citaty_info():
    print("Парсинг citaty.info...")
    url = "https://citaty.info/selection/citaty-stethema"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
            for p in paragraphs:
                if not p.startswith(('Цитаты Стетхема', 'Часто цитаты', 'Все эти мемные')):
                    filter_and_add(p)
    except Exception as e:
        print(f"Ошибка при парсинге citaty.info: {e}")

def scrape_reddit_json():
    print("Парсинг Reddit (r/rusAskReddit)...")
    url = "https://www.reddit.com/r/rusAskReddit/comments/16omboo/.json"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        def extract_comments(comment_list):
            for item in comment_list:
                if item['kind'] == 't1':
                    body = item['data'].get('body', '')
                    for line in body.split('\n'):
                        if "deleted" not in line:
                            filter_and_add(line)
                    replies = item['data'].get('replies')
                    if isinstance(replies, dict) and 'data' in replies:
                        extract_comments(replies['data'].get('children', []))
                        
        if len(data) > 1 and 'data' in data[1]:
            extract_comments(data[1]['data'].get('children', []))
    except Exception as e:
        print(f"Ошибка при парсинге Reddit: {e}")

def scrape_vk_article():
    print("Парсинг VK Статьи (Лонгрид)...")
    url = "https://vk.com/@430405572-luchshie-citaty-dzheisona-stethema-101-citata"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
            count = 0
            for p in paragraphs:
                # В статье цитаты обычно нумеруются
                p = re.sub(r'^\d+\.\s*', '', p)
                if filter_and_add(p):
                    count += 1
            print(f"Из статьи успешно добавлено {count} цитат.")
    except Exception as e:
        print(f"Ошибка парсинга статьи: {e}")

def scrape_vk_wall():
    print("Парсинг VK (Стены)...")
    vk_token = os.environ.get('VK_TOKEN')
    if not vk_token:
        print("ВНИМАНИЕ: VK_TOKEN не найден. Пропускаем VK API.")
        return
        
    vk_version = '5.131'
    # Расширенный список групп по наводке
    domains = [
        'jason_statham46', 
        'public96954008', 
        'jason_stathams',
        'dzheysonstetkhem', 
        'club225142165', 
        'mdk.jason.statham',
        'textmeme', 
        'txtmeme', 
        'club48417552'
    ]
    
    for domain in domains:
        print(f"Запрос постов из {domain}...")
        url = f"https://api.vk.com/method/wall.get?domain={domain}&count=100&v={vk_version}&access_token={vk_token}"
        
        # Если это clubXXXX или publicXXXX, метод wall.get с параметром domain иногда тоже срабатывает, 
        # но безопаснее передавать owner_id для таких случаев. Для простоты пока попробуем domain,
        # так как VK API умный и резолвит clubXXXX в domain.
        if domain.startswith(('club', 'public')):
            owner_id = "-" + re.sub(r'\D', '', domain)
            url = f"https://api.vk.com/method/wall.get?owner_id={owner_id}&count=100&v={vk_version}&access_token={vk_token}"

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
                if not text: continue
                
                # Строгий фильтр: пропускаем посты без упоминания Стетхема
                if not is_statham_quote(text):
                    continue
                
                # Некоторые паблики пишут подборки через пустую строку
                blocks = re.split(r'\n\s*\n', text)
                for block in blocks:
                    if filter_and_add(block):
                        added_count += 1
                        
            print(f"Из {domain} успешно добавлено: {added_count}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Ошибка при парсинге VK ({domain}): {e}")

def scrape_vk_board():
    print("Парсинг VK (Обсуждения)...")
    vk_token = os.environ.get('VK_TOKEN')
    if not vk_token: return
    vk_version = '5.131'
    
    # ID групп для парсинга обсуждений (jason_statham46 -> 31835783, club48417552 -> 48417552)
    # Знак минуса для group_id в board.getTopics не нужен
    group_ids = [31835783, 48417552]
    
    for gid in group_ids:
        print(f"Запрос обсуждений для группы {gid}...")
        try:
            url_topics = f"https://api.vk.com/method/board.getTopics?group_id={gid}&count=10&v={vk_version}&access_token={vk_token}"
            req = urllib.request.Request(url_topics, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as response:
                topics_data = json.loads(response.read().decode('utf-8'))
                
            topics = topics_data.get('response', {}).get('items', [])
            for topic in topics:
                title = topic.get('title', '').lower()
                # Ищем темы, где делятся цитатами
                if 'цитат' not in title and 'фраз' not in title and 'стетх' not in title:
                    continue
                    
                topic_id = topic.get('id')
                url_comments = f"https://api.vk.com/method/board.getComments?group_id={gid}&topic_id={topic_id}&count=100&v={vk_version}&access_token={vk_token}"
                req_comm = urllib.request.Request(url_comments, headers=HEADERS)
                with urllib.request.urlopen(req_comm, timeout=10) as response_comm:
                    comments_data = json.loads(response_comm.read().decode('utf-8'))
                    
                comments = comments_data.get('response', {}).get('items', [])
                added_count = 0
                for comment in comments:
                    text = comment.get('text', '')
                    if not text: continue
                    # В комментах обычно по одной цитате
                    for line in text.split('\n'):
                        if filter_and_add(line):
                            added_count += 1
                print(f"Из темы '{title}' добавлено {added_count} цитат.")
                time.sleep(0.5)
        except Exception as e:
            print(f"Ошибка парсинга обсуждений для группы {gid}: {e}")

def save_to_json():
    result_list = []
    # Сортируем для стабильности git diff
    for i, quote in enumerate(sorted(list(quotes_collection)), 1):
        result_list.append({
            "id": i,
            "text": quote,
            "author": "Jason Statham (Internet meme)"
        })
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result_list, f, ensure_ascii=False, indent=4)
    
    print(f"\nУспешно собрано {len(result_list)} уникальных, чистых цитат.")
    print(f"Данные сохранены в файл: {OUTPUT_FILE}")

if __name__ == "__main__":
    print("Запуск продвинутого комбайна по сбору цитат...")
    load_existing()
    
    scrape_citaty_info()
    scrape_reddit_json()
    scrape_vk_article()
    scrape_vk_wall()
    scrape_vk_board()
    
    save_to_json()
    print("Готово!")
