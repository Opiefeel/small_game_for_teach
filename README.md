Поддерживает Python <=3.12.x (ждём обновления pydantic)

Функционал
	•	Авторизация по email с получением JWT на почту
	•	Начало и завершение игровой сессии
	•	Удары по кротам (7 дырок, очки за серию)
	•	Ведение статистики пользователя и истории ударов
	•	Swagger UI для тестирования API

Быстрый старт

1. Клонируй репозиторий через команду git clone <repo-url>
cd small_game_for_teach

2. Создай и активируй виртуальное окружение python3.12 -m venv venv
source venv/bin/activate

3. Установи зависимости pip install --upgrade pip
pip install -r requirements.txt

4. Создай файл .env в корне проекта туда надо вставить свой SECRET_KEY=your_secret_key

p.s Секретный ключ можно сгенерировать:python3 -c "import secrets; print(secrets.token_urlsafe(32))"

5. Создай структуру таблиц python3 app/create_tables.py

6. Запусти MailHog для перехвата писем (если тестируешь email)
Для мака так:
brew install mailhog
mailhog

Для винды посмотри тут https://github.com/mailhog/MailHog

Почта будет доступна на http://localhost:8025.

7. Запусти серверuvicorn app.main:app --reload

Как пользоваться
	1.	Открой Swagger UI: http://127.0.0.1:8000/docs↗
	2.	Запроси токен на свою почту через /auth/request
	3.	Найди письмо в MailHog, скопируй токен
	4.	Вставь токен через кнопку “Authorize” в Swagger UI
	5.	Играй:
	▫	‎⁠/start⁠ — начать игру
	▫	‎⁠/hit⁠ — ударить по дырке
	▫	‎⁠/end⁠ — завершить игру и посмотреть финальную статистику
	▫	‎⁠/me⁠ — посмотреть свою статистику

Прямой доступ к базе

База данных — обычный SQLite-файл называться будет ‎⁠wackamole.db⁠.  Можно открыть через любой GUI-клиент (DB Browser for SQLite, DBeaver) или через консоль:sqlite3 wackamole.db
.tables (выбери табличку)
SELECT * FROM users;
SELECT * FROM requests;

FAQ:
	•	Ошибка SMTP: Запусти MailHog или пропиши реальные SMTP-настройки в ‎⁠.env⁠.
	•	Ошибка “no such table”: Не забудь создать таблицы через ‎⁠python3 app/create_tables.py⁠.
	•	Проблемы с токеном: Убедись, что вставляешь только сам JWT, без “Bearer “.