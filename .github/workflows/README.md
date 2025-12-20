# CI/CD Workflows

## Auth Service Pipeline

Автоматический CI/CD пайплайн для auth-сервиса включает:

### 🧪 Тестирование (test)
- **Линтер** (ruff check)
- **Форматирование** (ruff format)
- **Проверка типов** (mypy)
- **Unit тесты** (pytest tests/unit)
- **Integration тесты** (pytest tests/integrations)

### 🐳 Сборка и публикация (build-and-push-to-yc)
- Сборка Docker образа с использованием BuildKit
- Публикация в Yandex Container Registry с тремя тегами:
  - `latest` - последняя версия
  - `<sha>` - короткий хеш коммита
  - `<date>` - дата и время сборки
- Кеширование слоев для ускорения сборки

### 🚀 Деплой (deploy)
- Автоматический деплой в Yandex Serverless Containers
- Только для ветки `main`
- Конфигурация: 1 core, 512MB RAM, 4 concurrent requests

## Необходимые GitHub Secrets

Для работы пайплайна необходимо настроить следующие секреты в репозитории:

### Yandex Cloud
- `YC_KEYS` - JSON ключ сервисного аккаунта
- `YC_REGISTRY_ID` - ID Container Registry
- `YC_FOLDER_ID` - ID папки в Yandex Cloud
- `YC_CONTAINER_NAME` - Имя serverless container
- `YC_SA_ID` - ID сервисного аккаунта для контейнера

### Application Environment
- `ENV_POSTGRES_URL` - URL подключения к PostgreSQL (например: `postgresql+asyncpg://user:pass@host:5432/db`)
- `ENV_AMQP_URL` - URL подключения к RabbitMQ (например: `amqp://user:pass@host:5672`)
- `ENV_AUTH_TOKEN_URL` - URL для получения токена (например: `https://auth-service.example.com/auth/login`)
- `ENV_AUTH_REFRESH_URL` - URL для обновления токена (например: `https://auth-service.example.com/auth/refresh`)
- `ENV_JWT_ACCESS_KEY_TTL` - Время жизни access токена в формате ISO 8601 (например: `PT5M` = 5 минут)
- `ENV_JWT_REFRESH_TOKEN_TTL` - Время жизни refresh токена в формате ISO 8601 (например: `P7D` = 7 дней)
- `ENV_JWT_SIGNING_KEY` - Приватный RSA ключ для подписи JWT (в формате PEM, многострочный - используйте кавычки)
- `ENV_JWT_VERIFYING_KEY` - Публичный RSA ключ для проверки JWT (в формате PEM, многострочный - используйте кавычки)

## Триггеры запуска

Pipeline запускается при:
- Push в ветки `main` или `subscribes-service`
- Pull Request в ветку `main`
- Изменениях в директориях `auth/` или `commons/`

## Как получить YC_KEYS

```bash
# Создать сервисный аккаунт
yc iam service-account create --name github-ci

# Назначить роли
yc resource-manager folder add-access-binding <folder-id> \
  --role container-registry.images.pusher \
  --service-account-name github-ci

yc resource-manager folder add-access-binding <folder-id> \
  --role serverless.containers.admin \
  --service-account-name github-ci

# Создать ключ
yc iam key create \
  --service-account-name github-ci \
  --output key.json

# Содержимое key.json использовать как YC_KEYS
```

## Генерация JWT ключей

Для работы сервиса необходимо сгенерировать пару RSA ключей:

```bash
# Генерация приватного ключа (signing key)
openssl genrsa -out signing_key.pem 2048

# Генерация публичного ключа (verifying key)
openssl rsa -in signing_key.pem -pubout -out verifying_key.pem

# Для использования в GitHub Secrets нужно скопировать содержимое файлов
cat signing_key.pem    # Скопировать в ENV_JWT_SIGNING_KEY
cat verifying_key.pem  # Скопировать в ENV_JWT_VERIFYING_KEY
```

**Важно**: При добавлении многострочных ключей в GitHub Secrets вставляйте их как есть, включая заголовки `-----BEGIN RSA PRIVATE KEY-----` и `-----END RSA PRIVATE KEY-----`.

## Локальное тестирование

```bash
# Запустить тесты локально
cd auth
uv sync --group tests --group dev
uv run pytest tests/ -v

# Собрать образ локально
docker build -t auth-service:local \
  --build-arg MCS_NAME=auth \
  -f auth/Dockerfile .
```
