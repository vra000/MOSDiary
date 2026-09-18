from __future__ import annotations

from enum import StrEnum


class UserType(StrEnum):
    """Тип роли пользователя"""

    STUDENT = 'student'
    """Ученик"""

    PARENT = 'agent'
    """Родитель"""

    PRINCIPAL = '7'
    """Директор"""

    DEPUTY_PRINCIPAL = '8'
    """Завуч"""

    TEACHER = '9'
    """Учитель"""

    @classmethod
    def _missing_(cls, value: object) -> UserType | None:
        aliases = {
            1: cls.STUDENT,
            '1': cls.STUDENT,
            2: cls.PARENT,
            '2': cls.PARENT,
            7: cls.PRINCIPAL,
            8: cls.DEPUTY_PRINCIPAL,
            9: cls.TEACHER,
        }
        return aliases.get(value)


class UserSex(StrEnum):
    """Пол пользователя"""

    MALE = 'male'
    """Мужчина"""

    FEMALE = 'female'
    """Женшина"""

    @classmethod
    def _missing_(cls, value: object) -> UserSex | None:
        aliases = {
            'm': cls.MALE,
            'f': cls.FEMALE
        }
        return aliases.get(value)
