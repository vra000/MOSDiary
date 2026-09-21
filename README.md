<div align="center">

# MOSDiary

**Неофициальный асинхронный Python-клиент для школьного дневника МЭШ**

[![PyPI](https://img.shields.io/pypi/v/mosdiary?color=3775A9&label=PyPI&logo=pypi&logoColor=white)](https://pypi.org/project/mosdiary/0.1.0/)
[![Python](https://img.shields.io/pypi/pyversions/mosdiary?logo=python&logoColor=white)](https://pypi.org/project/mosdiary/0.1.0/)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](https://github.com/vra000/MOSDiary/blob/main/LICENSE)
[![AsyncIO](https://img.shields.io/badge/asyncio-ready-2C5BB4.svg)](https://docs.python.org/3/library/asyncio.html)

[Установка](#-установка) · [Быстрый старт](#-быстрый-старт) · [Авторизация](#-авторизация) · [Методы](#-доступные-методы)

</div>

MOSDiary предоставляет удобный типизированный интерфейс к данным электронного дневника [Московской Электронной Школы](https://school.mos.ru/). Библиотека построена на `asyncio` и возвращает готовые модели [Pydantic](https://docs.pydantic.dev/).

> [!IMPORTANT]
> Это неофициальный проект, не связанный с Департаментом образования и науки города Москвы или командой МЭШ. Внутреннее API МЭШ может измениться без предупреждения.

## ✨ Возможности

- вход по сохранённому `aupd_token` или QR-коду Mos ID;
- получение профиля и информации о семье;
- расписание уроков и событий за выбранный период;
- домашние задания;
- оценки по предметам и датам;
- полностью асинхронная работа через `aiohttp`;
- типизированные ответы на основе Pydantic-моделей;
- автоматическое управление HTTP-сессией через `async with`.

## 📦 Установка

Требуется **Python 3.11 или новее**.

```bash
python -m pip install mosdiary
```

Установка актуальной версии из репозитория:

```bash
python -m pip install git+https://github.com/vra000/MOSDiary.git
```

## 🚀 Быстрый старт

```python
import asyncio
from datetime import date, timedelta

from mosdiary import MOSDiaryClient


async def main() -> None:
    async with MOSDiaryClient(aupd_token="ваш_aupd_token") as diary:
        profile = await diary.get_base_info()
        print(f"Пользователь: {profile.full_name}")

        today = date.today()
        homework = await diary.get_homework(today, today + timedelta(days=7))

        for item in homework:
            print(f"{item.date:%d.%m} · {item.subject_name}: {item.homework}")


asyncio.run(main())
```

Контекстный менеджер автоматически закрывает сетевую сессию. Если клиент создаётся без `async with`, вызовите `await client.close()` самостоятельно.

## 🔐 Авторизация

### Готовый токен

Передайте cookie `aupd_token` при создании клиента:

```python
from mosdiary import MOSDiaryClient

client = MOSDiaryClient(aupd_token="ваш_aupd_token")
```

> [!CAUTION]
> `aupd_token` предоставляет доступ к данным дневника. Не публикуйте его, не добавляйте в Git и не записывайте в логи. Для приложений храните токен в переменной окружения или защищённом хранилище.

### Вход по QR-коду

```python
import asyncio

from mosdiary import MOSDiaryClient


async def main() -> None:
    async with MOSDiaryClient() as diary:
        login_url, expires = await diary.start_qr_login()
        print("Откройте ссылку и подтвердите вход:", login_url)

        aupd_token, refresh_token = await diary.wait_qr_login(expires)
        print("Вход выполнен")

        profile = await diary.get_base_info()
        print(profile.full_name)


asyncio.run(main())
```

Если Mos ID запрашивает второй фактор, передайте функцию получения кода. Для `sms` и `email` нужен шестизначный код, для `flash_call` — последние четыре цифры входящего номера:

```python
aupd_token, refresh_token = await diary.wait_qr_login(
    expires,
    get_code=lambda: input("Код подтверждения: "),
    verification_method="sms",
    trust_browser=False,
)
```

Метод `start_qr_login()` также умеет создавать PNG с QR-кодом:

```python
qr_png, expires = await diary.start_qr_login(return_type="qr")

with open("mos-id-qr.png", "wb") as file:
    file.write(qr_png)
```

## 📚 Доступные методы

| Метод | Результат | Назначение |
|---|---|---|
| `get_base_info()` | `UserInfo` | Основная информация о пользователе |
| `get_detail_info()` | `ProfileDeatail` | Расширенные данные профиля |
| `get_family_info()` | `Family` | Профиль, дети и представители семьи |
| `get_lessons(dates)` | `list[LessonDay]` | Краткое расписание на указанные даты |
| `get_schedule_events(from_date, to_date)` | `list[ScheduleEvent]` | Подробные события расписания |
| `get_homework(from_date, to_date)` | `list[Homework]` | Домашние задания за период |
| `get_marks()` | `list[SubjectMark]` | Сводные оценки по предметам |
| `get_date_marks(from_date, to_date)` | `list[Mark]` | Оценки за период |
| `refresh_session(role_id=1)` | `str` | Обновление токена после QR-входа |
| `logout()` | `bool` | Завершение текущей сессии |

Все даты передаются как объекты `datetime.date`. Ответы представлены Pydantic-моделями: их можно читать через атрибуты или преобразовывать в словари с помощью `model_dump()`.

### Пример расписания и оценок

```python
from datetime import date, timedelta

today = date.today()

events = await diary.get_schedule_events(today, today + timedelta(days=7))
for event in events:
    title = getattr(event, "subject_name", getattr(event, "title", "Событие"))
    print(event.start_at.strftime("%d.%m %H:%M"), title)

marks = await diary.get_date_marks(today - timedelta(days=30), today)
for mark in marks:
    print(mark.date.strftime("%d.%m"), mark.subject_name, mark.value)
```

## 🛠 Разработка

```bash
git clone https://github.com/vra000/MOSDiary.git
cd MOSDiary
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Сообщения об ошибках и предложения можно оставить в [GitHub Issues](https://github.com/vra000/MOSDiary/issues).

## 📄 Лицензия

Проект распространяется на условиях [GNU General Public License v3.0](https://github.com/vra000/MOSDiary/blob/main/LICENSE).

---

<div align="center">

Если библиотека оказалась полезной, поставьте проекту ⭐ на GitHub.

</div>
