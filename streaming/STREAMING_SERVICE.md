# Streaming Service

Микросервис стриминга видео для онлайн кинотеатра.

## Основные сущности

### Title (Тайтл)
Фильм или сериал в системе. Содержит только базовую информацию о создании.

### Episode (Эпизод)
Видео-контент, привязанный к тайтлу. Может быть фильмом (один эпизод на тайтл) или серией (множество эпизодов на тайтл).

**Статусы эпизода:**
- `DRAFT` - черновик, ссылка на загрузку создана
- `SOURCE_UPLOADED` - файл загружен в S3
- `SOURCE_PROCESSED` - видео обработано
- `PUBLISHED` - опубликовано и доступно для просмотра
- `HIDDEN` - скрыто от просмотра

### Viewer (Зритель)
Пользователь, который может просматривать видео.

### ViewingSession (Сессия просмотра)
Сессия просмотра эпизода зрителем с отслеживанием прогресса.

## Основной флоу работы

### 1. Создание эпизода и загрузка видео

```
POST /episodes
{
  "title_id": "uuid"
}

Response:
{
  "episode": {
    "id": "uuid",
    "title_id": "uuid",
    "s3_key": "episodes/{episode_id}/source.mp4",
    "status": "DRAFT",
    ...
  },
  "upload_url": "https://s3.../presigned-url"
}
```

Сервис:
1. Создает эпизод в статусе DRAFT
2. Генерирует S3 ключ для файла
3. Создает presigned URL для загрузки (PUT)
4. Возвращает эпизод и ссылку для загрузки

Клиент должен самостоятельно загрузить файл по presigned URL используя HTTP PUT.

### 2. Подтверждение загрузки

```
POST /episodes/{episode_id}/upload
```

После загрузки файла клиент дергает эту ручку. Сервис:
1. Меняет статус эпизода на SOURCE_UPLOADED
2. Публикует событие `episode.source_uploaded` в RabbitMQ
3. Воркер подхватывает событие и запускает обработку видео

### 3. Обработка видео (Воркер)

Воркер слушает очередь `streaming.video_processing` и обрабатывает события `episode.source_uploaded`.

В реальной реализации здесь должно происходить:
- Транскодирование видео в разные качества (720p, 1080p, 4K)
- Генерация HLS/DASH манифестов
- Извлечение метаданных (длительность, разрешение)
- Генерация превью/thumbnails

После обработки воркер вызывает:
```
POST /episodes/{episode_id}/process
```

Это меняет статус на SOURCE_PROCESSED.

### 4. Публикация эпизода

```
POST /episodes/{episode_id}/publish
```

Меняет статус на PUBLISHED. Теперь эпизод доступен для просмотра.

### 5. Получение ссылки на просмотр

```
POST /streaming/url
{
  "viewer_id": "uuid",
  "episode_id": "uuid"
}

Response:
{
  "streaming_url": "https://s3.../presigned-url"
}
```

Сервис проверяет:
- Зритель существует и не удален
- Эпизод опубликован (статус PUBLISHED)

Затем генерирует presigned URL для скачивания (GET) из S3.

### 6. Отслеживание прогресса

```
# Создание сессии просмотра
POST /sessions
{
  "viewer_id": "uuid",
  "episode_id": "uuid"
}

# Обновление прогресса
PATCH /sessions/{session_id}/progress
{
  "progress_seconds": 120
}

# Завершение просмотра
POST /sessions/{session_id}/complete
```

## Конфигурация

Сервис требует следующие переменные окружения:

### База данных
- `APP_DB__DSN` - PostgreSQL connection string

### RabbitMQ
- `APP_RABBIT__DSN` - RabbitMQ connection string

### S3
- `APP_S3__ENDPOINT_URL` - S3-совместимое хранилище URL
- `APP_S3__ACCESS_KEY_ID` - S3 access key
- `APP_S3__SECRET_ACCESS_KEY` - S3 secret key
- `APP_S3__BUCKET_NAME` - имя S3 бакета
- `APP_S3__REGION_NAME` - регион (по умолчанию us-east-1)
- `APP_S3__UPLOAD_EXPIRATION_SECONDS` - время жизни presigned URL для загрузки (по умолчанию 3600)
- `APP_S3__DOWNLOAD_EXPIRATION_SECONDS` - время жизни presigned URL для скачивания (по умолчанию 3600)

## Запуск

### API сервер
```bash
uvicorn streaming.api.app:app --host 0.0.0.0 --port 8000
```

### Воркер
```bash
python -m streaming.worker
```

### Миграции
```bash
alembic upgrade head
```

## Архитектура

Сервис построен на:
- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM
- **FastStream** - обработка событий из RabbitMQ
- **Dishka** - DI контейнер
- **boto3** - работа с S3
- **Alembic** - миграции БД

Используется Clean Architecture с разделением на слои:
- `domain/` - доменные модели и события
- `persistence/` - репозитории и схема БД
- `use_cases/` - бизнес-логика (команды)
- `api/` - HTTP API (FastAPI роуты и модели)
- `worker/` - обработчики событий
- `services/` - внешние сервисы (S3)
- `events/` - публикация событий

## Безопасность

- Все файлы загружаются и скачиваются через presigned URLs с ограниченным временем жизни
- Доступ к просмотру контролируется через проверку существования и статуса зрителя
- Только опубликованные эпизоды доступны для просмотра
