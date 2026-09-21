from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ..enums import MarkDynamicType


class SubjectMark(BaseModel):
    """Школьная оценка по предмету"""
    model_config = ConfigDict(extra='ignore')

    #TODO: Описать
    average: Decimal

    dynamic_type: MarkDynamicType = Field(
        validation_alias=AliasChoices('dynamic_type', 'dynamic')
    )
    """Динамика среднего балла по оценке"""

    periods: list[SubjectMarkPeriod]
    """Учебные периоды выставления оценок (к примеру, триместры)"""

    subject_name: str
    """Название предмета"""

    value: Decimal = Field(validation_alias='average_by_all')
    """Средний балл оценки"""

    #TODO: Описать. Возможно, итоговая оценка за год
    year_mark: Any | None


class SubjectMarkPeriod(BaseModel):
    """Учебынй период выставления оценки"""
    model_config = ConfigDict(extra='ignore')

    start: str
    """Дата начала учебного периода в формате `mm.dd`"""

    title: str
    """Название учебного периода"""

    dynamic: MarkDynamicType
    """Динамика среднего балла оценки"""

    value: Decimal
    """Значение среднего балла"""

    marks: list[SubjectMarkPeriodMark]
    """Список школьных оценок"""

    count: int
    """Кол-во оценок"""

    target: MarkTarget
    """Цель текущей оценки до следующего балла"""

    #TODO: Описать
    fixed_value: Any | None

    start_date: date = Field(validation_alias='start_iso')
    """Дата начала учебного периода"""

    end_date: date = Field(validation_alias='end_iso')
    """Дата окончания учебного периода"""


class MarkTarget(BaseModel):
    """Цель оценки до следующего балла"""
    model_config = ConfigDict(extra='ignore')

    value: int
    """Цель оценки"""

    remain: int
    """Кол-во оценок с максимальным баллом до цели"""

    round: Decimal | None
    """Балл для перехода на следующую оценку"""

    paths: list[MarkTargetPath]
    """Варианты значений оценок для повышения среднего балла"""


class MarkTargetPath(BaseModel):
    """Вариант значения оценки для повышения среднего балла"""
    model_config = ConfigDict(extra='ignore')

    value: int
    """Значение оценки"""

    remain: int
    """Кол-во оценок `value` до следующего балла"""

    weight: int
    """Вес оценки `value`"""


class _MarkBase(BaseModel):
    """Общие поля школьной оценки"""
    model_config = ConfigDict(extra='ignore')

    id: int
    """ID оценки"""

    value: str
    """Значение оценки"""

    comment: str
    """Комментарий к оценке"""

    weight: int
    """Вес оценки"""

    #TODO: Описать. Скорее всего, дата выставления точки
    point_date: Any | None

    control_form_name: str
    """За что поставлена оценка"""

    comment_exists: bool
    """Написан ли комментарий к оценке"""

    #TODO: Описать
    criteria: Any | None

    has_files: bool
    """Имеет ли оценка прикреплённые файлы"""

    date: date
    """Дата, на которую выставлена оценка"""

    is_point: bool
    """Является ли оценка точкой"""

    is_exam: bool
    """Оценка с весом > 1"""

    #TODO: Описать. Скорее всего, система оценивания
    original_grade_system_type: str


class Mark(_MarkBase):
    """Школьная оценка из endpoint `marks`"""

    values: list[MarkValue]
    """Значения оценки в системах оценивания"""

    created_at: datetime
    """Дата выставления оценки"""

    updated_at: datetime
    """Дата изменения оценки"""

    subject_name: str
    """Название предмета, за который выставлена оценка"""

    subject_id: int
    """ID предмета, за которой выставлена оценка"""


class SubjectMarkPeriodMark(_MarkBase):
    """Сокращённая оценка из `subject_marks`"""

    values: list[MarkValue] | None
    """Значения оценки в системах оценивания"""

    created_at: datetime | None
    """Дата выставления оценки"""

    updated_at: datetime | None
    """Дата изменения оценки"""


class ScheduleEventMark(BaseModel):
    """Оценка из события расписания"""
    model_config = ConfigDict(extra='ignore')

    comment: str | None
    """Комментарий к оценке"""

    #TODO: Убедиться, что за оценку с тройным коэфицентом тоже True
    is_exam: bool
    """Оценка с весом > 1"""

    is_point: bool
    """Является ли оценка точкой"""

    #TODO: Описать. Скорее всего, дата выставления точки
    point_date: Any | None

    #TODO: Описать. Скорее всего, система оценивания
    original_grade_system_type: str

    #TODO: Описать
    criteria: list[Any] | None

    value: str
    """Значение оценки"""

    values: list[ScheduleEventMarkValue]
    """Значения оценки в системах оценивания"""

    weight: int
    """Вес оценки"""


class ScheduleEventMarkValue(BaseModel):
    """Значение оценки из события расписания в системе оценивания"""
    model_config = ConfigDict(extra='ignore')

    grade: ScheduleEventMarkGrade
    """Значения оценки по разным шкалам"""

    grade_system_type: str
    """Тип системы оценивания"""


class ScheduleEventMarkGrade(BaseModel):
    """Оценка из события расписания, приведённая к разным шкалам"""
    model_config = ConfigDict(extra='ignore')

    origin: str
    """Исходное значение оценки"""

    five: float | None = None
    """Оценка по пятибалльной шкале"""

    hundred: float | None = None
    """Оценка по стобалльной шкале"""


class MarkValue(BaseModel):
    """Значение оценки в системе оценивания"""
    model_config = ConfigDict(extra='ignore')

    name: str
    """Название шкалы оценивания"""

    nmax: float
    """Верхняя граница шкалы"""

    grade: MarkGrade
    """Значения оценки по разным шкалам"""

    grade_system_id: int
    """ID системы оценивания"""

    grade_system_type: str
    """Тип системы оценивания"""


class MarkGrade(BaseModel):
    """Оценка, приведённая к разным шкалам"""
    model_config = ConfigDict(extra='ignore')

    origin: str
    """Исходное значение оценки"""

    five: float
    """Оценка по пятибалльной шкале"""

    ten: float
    """Оценка по десятибалльной шкале"""

    hundred: float
    """Оценка по стобалльной шкале"""
