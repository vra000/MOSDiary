from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LessonDay(BaseModel):
    """Урок"""
    model_config = ConfigDict(extra='ignore')

    date: date
    """Дата проведения урока"""

    lessons: list[LesssonShortcut]
    """Уроки"""

    @model_validator(mode='before')
    @classmethod
    def combine_lesson_times_with_date(cls, value: Any) -> Any:
        if not isinstance(value, Mapping):
            return value

        lesson_date = value.get('date')
        if isinstance(lesson_date, str):
            try:
                lesson_date = date.fromisoformat(lesson_date)
            except ValueError:
                return value
        elif isinstance(lesson_date, datetime):
            lesson_date = lesson_date.date()

        lessons = value.get('lessons')
        if not isinstance(lesson_date, date) or not isinstance(lessons, list):
            return value

        prepared_lessons = []
        for raw_lesson in lessons:
            if not isinstance(raw_lesson, Mapping):
                prepared_lessons.append(raw_lesson)
                continue

            lesson = dict(raw_lesson)
            for field_name in ('begin_time', 'end_time'):
                raw_time = lesson.get(field_name)
                if isinstance(raw_time, str):
                    try:
                        lesson[field_name] = datetime.combine(
                            lesson_date,
                            time.fromisoformat(raw_time),
                        )
                    except ValueError:
                        pass
            prepared_lessons.append(lesson)

        return {**value, 'lessons': prepared_lessons}


class LesssonShortcut(BaseModel):
    """Урок в списке уроков дня"""
    model_config = ConfigDict(extra='ignore')

    id: int | None = Field(validation_alias='lesson_id')
    """ID урока"""

    begin_time: datetime
    """Время начала урока"""

    end_time: datetime
    """Время окончания урока"""

    #TODO: Описать. Возможно, ID мелодии звонка с окончания урока (bell с англ. - звонок), хотя странно
    bell_id: int | None

    subject_name: str | None
    """Название предмета"""

    #TODO: Типизировать в enum. Может быть "NORMAL"
    lesson_type: str

    group_id: int
    """ID группы предмета"""

    group_name: str
    """Название группы предмета"""

    #TODO: Описать. Может быть OO, EC, AE
    lesson_education_type: str

    #TODO: Описать. Возможно, оценка за поведение. Не знаю
    evaluation: Any | None

    #TODO: Описать. Вообще, в переводе с английского: "ID причины отсутствия"
    absence_reason_id: Any | None

    subject_id: int | None
    """ID предмета"""

    lesson_name: str | None
    """Название темы урока"""

    #TODO: Описать. Возможно, частный ID предмета в расписании на день
    schedule_item_id: int

    #TODO: Описать. Возможно, проводится ли урок виртуально
    is_virtual: bool