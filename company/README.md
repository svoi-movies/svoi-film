Company service
===============

API surface translated to the company context from the diagram.

### Domain
- Компания — агрегат с полями `id`, `name`, `status` (`active`/`deleted`), `created_at`, `updated_at`.
- Контент-овнер — представитель компании, который управляет загрузкой и редактированием тайтлов. Создается как пользователь с ролью `content-owner` в auth-сервисе (порт `8001`), хранится связка `content_owner.id` ↔ `auth_user.id`. Поля: `id`, `user_id` (из auth), `company_id`, `permissions` (массив действий, например `upload_titles`, `edit_titles`, `request_moderation`), `status`, `created_at`, `updated_at`.
- Операции компании выполняет админ (`Authorization: Bearer <token>`, роль `admin`). Для контент-овнеров через `/content-owners` используется роль `moderator` (админ тоже подходит). Токен из входящего запроса пробрасывается при обращении к auth при добавлении контент-овнера.
- События кладутся в outbox/exchange `company` и `content-owner`.

### HTTP API
- `POST /companies` — создать компанию. Тело: `{"name": "..."}`. Возвращает созданную компанию (201).
- `POST /companies/{company_id}/content-owners` — добавить контент-овнера в компанию. Тело:
  - `user`: данные для создания пользователя в auth (`email`, `first_name`, `last_name`, `password`); запрос уходит в `http://auth:8001` с тем же bearer-токеном, пользователь создается с ролью `content-owner`.
  - `permissions`: список прав для работы с тайтлами.
  Возвращает созданного контент-овнера (201).
- `PATCH /companies/{company_id}/content-owners/{content_owner_id}/permissions` — изменить права контент-овнера. Тело: `{"permissions": ["upload_titles", ...]}`. Возвращает обновленный ресурс (200).
- `DELETE /companies/{company_id}/content-owners/{content_owner_id}` — удалить/деактивировать контент-овнера (200). Статус становится `deleted`.
- `GET /companies/{company_id}` — получить компанию (200).
- `GET /companies/{company_id}/content-owners/{content_owner_id}` — получить контент-овнера (200).
- `POST /content-owners` — создать контент-овнера. Тело:
  - `user`: данные для создания пользователя в auth (`email`, `first_name`, `last_name`, `password`); запрос уходит в `http://auth:8001` с тем же bearer-токеном, пользователь создается с ролью `content-owner`.
  - `company_id`: идентификатор компании, которую представляет контент-овнер.
  - `permissions`: список прав для работы с тайтлами.
  Возвращает созданного контент-овнера с `id` и привязанным `user_id` (201).
- `PATCH /content-owners/{id}/permissions` — изменить права контент-овнера. Тело: `{"permissions": ["upload_titles", ...]}`. Возвращает обновленный ресурс (200).
- `DELETE /content-owners/{id}` — удалить/деактивировать контент-овнера (200). Статус становится `deleted`.
- `GET /content-owners/{id}` — получить текущее состояние контент-овнера (200).

### Events (routing keys)
- `company.{company_id}.created`
- `company.{company_id}.content-owner.added`
- `company.{company_id}.content-owner.permissions-updated`
- `company.{company_id}.content-owner.removed`
- `content-owner.{id}.created`
- `content-owner.{id}.permissions-updated`
- `content-owner.{id}.deleted`
