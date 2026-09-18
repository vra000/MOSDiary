from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Any


class Homework(BaseModel):
    """Домашнее задание"""
    model_config = ConfigDict(extra='ignore')

    #TODO: Описать
    type: str

    description: str
    """Описание Д/З"""

    #TODO: Описать
    comments: list

    #TODO: Описать
    materials: list

    homework: str
    """Текст Д/З"""

    homework_entry_student_id: int
    """ID ученика для Д/З"""

    #TODO: Описать
    attachments: list

    subject_id: int
    """ID предмета"""

    group_id: int
    """ID группы предмета"""

    date: date
    """Дата, на которую задано Д/З"""

    assigned_on: date = Field(validation_alias='date_assigned_on')
    """Дата создания Д/З"""

    subject_name: str
    """Название предмета"""

    lesson_ends_at: datetime = Field(validation_alias='lesson_date_time')
    """Дата окончания урока"""

    is_done: bool
    """Д/З помечено как выполненное"""

    has_teacher_answer: bool
    """Ответил ли учитель на прикреплённое Д/З"""

    id: int = Field(validation_alias='homework_id')
    """ID домашней работы"""

    #TODO: Описать
    homework_entry_id: int

    created_at: datetime = Field(validation_alias='homework_created_at')
    """Время создания Д/З"""

    updated_at: datetime = Field(validation_alias='homework_updated_at')
    """Время обновления Д/З"""

    #TODO: Описать. Скорее всего, текстовый ответ на Д/З
    written_answer: Any | None

    date_prepared_for: date
    """Дата, на которую задано Д/З"""