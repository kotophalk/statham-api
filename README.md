# Statham API 🕶️

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)

**Statham API** — это сверхбыстрое REST API для получения эталонных пацанских мемов-цитат Джейсона Стэтхэма. 
Идеально подходит для Telegram-ботов, генераторов статусов во ВКонтакте, пет-проектов и просто для поднятия настроения.

База содержит **более 2100** вручную отобранных, дедуплицированных и очищенных от мусора цитат.

## 🚀 Фичи
- **Случайные цитаты:** Получение одной или сразу нескольких случайных мудростей.
- **Пагинация:** Удобный перебор всей базы.
- **CORS:** API готово к использованию напрямую из браузера (frontend-приложения).
- **Авто-документация:** Swagger UI из коробки (эндпоинт `/docs`).
- **Быстрота:** Написано на FastAPI, база загружается в оперативную память.

## 📦 Эндпоинты

| Метод | Маршрут | Описание |
|---|---|---|
| `GET` | `/` | Проверка статуса API и количество цитат в базе |
| `GET` | `/api/v1/quote/random` | Получить 1 случайную цитату |
| `GET` | `/api/v1/quote/random?count=5` | Получить 5 случайных цитат (от 1 до 50) |
| `GET` | `/api/v1/quote/{id}` | Получить конкретную цитату по её `id` |
| `GET` | `/api/v1/quotes?limit=50&offset=0` | Получить список всех цитат с пагинацией |

### Пример ответа
```json
{
    "id": 142,
    "text": "Когда не выносят пиво в баре, выношу весь бар",
    "author": "Jason Statham (Internet meme)"
}
```

## 🛠️ Установка и запуск

Самый простой и чистый способ развернуть API на своем сервере — использовать **Docker**.

1. Склонируйте репозиторий:
```bash
git clone https://github.com/kotophalk/statham-api.git
cd statham-api
```

2. Соберите Docker-образ:
```bash
docker build -t statham-api .
```

3. Запустите контейнер (API будет доступно на порту 8000):
```bash
docker run -d -p 8000:8000 --name statham-api --restart unless-stopped statham-api
```

### Запуск без Docker (через venv)
Если вы хотите запустить проект локально для разработки:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Документация
После запуска перейдите по адресу `http://localhost:8000/docs`, чтобы открыть интерактивную Swagger-документацию, где можно протестировать все методы прямо в браузере.

## 🤝 Вклад в проект
Если вы нашли опечатку или хотите добавить новую партию мощных цитат:
1. Добавьте их в файл `statham_quotes.json`.
2. Убедитесь, что формат соблюден (id, text, author).
3. Создайте Pull Request!
