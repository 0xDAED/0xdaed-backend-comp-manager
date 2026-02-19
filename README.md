Ниже — **нормальный production-style README** для твоего проекта (не студенческий, а как у настоящего open-source RMM).
Можешь просто сохранить как `README.md` в корень репозитория.

---

# 🧠 0xDAED — Realtime Remote Computer Management (RMM)

> Lightweight realtime Windows PC management system
> FastAPI + Redis + Postgres + WebSocket + Native .NET Agent

---

## ✨ Возможности

### 📡 Realtime мониторинг

* online/offline статус
* CPU / RAM / Disk usage
* список процессов
* last activity
* IP / MAC / OS / user

### 🎮 Управление ПК

* выполнить PowerShell команду
* kill process
* reboot / shutdown / sleep
* запуск программ
* планировщик задач

### ⚡ Архитектура realtime

* **heartbeat → online**
* **metrics → live stats**
* **processes → process list**
* **commands → pull model**
* **WebSocket → UI updates**

UI обновляется мгновенно без refresh.

---

## 🏗 Архитектура

```
                ┌─────────────────────┐
                │      Vue UI         │
                │   Pinia + WS        │
                └─────────┬───────────┘
                          │ WebSocket
                          ▼
┌──────────────────────────────────────────────┐
│                FastAPI API                   │
│                                              │
│  Agents API      Dashboard API    UI API     │
│  heartbeat       /dashboard/pcs   create cmd │
│  metrics         realtime push                │
│  processes                                     
│                                              │
└───────┬──────────────┬───────────────┬──────┘
        │              │               │
        ▼              ▼               ▼
     Redis          Postgres        WS Broker
 realtime state     persistent      fanout
 online/cache       commands/meta   updates
```

---

## 🖥 Windows Agent

Native C# (.NET 10) сервис.

Отправляет:

| Поток     | Частота | Назначение       |
| --------- | ------- | ---------------- |
| heartbeat | 60s     | online + команды |
| metrics   | 2s      | CPU/RAM/Disk     |
| processes | 5s      | список процессов |

Получает команды в ответ на heartbeat.

---

## 📂 Структура проекта

```
oxdaed/
│
├── server/                 # FastAPI backend
│   ├── app/
│   │   ├── modules/
│   │   │   ├── agents/
│   │   │   ├── commands/
│   │   │   ├── dashboard/
│   │   │   └── ws/
│   │   ├── db/
│   │   └── core/
│
├── agent/                  # .NET Windows agent
│   ├── Core/
│   ├── Api/
│   ├── SystemInfo/
│   └── Config/
│
├── frontend/               # Vue 3 UI
│   ├── stores/
│   ├── components/
│   └── composables/
│
└── bruno/                  # API tests
```

---

## 🚀 Быстрый запуск

### 1️⃣ Backend

```bash
cd server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

API:

```
http://127.0.0.1:8000/docs
```

---

### 2️⃣ Redis

```bash
docker run -p 6379:6379 redis
```

---

### 3️⃣ Postgres

```bash
docker run -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=oxdaed \
  postgres:16
```

---


## 🔁 Командный цикл

1. UI создаёт команду
2. Backend кладёт в Postgres
3. Агент получает в heartbeat
4. Агент ACK → выполняет → RESULT
5. Backend → WebSocket → UI

```
UI → POST /ui/commands
Agent ← heartbeat commands[]
Agent → command_ack
Agent → command_result
Server → WS task_update
UI обновляется
```

---

## 📡 WebSocket события

| Event       | Описание             |
| ----------- | -------------------- |
| pc_update   | обновление состояния |
| task_update | статус задачи        |
| pc_offline  | потеря соединения    |

---

## 🧪 Тестирование (Bruno)

```bash
bru run bruno/oxdaed --env local
```

Порядок:

```
heartbeat → metrics → processes → dashboard
```

---

## 🧠 Модель данных

### Redis (ephemeral)

* online state
* realtime metrics
* processes

### Postgres (persistent)

* computers
* commands
* results
* meta info

---

## 🔐 Команды агента

| Тип               | Описание          |
| ----------------- | ----------------- |
| RUN_SHELL         | PowerShell        |
| KILL_PROCESS      | kill pid          |
| REBOOT            | reboot PC         |
| SHUTDOWN          | shutdown          |
| SLEEP             | sleep             |
| REQUEST_PROCESSES | обновить процессы |

---

## 🧩 Пример команды

```json
{
  "pc_id": "uuid",
  "type": "RUN_SHELL",
  "payload": {
    "params": "Get-Process | select -First 5"
  }
}
```

---


## 👨‍💻 Автор

0xDAED experimental RMM platform
Realtime control infrastructure for Windows environments.


