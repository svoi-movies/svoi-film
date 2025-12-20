Content-owner service
=====================

API surface translated to the content-owner context from the diagram.

### Domain
- Content owner — представитель компании, который управляет загрузкой и редактированием тайтлов. Создается как пользователь с ролью `content-owner` в auth-сервисе (порт `8001`), хранится связка `content_owner.id` ↔ `auth_user.id`.
- Поля ресурса: `id`, `user_id` (из auth), `company_id`, `permissions` (массив действий, например `upload_titles`, `edit_titles`, `request_moderation`), `status` (`active`/`deleted`), `created_at`, `updated_at`.
- Все операции выполняет модератор (`Authorization: Bearer <token>`). Токен из входящего запроса пробрасывается при обращении к auth.
- События кладутся в outbox/exchange `content-owner`: создан, права изменены, удален.

### HTTP API
- `POST /content-owners` — создать контент-овнера. Тело:
  - `user`: данные для создания пользователя в auth (`email`, `first_name`, `last_name`, `password`); запрос уходит в `http://auth:8001` с тем же bearer-токеном, пользователь создается с ролью `content-owner`.
  - `company_id`: идентификатор компании, которую представляет контент-овнер.
  - `permissions`: список прав для работы с тайтлами.
  Возвращает созданный контент-овнер с `id` и привязанным `user_id` (201).
- `PATCH /content-owners/{id}/permissions` — изменить права контент-овнера. Тело: `{"permissions": ["upload_titles", ...]}`. Возвращает обновленный ресурс (200).
- `DELETE /content-owners/{id}` — удалить/деактивировать контент-овнера (200). Статус становится `deleted`.
- `GET /content-owners/{id}` — получить текущее состояние контент-овнера (200).

### Events (routing keys)
- `content-owner.{id}.created`
- `content-owner.{id}.permissions-updated`
- `content-owner.{id}.deleted`
