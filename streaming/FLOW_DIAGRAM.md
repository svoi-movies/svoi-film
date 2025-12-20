# Диаграмма потока работы Streaming Service

## 1. Загрузка нового эпизода

```
Клиент                  API Service              S3              RabbitMQ           Worker
  |                          |                    |                  |                 |
  |--POST /episodes--------->|                    |                  |                 |
  |  {title_id}              |                    |                  |                 |
  |                          |                    |                  |                 |
  |                          |--generate_upload_presigned_url()----->|                 |
  |                          |                    |                  |                 |
  |                          |<---presigned_url---|                  |                 |
  |                          |                    |                  |                 |
  |                          |--save Episode(DRAFT)                  |                 |
  |                          |                    |                  |                 |
  |<--{episode, upload_url}--|                    |                  |                 |
  |                          |                    |                  |                 |
  |                          |                    |                  |                 |
  |==PUT video to upload_url===================>|                  |                 |
  |                          |                    |                  |                 |
  |<-200 OK=====================                  |                  |                 |
  |                          |                    |                  |                 |
  |                          |                    |                  |                 |
  |--POST /episodes/{id}/upload----------------->|                  |                 |
  |                          |                    |                  |                 |
  |                          |--update status=SOURCE_UPLOADED        |                 |
  |                          |                    |                  |                 |
  |                          |--publish event(episode.source_uploaded)--------------->|
  |                          |                    |                  |                 |
  |<--{episode}--------------|                    |                  |                 |
  |                          |                    |                  |                 |
  |                          |                    |                  |--subscribe----->|
  |                          |                    |                  |                 |
  |                          |                    |                  |                 |--process video
  |                          |                    |                  |                 |  (transcode, etc)
  |                          |                    |                  |                 |
  |                          |<--POST /episodes/{id}/process-------------------------|
  |                          |                    |                  |                 |
  |                          |--update status=SOURCE_PROCESSED       |                 |
  |                          |                    |                  |                 |
  |                          |---200 OK---------------------------------------->|
```

## 2. Публикация и просмотр эпизода

```
Клиент                  API Service              S3
  |                          |                    |
  |--POST /episodes/{id}/publish---------------->|
  |                          |                    |
  |                          |--update status=PUBLISHED
  |                          |                    |
  |<--{episode}--------------|                    |
  |                          |                    |
  |                          |                    |
  |--POST /streaming/url---->|                    |
  |  {viewer_id, episode_id} |                    |
  |                          |                    |
  |                          |--check viewer exists & not deleted
  |                          |--check episode status=PUBLISHED
  |                          |                    |
  |                          |--generate_download_presigned_url()--->|
  |                          |                    |
  |                          |<---presigned_url---|
  |                          |                    |
  |<--{streaming_url}--------|                    |
  |                          |                    |
  |==GET video from streaming_url===============>|
  |                          |                    |
  |<-Video stream================================|
```

## 3. Отслеживание просмотра

```
Клиент                  API Service
  |                          |
  |--POST /sessions--------->|
  |  {viewer_id, episode_id} |
  |                          |
  |                          |--create ViewingSession(progress=0)
  |                          |
  |<--{session}--------------|
  |                          |
  |                          |
  | ... просмотр видео ...   |
  |                          |
  |--PATCH /sessions/{id}/progress-------------->|
  |  {progress_seconds: 120} |
  |                          |
  |                          |--update session progress
  |                          |
  |<--{session}--------------|
  |                          |
  |                          |
  | ... завершение ...       |
  |                          |
  |--POST /sessions/{id}/complete--------------->|
  |                          |
  |                          |--mark session as completed
  |                          |
  |<--{session}--------------|
```

## Ключевые моменты

1. **Presigned URLs**: Клиент напрямую работает с S3, сервис только генерирует временные ссылки
2. **Асинхронная обработка**: Обработка видео происходит в фоне через RabbitMQ
3. **Статусы**: Четкий lifecycle эпизода через статусы
4. **Авторизация**: Проверка прав доступа перед выдачей streaming URL
5. **Прогресс**: Отслеживание просмотра через сессии
