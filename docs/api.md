# API — FastAPI

## Запуск

```bash
opensaw serve --host 0.0.0.0 --port 8000
```

Swagger: `http://localhost:8000/docs`

## Эндпоинты

### `POST /v1/chat`

```json
{
  "message": "Привет!",
  "system_prompt": "optional",
  "max_tokens": 512,
  "temperature": 0.7,
  "use_memory": true
}
```

**Response:** `{"response": "...", "usage": {...}}`

### `GET /v1/chat/stream`

SSE-поток.

### `POST /v1/memory/add`

```json
{"text": "Пользователь любит Python"}
```

### `POST /v1/memory/search`

```json
{"query": "любимый язык"}
```

**Response:** `{"results": [{"text": "...", "similarity": 0.92}]}`

### `GET /v1/system/info`

```json
{"version": "1.1.0", "model": "...", "backend": "llama.cpp", "plugins": 2}
```

## curl

```bash
curl -s http://localhost:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Как дела?"}' | jq .
```
