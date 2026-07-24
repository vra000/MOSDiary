from enum import Enum, StrEnum


#TODO: Дополнить
class UserType(Enum):
    """Тип роли пользователя"""

    STUDENT = 'student'
    """Ученик"""

    # REPRESENTATIVE = (1)
    # """Законный представитель"""


class UserSex(Enum):
    """Пол пользователя"""

    MALE = ('male', 'm')
    """Мужчина"""

    FEMALE = 'female'
    """Женшина"""