Moderator service
================

API surface translated to the moderation context from the diagram.

### Domain
- Модератор — пользователь с ролью `moderator` в auth-сервисе (порт `8001`), хранится связка `moderator.id` ↔ `auth_user.id`. Поля: `id`, `user_id`, `status` (`active`/`deleted`), `created_at`, `updated_at`.
- Запрос модерации — агрегат, фиксирующий запрос на проверку эпизода. Поля: `id`, `episode_id`, `content_owner_id`, `moderator_id` (появляется после решения), `status` (`requested`/`approved`/`rejected`), `created_at`, `updated_at`.
- Запрос модерации создает контент-овнер (роль `content-owner`). Решение принимает модератор (роль `moderator`). Создание/удаление модератора выполняет админ.
- События кладутся в outbox/exchange `moderator` и `moderation-request`.

### HTTP API
- `POST /moderators` — создать модератора. Тело: `{"user": {"email": "...", "first_name": "...", "last_name": "...", "password": "..."}}`. Запрос уходит в `http://auth:8001` с тем же bearer-токеном, пользователь создается с ролью `moderator`. Возвращает созданного модератора (201).
- `DELETE /moderators/{moderator_id}` — удалить/деактивировать модератора (200). Статус становится `deleted`.
- `GET /moderators/{moderator_id}` — получить модератора (200).
- `POST /moderation-requests` — запросить модерацию эпизода. Тело: `{"episode_id": "...", "content_owner_id": "..."}`. Возвращает созданный запрос (201).
- `POST /moderation-requests/{moderation_request_id}/approve` — разрешить публикацию/принять модерацию. Тело: `{"moderator_id": "..."}`. Возвращает обновленный запрос (200).
- `POST /moderation-requests/{moderation_request_id}/reject` — запретить публикацию/отклонить модерацию. Тело: `{"moderator_id": "..."}`. Возвращает обновленный запрос (200).
- `GET /moderation-requests/{moderation_request_id}` — получить запрос модерации (200).

### Events (routing keys)
- `moderator.{moderator_id}.created`
- `moderator.{moderator_id}.deleted`
- `moderation-request.{moderation_request_id}.requested`
- `moderation-request.{moderation_request_id}.approved`
- `moderation-request.{moderation_request_id}.rejected`
