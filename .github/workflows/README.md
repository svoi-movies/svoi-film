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
- `ENV_POSTGRES_URL` - URL подключения к PostgreSQL
- `ENV_AMQP_URL` - URL подключения к RabbitMQ
- `ENV_JWT_SECRET` - Секретный ключ для JWT
- `ENV_JWT_ALGORITHM` - Алгоритм JWT (например, HS256)
- `ENV_JWT_EXPIRE_MINUTES` - Время жизни токена в минутах

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
