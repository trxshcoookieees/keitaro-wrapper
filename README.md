# Keitaro Wrapper

Веб-приложение для создания и редактирования рекламных кампаний в [Keitaro](https://keitaro.io/) через AdminAPI

Выполнено в рамках тестового задания

## Требования
- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20.9+
- pnpm
- Docker

## Установка и запуск
### 1. Клонирование репозитория
```bash
git clone https://github.com/trxshcoookieees/keitaro-wrapper.git
cd keitaro-wrapper
```
### 2. Запуск PostgreSQL
Из корневой директории проекта:
```bash
docker compose up -d db
```

В дальнейшем PostgreSQL будет доступен на `localhost:5432`

Параметры подключения по умолчанию:

| Параметр | Значение |
|---|---|
| Database | `keitaro_wrapper` |
| User | `web` |
| Password | `postgres` |
| Port | `5432` |

### 3. Настройка Backend
Перейдите в директорию backend:
```bash
cd backend
```

Создайте файл `.env` на основе примера:
```bash
cp .env.example .env
```

Настройте переменные окружения:
```env
DATABASE_URL=postgresql+psycopg://web:postgres@localhost:5432/keitaro_wrapper
KEITARO_BASE_URL=https://keitaro-for-tests.etolegko.com/admin_api/v1
KEITARO_API_KEY=your_api_key
```

`KEITARO_BASE_URL` — адрес Admin API Keitaro.

`KEITARO_API_KEY` — API-ключ, полученный в админ-панели Keitaro.

Установите зависимости:
```bash
uv sync
```

Примените миграции базы данных:
```bash
uv run alembic upgrade head
```

Запустите backend:
```bash
uv run uvicorn app.main:app --reload
```

Backend будет доступен по адресу: http://localhost:8000

Swagger UI: http://localhost:8000/docs

### 4. Настройка Frontend
Откройте второй терминал и перейдите в директорию frontend:
```bash
cd frontend
```
Создайте файл `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/keitaro
```

Установите зависимости:
```bash
pnpm install
```

Запустите frontend:
```bash
pnpm dev
```

Frontend будет доступен по адресу: http://localhost:3000

## Проверка работы

После запуска приложения можно проверить следующие сценарии:
1. Создать кампанию, указав название, GEO, домен, группу, источник трафика и офферы.
2. Убедиться, что в Keitaro созданы GEO-поток и поток офферов.
3. Открыть существующую кампанию в редакторе.
4. Добавить новый оффер и проверить перераспределение долей.
5. Закрепить долю одного из офферов и добавить ещё один оффер.
6. Удалить оффер и проверить пересчёт долей.
7. Нажать Push и проверить, что изменения применились в Keitaro.