# Mini App для записи на услуги (Telegram Web App)

Рабочий прототип Telegram-бота с встроенным Mini App для записи клиентов на услуги. Проект создан для портфолио.

## 🚀 Функционал

### Telegram-бот
- **/start** — приветствие, кнопки: "Записаться", "Мои записи", "Услуги", "Конкурс", "Контакты"
- **Mini App** — запись на услугу через Web App (выбор услуги, даты, времени, ввод имени и телефона)
- **Конкурс** — участие в розыгрыше скидки 20% (ввод ответа на загадку)
- **/admin** — админ-панель (просмотр записей, смена статусов, участники конкурса)
- Уведомления администратору о новых записях и участниках конкурса

### Mini App (Web App)
1. **Главный экран** — выбор услуги (5 услуг с иконками, ценами, длительностью)
2. **Выбор даты** — доступные даты (сегодня, завтра, послезавтра)
3. **Выбор времени** — слоты 10:00, 12:00, 14:00, 16:00, 18:00 (занятые недоступны)
4. **Форма записи** — имя, телефон, комментарий
5. **Экран успеха** — детали записи, кнопка возврата в бот
6. **Страница конкурса** — загадка, форма ответа, экран успеха

## 🛠 Технологический стек

| Компонент | Технологии |
|-----------|------------|
| Telegram-бот | Python 3.11+, aiogram 3.x |
| Mini App | HTML5, CSS3, Vanilla JS (ES6+) |
| База данных | SQLite (aiosqlite + SQLAlchemy 2.0) |
| Конфиг | python-dotenv, pydantic-settings |
| Хостинг бота | Render.com / VPS |
| Хостинг Mini App | Netlify (drag & drop) |

## 📁 Структура проекта

```
mini-app-booking/
├── .env.example          # Пример переменных окружения
├── .gitignore
├── requirements.txt      # Python зависимости
├── README.md             # Этот файл
├── main.py               # Точка входа бота
├── bot/
│   ├── config.py         # Настройки (pydantic-settings)
│   ├── database.py       # SQLAlchemy async engine/session
│   ├── models.py         # ORM модели (User, Service, TimeSlot, Booking, ContestEntry, Admin)
│   ├── init_data.py      # Инициализация тестовых данных
│   ├── keyboards/
│   │   └── reply.py      # Inline клавиатуры с WebApp кнопками
│   ├── handlers/
│   │   ├── __init__.py   # Регистрация всех роутеров
│   │   ├── start.py      # /start, мои записи, админка
│   │   ├── booking.py    # Обработка данных из Mini App (запись, отмена)
│   │   ├── contest.py    # Обработка ответов конкурса
│   │   └── admin.py      # Админские колбэки
│   └── utils/
│       └── webapp.py     # Валидация initData от Telegram Web App
└── webapp/
    ├── booking.html      # Mini App: запись на услугу
    ├── contest.html      # Mini App: конкурс
    ├── style.css         # Стили (современные, адаптивные, dark mode ready)
    └── script.js         # Логика Mini App (навигация, валидация, отправка данных)
```

## ⚙️ Установка и запуск

### 1. Клонирование и настройка

```bash
git clone <repo-url>
cd mini-app-booking
cp .env.example .env
```

### 2. Настройка `.env`

Отредактируйте `.env`:

```env
BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=sqlite:///./data/bot.db
ADMIN_CHAT_ID=ваш_telegram_id
WEBAPP_URL=https://ваш-сайт.netlify.app
```

- `BOT_TOKEN` — получите у [@BotFather](https://t.me/BotFather)
- `ADMIN_CHAT_ID` — ваш Telegram ID (узнайте у [@userinfobot](https://t.me/userinfobot))
- `WEBAPP_URL` — ссылка на задеплоенный Mini App (см. ниже)

### 3. Установка зависимостей

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 4. Запуск бота

```bash
python main.py
```

Бот создаст БД в `data/bot.db` и заполнит её тестовыми услугами и слотами.

## 🌐 Деплой Mini App на Netlify

1. Зайдите на [netlify.com](https://netlify.com) (или app.netlify.com/drop)
2. Перетащите папку `webapp/` в окно браузера
3. Получите ссылку вида `https://random-name.netlify.app`
4. Вставьте её в `.env` как `WEBAPP_URL`
5. В настройках бота укажите эту ссылку в кнопке `web_app`

> **Важно:** Netlify должен обслуживать файлы как статический сайт. `booking.html` — главная страница записи, `contest.html` — конкурс.

## 📱 Настройка бота в Telegram

1. Откройте [@BotFather](https://t.me/BotFather)
2. `/mybots` → выберите бота → `Bot Settings` → `Menu Button`
3. Установите URL: `https://ваш-сайт.netlify.app/booking.html`
4. Текст кнопки: `📅 Записаться`

Теперь при нажатии на кнопку меню откроется Mini App.

## 🗄 Модели данных

### User
- `id`, `telegram_id` (unique), `username`, `first_name`, `last_name`, `phone`, `created_at`

### Service
- `id`, `name`, `description`, `duration_minutes`, `price`, `service_type`, `is_active`

### TimeSlot
- `id`, `service_id`, `date`, `start_time`, `end_time`, `is_available`, `max_bookings`, `current_bookings`

### Booking
- `id`, `user_id`, `service_id`, `time_slot_id`, `client_name`, `client_phone`, `status`, `notes`, `created_at`

### ContestEntry
- `id`, `user_id`, `answer`, `created_at`

### Admin
- `id`, `telegram_id` (unique), `username`, `is_superadmin`, `created_at`

## ✅ Критерии приёмки

- [ ] Бот отвечает на `/start`
- [ ] Кнопка "Записаться" открывает Mini App
- [ ] В Mini App можно выбрать услугу, дату, время
- [ ] После формы — данные уходят в бот
- [ ] Бот присылает подтверждение пользователю
- [ ] Бот присылает уведомление админу
- [ ] Занятый слот становится недоступен
- [ ] Конкурс: ответ сохраняется в БД
- [ ] `/admin` показывает список записей
- [ ] Код задеплоен на Render (бот) и Netlify (Mini App)

## 📸 Скриншоты (добавьте свои)

| Бот: /start | Mini App: услуги | Mini App: форма |
|-------------|------------------|-----------------|
| ![](docs/start.jpg) | ![](docs/services.jpg) | ![](docs/form.jpg) |

## 📄 Лицензия

MIT — используйте свободно для портфолио и коммерческих проектов.

## 🤝 Контакты

- Telegram: [@your_username](https://t.me/your_username)
- Email: your@email.com
- GitHub: [github.com/yourname](https://github.com/yourname)

---

*Сделано для портфолио. Демонстрирует работу с Telegram Web App, aiogram 3, SQLAlchemy 2, современным CSS/JS.*