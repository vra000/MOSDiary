from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from ..enums import ScheduleEventType
from .marks import ScheduleEventMark


class _ScheduleEventBase(BaseModel):
    """Общие поля события расписания"""
    model_config = ConfigDict(extra='ignore')

    id: int
    """ID события"""

    #TODO: Описать
    source_id: str

    source: ScheduleEventType
    """Источник события"""

    start_at: datetime
    """Время начала события"""

    finish_at: datetime
    """Время окончания события"""


class ScheduleLesson(_ScheduleEventBase):
    """Урок из расписания"""

    source: Literal[ScheduleEventType.LESSON]
    """Источник события"""

    is_cancelled: bool = Field(validation_alias='cancelled')
    """Отменено ли событие"""

    #TODO: Описать. Может быть "NORMAL"
    lesson_type: str

    #TODO: Описать. Может быть THEMATIC_TEST (контрольная работа)
    course_lesson_type: str | None

    #TODO: Описать
    lesson_form: Any | None

    #TODO: Описать. Возможно, есть ли замена
    is_replaced: bool = Field(validation_alias='replaced')

    room_name: str
    """Название кабинета"""

    room_number: str
    """Номер кабинета"""

    subject_id: int
    """ID предмета"""

    subject_name: str
    """Название предмета"""

    #TODO: Описать. Возможно, ссылка на присоединение
    link_to_join: Any | None

    #TODO: Описать
    health_status: Any | None

    #TODO: Описать
    absence_reason_id: Any | None

    #TODO: Описать
    nonattendance_reason_id: Any | None

    homework: ScheduleEventHomework
    """Домашнее задание к событию"""

    marks: list[ScheduleEventMark] | None
    """Оценки за урок"""

    is_missed_lesson: bool
    """Пропустил ли урок"""


class ScheduleOlympiad(_ScheduleEventBase):
    """Олимпиада из расписания"""

    source: Literal[ScheduleEventType.OLYMPIAD]
    """Источник события"""

    title: str
    """Название события"""

    description: str
    """Описание события"""

    address: str | None
    """Адрес события"""

    format_name: str
    """Формат события"""

    url: str
    """Ссылка на событие"""

    stage: str
    """Этап события"""

    subjects: list[ScheduleEventSubject]
    """Предметы события"""


class ScheduleExtraCurricular(_ScheduleEventBase):
    """Внеурочное событие из расписания"""

    source: Literal[ScheduleEventType.EC]
    """Источник события"""

    is_cancelled: bool = Field(validation_alias='cancelled')
    """Отменено ли событие"""

    is_replaced: bool = Field(validation_alias='replaced')
    """Заменено ли событие"""

    room_name: str
    """Название кабинета"""

    room_number: str
    """Номер кабинета"""

    subject_name: str
    """Название события"""

    #TODO: Описать
    health_status: Any | None

    #TODO: Описать
    absence_reason_id: Any | None

    #TODO: Описать
    nonattendance_reason_id: Any | None

    homework: ScheduleEventHomework
    """Домашнее задание к событию"""

    marks: list[ScheduleEventMark] | None
    """Оценки за событие"""

    is_missed_lesson: bool
    """Пропущено ли событие"""


class ScheduleAdditionalEducation(_ScheduleEventBase):
    """Событие дополнительного образования из расписания"""

    source: Literal[ScheduleEventType.AE]
    """Источник события"""

    subject_name: str
    """Название события"""

    room_name: None
    """Название кабинета"""

    room_number: None
    """Номер кабинета"""

    #TODO: Описать
    esz_field_id: int

    #TODO: Описать
    lesson_theme: Any | None

    #TODO: Описать
    health_status: Any | None

    #TODO: Описать
    absence_reason_id: Any | None

    #TODO: Описать
    nonattendance_reason_id: Any | None

    is_missed_lesson: bool
    """Пропущено ли событие"""


ScheduleEvent: TypeAlias = (
    ScheduleLesson
    | ScheduleOlympiad
    | ScheduleExtraCurricular
    | ScheduleAdditionalEducation
)
"""Событие расписания"""


def parse_schedule_event(data: Any)-> ScheduleEvent:
    """Создать модель события расписания по значению `source`.

    Returns:
        ScheduleEvent: Модель, соответствующая типу события в поле `source`.
    """
    if isinstance(data, dict):
        try:
            source = ScheduleEventType(data.get('source'))
        except ValueError:
            raise ValueError(f"Неподдерживаемый source события расписания: {data.get('source')!r}") from None

        if source == ScheduleEventType.LESSON:
            return ScheduleLesson.model_validate(data)
        if source == ScheduleEventType.OLYMPIAD:
            return ScheduleOlympiad.model_validate(data)
        if source == ScheduleEventType.EC:
            return ScheduleExtraCurricular.model_validate(data)
        if source == ScheduleEventType.AE:
            return ScheduleAdditionalEducation.model_validate(data)
        raise ValueError(f'Неподдерживаемый source события расписания: {source.value!r}')
    raise ValueError('Событие расписания должно быть JSON-объектом')


class ScheduleEventSubject(BaseModel):
    """Предмет события расписания"""
    model_config = ConfigDict(extra='ignore')

    name: str
    """Название предмета"""


class ScheduleEventHomework(BaseModel):
    """Д/З для события в расписании"""
    model_config = ConfigDict(extra='ignore')

    #TODO: Описать. И возможно составить IntEnum класс
    presence_status_id: int

    total_count: int

    execute_count: int

    descriptions: list[str]
    """Тексты домашних заданий"""

    materials: ScheduleEventHomeworkMaterial | None
    """Материалы"""


class ScheduleEventHomeworkMaterial(BaseModel):
    """Материал Д/З для события в расписании"""
    model_config = ConfigDict(extra='ignore')

    #TODO: Описать
    count_execute: int

    #TODO: Описать
    count_learn: int

    #TODO: Описать
    count_homework: int