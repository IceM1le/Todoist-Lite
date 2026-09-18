# Todoist-Lite

Легковесное приложение для управления задачами (todo list), построенное на **FastAPI**.

## Особенности

- REST API для управления задачами и пользователями
- Аутентификация через JWT токены
- Асинхронные задачи с помощью **Celery** и **Redis**
- Интеграция с **Telegram** для уведомлений
- PostgreSQL в качестве основной базы данных
- Alembic для миграций БД
- Docker и Docker Compose для контейнеризации
- CI/CD пайплайн с GitHub Actions (тесты + автодеплой в Docker Hub)
- Веб-интерфейс на HTML/CSS/JS

## Технологии

- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **База данных:** PostgreSQL 15
- **Кэш/Брокер:** Redis 7
- **Асинхронные задачи:** Celery
- **Аутентификация:** JWT (python-jose, passlib)
- **Миграции:** Alembic
- **Контейнеризация:** Docker, Docker Compose
- **Тестирование:** pytest, pytest-asyncio

## Установка и запуск

### Требования

- Python 3.10+
- Docker и Docker Compose (опционально)

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd todoist-lite
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/todo
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379/0
TELEGRAM_TOKEN=your_telegram_bot_token
```

### 3. Запуск через Docker Compose (рекомендуется)

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL на порту 5432
- Redis на порту 6379

### 4. Установка зависимостей и запуск приложения

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Применение миграций

```bash
alembic upgrade head
```

## Тестирование

```bash
pytest -v
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Главная страница |
| GET | `/login` | Страница входа |
| GET | `/register` | Страница регистрации |
| GET | `/ping` | Проверка доступности API |
| POST | `/api/v1/register` | Регистрация пользователя |
| POST | `/api/v1/login` | Вход (получение JWT токена) |
| GET | `/api/v1/tasks` | Получить список задач |
| POST | `/api/v1/tasks` | Создать задачу |
| PUT | `/api/v1/tasks/{id}` | Обновить задачу |
| DELETE | `/api/v1/tasks/{id}` | Удалить задачу |

## Telegram бот

Приложение поддерживает уведомления через Telegram. Для активации:
1. Создайте бота через @BotFather
2. Добавьте токен в `.env` (`TELEGRAM_TOKEN`)
3. Бот будет отправлять уведомления о новых задачах

## Структура проекта

```
.
├── alembic/              # Миграции базы данных
├── app/
│   ├── api/v1/          # API роуты
│   ├── core/            # Конфигурация, БД, безопасность
│   ├── models/          # SQLAlchemy модели
│   ├── schemas/         # Pydantic схемы
│   └── main.py          # Точка входа
├── static/              # Статические файлы
├── templates/           # HTML шаблоны
├── tests/               # Тесты
├── docker-compose.yml   # Docker Compose конфигурация
├── Dockerfile           # Docker образ
└── requirements.txt     # Зависимости Python
```

## Безопасность

- Пароли хешируются с помощью bcrypt
- JWT токены для аутентификации
- Валидация данных через Pydantic

## Лицензия

MIT

## Авторы

Разработано как учебный проект для демонстрации навыков работы с FastAPI, Celery, PostgreSQL и Docker.
