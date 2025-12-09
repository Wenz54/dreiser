# 🔐 Быстрый гайд по входу

## Учетные данные

```
Username: admin
Password: Admin123!Secret
```

**ВАЖНО: Используй именно Username, а не Email!**

---

## Через Frontend

1. Открой: **http://localhost:3000**
2. На странице Login введи:
   - **Username**: `admin`
   - **Password**: `Admin123!Secret`
   - **2FA Code**: оставь пустым
3. Нажми **Login**

---

## Если не получается войти

### Проверь что вводишь правильно:
- ✅ **Username**: `admin` (не email!)
- ✅ **Password**: `Admin123!Secret` (с заглавными буквами и символом!)

### Распространенные ошибки:
- ❌ Вводишь `admin@draizer.app` вместо `admin`
- ❌ Неправильный регистр в пароле
- ❌ Забыл символ `!` в пароле

---

## Через API напрямую (для проверки)

### PowerShell:
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
  -Method Post `
  -Body '{"username":"admin","password":"Admin123!Secret"}' `
  -ContentType "application/json"

$response.access_token
```

### curl:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!Secret"}'
```

---

## Swagger UI (самый простой способ!)

1. Открой: **http://localhost:8000/docs**
2. Найди **POST /api/v1/auth/login**
3. Нажми **"Try it out"**
4. Введи:
   ```json
   {
     "username": "admin",
     "password": "Admin123!Secret"
   }
   ```
5. Нажми **Execute**
6. Скопируй `access_token` из ответа
7. Нажми **"Authorize"** (замок вверху)
8. Вставь токен
9. Теперь можешь тестировать все endpoints!

---

## Создать нового пользователя

### Через API:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "username": "testuser",
    "password": "TestPass123!"
  }'
```

### Через Frontend:
1. http://localhost:3000/register
2. Заполни форму
3. Используй **username** для входа

---

## Проверка статуса системы

### Backend:
```
http://localhost:8000/health
```
Должен вернуть: `{"status":"healthy"}`

### Frontend:
```
http://localhost:3000
```
Должна открыться страница входа

### Docker:
```bash
docker-compose ps
```
Все сервисы должны быть **Up**

---

## Если ничего не помогает

### 1. Пересоздай пользователя:
```bash
docker exec draizer_backend python create_user.py
```

### 2. Проверь логи:
```bash
docker-compose logs backend | tail -50
```

### 3. Перезапусти систему:
```bash
docker-compose restart
```

---

## Успешный вход выглядит так:

**Frontend Console (F12):**
```
Login successful!
✅ Redirect to dashboard
```

**Backend Logs:**
```
INFO: POST /api/v1/auth/login 200 OK
```

**В браузере:**
- URL изменится на http://localhost:3000/
- Увидишь Dashboard с балансом $1000

---

**Готово! Теперь должно работать! 🚀**







