# FSTR Pass API

API для мобильного приложения туристов, предназначенное для работы с перевалами. Позволяет пользователям добавлять перевалы, модераторам проверять новые записи, а пользователям видеть статус модерации и свои внесённые данные.

---

## **Технологии**
- Python 3.10+
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- asyncpg
- Pydantic

---

## **Переменные окружения для подключения к базе**
- `FSTR_DB_HOST` — хост базы данных (по умолчанию `localhost`)
- `FSTR_DB_PORT` — порт базы (по умолчанию `5432`)
- `FSTR_DB_LOGIN` — логин пользователя базы
- `FSTR_DB_PASS` — пароль пользователя базы
- `FSTR_DB_NAME` — название базы (по умолчанию `fstr_db`)

---

## **Модели базы данных**

### **User**
- `id` — ID пользователя
- `email` — Email пользователя
- `fam` — Фамилия
- `name` — Имя
- `otc` — Отчество (опционально)
- `phone` — Телефон (опционально)
- `passes` — Список перевалов пользователя

### **Pass**
- `id` — ID перевала
- `beauty_title` — Красивое название перевала
- `title` — Основное название перевала
- `other_titles` — Другие названия перевала
- `connect` — Описание маршрута
- `add_time` — Время добавления
- `status` — Статус перевала (`new`, `pending`, `accepted`, `rejected`)
- `user_id` — ID пользователя
- `latitude`, `longitude` — Координаты перевала
- `height` — Высота (опционально)
- `level_winter`, `level_summer`, `level_autumn`, `level_spring` — Сложность по сезонам
- `images` — Список изображений

### **Image**
- `id` — ID изображения
- `data` — Base64 данных изображения
- `title` — Название изображения (опционально)
- `pass_id` — ID перевала

---

## **Эндпоинты**

### **POST /submitData**
Добавление нового перевала.

**Пример запроса:**
```json
{
  "beauty_title": "Перевал Пример",
  "title": "Test Pass3",
  "other_titles": "Тестовый",
  "connect": "Описание маршрута",
  "add_time": "2025-08-26T17:00:00",
  "user": {
    "email": "testuser@example.com",
    "fam": "Иванов",
    "name": "Петр"
  },
  "coords": {
    "latitude": "50.4501",
    "longitude": "30.5234",
    "height": "1200"
  },
  "level": {
    "winter": "1Б",
    "summer": "1А",
    "autumn": "",
    "spring": ""
  },
  "images": [
    {"data": "<картинка1_base64>", "title": "Седловина"},
    {"data": "<картинка2_base64>", "title": "Подъём"}
  ]
}
```

**Пример ответа:**
```json
{
  "status": 200,
  "message": null,
  "id": 3
}
```

---

### **GET /submitData/{id}**
Получение перевала по ID.

**Пример запроса:**  
`GET http://127.0.0.1:8000/submitData/3`

**Пример ответа:**
```json
{
  "id": 3,
  "beauty_title": "Перевал Пример",
  "title": "Test Pass3",
  "other_titles": "Тестовый",
  "connect": "Описание маршрута",
  "add_time": "2025-08-26T17:00:00",
  "status": "new",
  "user": {
    "email": "testuser@example.com",
    "fam": "Иванов",
    "name": "Петр",
    "otc": null,
    "phone": null
  },
  "coords": {
    "latitude": "50.4501",
    "longitude": "30.5234",
    "height": "1200"
  },
  "level": {
    "winter": "1Б",
    "summer": "1А",
    "autumn": "",
    "spring": ""
  },
  "images": [
    {"data": "<картинка1_base64>", "title": "Седловина"},
    {"data": "<картинка2_base64>", "title": "Подъём"}
  ]
}
```

---

### **PATCH /submitData/{id}**
Редактирование перевала (доступно только если `status = new`).

**Пример запроса:**
```json
{
  "beauty_title": "Перевал Обновлённый",
  "title": "Test Pass3 Updated",
  "other_titles": "Тестовый Обновлённый",
  "connect": "Описание маршрута обновлено",
  "add_time": "2025-08-27T12:00:00",
  "user": {
    "email": "testuser@example.com",
    "fam": "Иванов",
    "name": "Петр"
  },
  "coords": {
    "latitude": "50.4505",
    "longitude": "30.5240",
    "height": "1250"
  },
  "level": {
    "winter": "1Б",
    "summer": "1А",
    "autumn": "",
    "spring": ""
  },
  "images": []
}
```

**Пример ответа:**
```json
{
  "status": 200,
  "message": null,
  "id": 3
}
```

---

### **GET /submitData/?user__email=<email>**
Получение всех перевалов пользователя по email.

**Пример запроса:**  
`GET http://127.0.0.1:8000/submitData/?user__email=testuser@example.com`

**Пример ответа:**
```json
[
  {"status": 200, "message": null, "id": 3},
  {"status": 200, "message": null, "id": 2}
]
```

---

## **Пример проверки работы API в Postman**
1. **Добавление перевала** — POST /submitData  
   - Проверить, что в ответе есть `status=200` и ID новой записи
2. **Получение перевала по ID** — GET /submitData/{id}  
   - Проверить поля перевала, координаты, пользователя и изображения
3. **Редактирование перевала** — PATCH /submitData/{id}  
   - Проверить, что данные обновились
4. **Список всех перевалов пользователя** — GET /submitData/?user__email=<email>  
   - Проверить, что возвращается список ID всех перевалов пользователя

---

## **Примечания**
- Все даты должны быть в формате ISO: `YYYY-MM-DDTHH:MM:SS`
- Поля `beauty_title`, `other_titles`, `connect`, `images`, `otc`, `phone` — опциональные
- Изображения передаются в Base64
- Редактировать перевалы можно только если `status = new`
- API возвращает ID новой или изменённой записи для удобства
