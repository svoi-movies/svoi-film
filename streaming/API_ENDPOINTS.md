# API Endpoints

## Viewers (Зрители)

### Create Viewer
```http
POST /viewers
```

**Response 201:**
```json
{
  "id": "uuid",
  "created_at": "2025-12-20T12:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

### Delete Viewer
```http
DELETE /viewers/{viewer_id}
```

**Response 200:**
```json
{
  "id": "uuid",
  "created_at": "2025-12-20T12:00:00Z",
  "deleted_at": "2025-12-20T13:00:00Z",
  "is_deleted": true
}
```

## Titles (Тайтлы)

### Create Title
```http
POST /titles
```

**Response 201:**
```json
{
  "id": "uuid",
  "created_at": "2025-12-20T12:00:00Z"
}
```

## Episodes (Эпизоды)

### Create Episode
```http
POST /episodes
Content-Type: application/json

{
  "title_id": "uuid"
}
```

**Response 201:**
```json
{
  "episode": {
    "id": "uuid",
    "title_id": "uuid",
    "s3_key": "episodes/{episode_id}/source.mp4",
    "status": "DRAFT",
    "created_at": "2025-12-20T12:00:00Z",
    "uploaded_at": null,
    "processed_at": null,
    "published_at": null,
    "hidden_at": null
  },
  "upload_url": "https://s3.amazonaws.com/bucket/episodes/{episode_id}/source.mp4?signature=..."
}
```

### Mark Episode as Uploaded
```http
POST /episodes/{episode_id}/upload
```

**Response 200:**
```json
{
  "id": "uuid",
  "title_id": "uuid",
  "s3_key": "episodes/{episode_id}/source.mp4",
  "status": "SOURCE_UPLOADED",
  "created_at": "2025-12-20T12:00:00Z",
  "uploaded_at": "2025-12-20T12:05:00Z",
  "processed_at": null,
  "published_at": null,
  "hidden_at": null
}
```

### Mark Episode as Processed
```http
POST /episodes/{episode_id}/process
```

**Response 200:**
```json
{
  "id": "uuid",
  "title_id": "uuid",
  "s3_key": "episodes/{episode_id}/source.mp4",
  "status": "SOURCE_PROCESSED",
  "created_at": "2025-12-20T12:00:00Z",
  "uploaded_at": "2025-12-20T12:05:00Z",
  "processed_at": "2025-12-20T12:10:00Z",
  "published_at": null,
  "hidden_at": null
}
```

### Publish Episode
```http
POST /episodes/{episode_id}/publish
```

**Response 200:**
```json
{
  "id": "uuid",
  "title_id": "uuid",
  "s3_key": "episodes/{episode_id}/source.mp4",
  "status": "PUBLISHED",
  "created_at": "2025-12-20T12:00:00Z",
  "uploaded_at": "2025-12-20T12:05:00Z",
  "processed_at": "2025-12-20T12:10:00Z",
  "published_at": "2025-12-20T12:15:00Z",
  "hidden_at": null
}
```

### Hide Episode
```http
POST /episodes/{episode_id}/hide
```

**Response 200:**
```json
{
  "id": "uuid",
  "title_id": "uuid",
  "s3_key": "episodes/{episode_id}/source.mp4",
  "status": "HIDDEN",
  "created_at": "2025-12-20T12:00:00Z",
  "uploaded_at": "2025-12-20T12:05:00Z",
  "processed_at": "2025-12-20T12:10:00Z",
  "published_at": "2025-12-20T12:15:00Z",
  "hidden_at": "2025-12-20T13:00:00Z"
}
```

## Viewing Sessions (Сессии просмотра)

### Create Session
```http
POST /sessions
Content-Type: application/json

{
  "viewer_id": "uuid",
  "episode_id": "uuid"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "viewer_id": "uuid",
  "episode_id": "uuid",
  "progress_seconds": 0,
  "created_at": "2025-12-20T12:00:00Z",
  "completed_at": null,
  "is_completed": false
}
```

### Update Progress
```http
PATCH /sessions/{session_id}/progress
Content-Type: application/json

{
  "progress_seconds": 120
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "viewer_id": "uuid",
  "episode_id": "uuid",
  "progress_seconds": 120,
  "created_at": "2025-12-20T12:00:00Z",
  "completed_at": null,
  "is_completed": false
}
```

### Complete Session
```http
POST /sessions/{session_id}/complete
```

**Response 200:**
```json
{
  "id": "uuid",
  "viewer_id": "uuid",
  "episode_id": "uuid",
  "progress_seconds": 3600,
  "created_at": "2025-12-20T12:00:00Z",
  "completed_at": "2025-12-20T13:00:00Z",
  "is_completed": true
}
```

## Streaming

### Get Streaming URL
```http
POST /streaming/url
Content-Type: application/json

{
  "viewer_id": "uuid",
  "episode_id": "uuid"
}
```

**Response 200:**
```json
{
  "streaming_url": "https://s3.amazonaws.com/bucket/episodes/{episode_id}/source.mp4?signature=..."
}
```

**Response 403 (Forbidden):**
```json
{
  "detail": "Viewer is deleted"
}
```
или
```json
{
  "detail": "Episode is not published"
}
```

## Error Responses

### 404 Not Found
Когда запрашиваемая сущность не найдена.

### 409 Conflict
Когда операция нарушает бизнес-правила (например, попытка обработать неопубликованный эпизод).

```json
{
  "detail": "Can only upload source for draft episodes"
}
```

### 403 Forbidden
Когда у пользователя нет прав на операцию.

```json
{
  "detail": "Viewer is deleted"
}
```
