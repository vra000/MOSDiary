from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from datetime import date, datetime
from uuid import UUID
from typing import Any

from ..enums import UserType, UserSex


class UserInfo(BaseModel):
    """Информация о пользователе"""
    model_config = ConfigDict(extra='ignore')

    email: str | None = None
    """Электронный адрес почты"""

    phone_number: str | None = Field(default=None, validation_alias='phone')
    """Номер телефона без первой цифры"""

    full_name: str = Field(validation_alias='name')
    """ФИО пользователя"""

    sex: UserSex = Field(validation_alias='gender')
    """Пол пользователя"""

    education: list[UserInfoEducation]
    """Образование пользователя"""

    #TODO: Описать, типизировать
    children: list

    #TODO: Описать
    agents: list[str]

    #TODO: Описать
    sub: str

    broles: list[UserType]
    """Роли пользователя"""

    #TODO: Описать
    person_uid: str = Field(validation_alias='person_id')

    first_name: str = Field(validation_alias='given_name')
    """Имя пользователя"""

    family_name: str = Field(validation_alias='family_name')
    """Фамилия пользователя"""

    middle_name: str | None = None
    """Отчество пользователя"""

    birth_date: date
    """День рождение пользователя"""


class UserInfoEducation(BaseModel):
    """Информация об образовании пользователя"""
    model_config = ConfigDict(extra='ignore')

    training_begin_at: date
    """Дата начала обучения"""

    training_end_at: date
    """Дата окончания обучения"""

    study_class: UserInfoStudyClass = Field(validation_alias=AliasChoices('study_class', 'class'))
    """Уфчебный класс учащегося"""

    service_type: UserInfoEducationServiceType

#TODO: Описать
class UserInfoEducationServiceType(BaseModel):
    model_config = ConfigDict(extra='ignore')

    name: str
    global_id: int

class UserInfoStudyClass(BaseModel):
    """Учебный учащегося"""
    model_config = ConfigDict(extra='ignore')

    id: int
    """ID класса"""

    uid: UUID
    """UID класса"""

    name: str
    """Название класса. *К примеру, 9А-1*"""

    parallel: UserInfoStudyClassParallel
    """Параллель учащегося"""

    organization: UserInfoStudyClassOrganization
    """Учебное учереждение учащегося"""

    #TODO: Описать
    education_stage_id: int

    #TODO: Описать
    staff_ids: list[int]


class UserInfoStudyClassParallel(BaseModel):
    """Информация о параллели обучающегося"""
    model_config = ConfigDict(extra='ignore')

    name: str
    """Название праллели"""

    id: int
    """ID параллели"""


class UserInfoStudyClassOrganization(BaseModel):
    """Учебное учереждение учащегося"""

    name: str
    """Название учереждения"""

    global_id: int
    """Глобальный ID учереждения"""

    #TODO: Если знаете что это, то опишите, пожалуйста
    property_type_id: int


class Family(BaseModel):
    """Семья"""
    model_config = ConfigDict(extra='ignore')

    profile: FamilyProfile
    """Ваш профиль в семье"""

    children: list[FamilyChild]
    """Профили детей в семье"""

    hash: str


class FamilyProfile(BaseModel):
    """Ваш профиль в семье"""
    model_config = ConfigDict(extra='ignore')

    last_name: str
    """Фамилия"""

    first_name: str
    """Имя"""

    middle_name: str | None = None
    """Отчество"""

    birth_date: date
    """Дата рождения"""

    sex: UserSex
    """Пол"""

    # TODO: Описать
    user_id: int

    id: int
    """МЭШ ID"""

    phone_number: str | None = Field(default=None, validation_alias='phone')
    """Номер телефона без первой цифры"""

    email: str | None = None
    """Электронный адрес почты"""

    snils: str
    """СНИЛС"""

    role: UserType = Field(validation_alias=AliasChoices('role', 'type'))
    """Роль"""


class FamilyChild(BaseModel):
    """Ребёнок в семье"""
    model_config = ConfigDict(extra='ignore')

    last_name: str
    """Фамилия ребёнка"""

    first_name: str
    """Имя ребёнка"""

    middle_name: str | None = None
    """Отчество ребёнка"""

    birth_date: date
    """Дата рождения ребёнка"""

    sex: UserSex
    """Пол ребёнка"""

    # TODO: Описать
    user_id: int

    id: int
    """МЭШ ID ребёнка"""

    phone_number: str | None = Field(default=None, validation_alias='phone')
    """Номер телефона ребёнка без первой цифры"""

    email: str | None = None
    """Электронный адрес почты ребёнка"""

    snils: str
    """СНИЛС ребёнка"""

    role: UserType | None = Field(validation_alias=AliasChoices('role', 'type'))
    """Роль ребёнка"""

    school: FamilyChildSchool
    """Школа ребёнка"""

    class_name: str
    """Название класса (к примеру, 4-Б2)"""

    class_level: int = Field(validation_alias=AliasChoices('class_level', 'class_level_id'))
    """Номер класса ребёнка"""

    # TODO: Описать
    class_unit_id: int

    class_uid: UUID
    """UID класса ребёнка"""

    age: int
    """Возраст ребёнка"""

    subjects: list[FamilyChildSubject] = Field(validation_alias=AliasChoices('subjects', 'groups'))
    """Школьные предметы ребёнка"""

    # TODO: Описать
    ec_groups: Any | None

    representatives: list[FamilyChildRepresentative]
    """Законные представители ребёнка (к примеру, родители)"""

    sudir_account_exists: bool
    """Есть аккаунт в СУДИР (Система управления доступом к информационным системам и ресурсам города Москвы)"""

    sudir_login: Any | None
    """Логин СУДИР (Система управления доступом к информационным системам и ресурсам города Москвы)"""

    # TODO: Описать
    is_legal_representetive: bool = Field(
        validation_alias=AliasChoices(
            'is_legal_representetive',
            'is_legal_representative'
        )
    )

    # TODO: Описать
    parallel_curriculum_id: int | None

    # TODO: Описать
    contingent_guid: UUID

    enrollment_date: date
    """Дата поступления в первый класс"""

    # TODO: Описать
    service_type_id: int

    profession_specialty_code: Any | None

    profession_specialty_name: Any | None

    grade_book_number: Any | None

    grade_book_date: Any | None

    # TODO: Описать
    education_level_id: int

    # TODO: Описать
    physical_training_health_group_id: int


class FamilyChildSchool(BaseModel):
    """Школа ребёнка в семье"""
    model_config = ConfigDict(extra='ignore')

    id: int
    """ID школы"""

    name: str
    """Полное название школы"""

    short_name: str
    """Короткое название школы"""

    county: str
    """Округ"""

    principal_fullname: str = Field(validation_alias=AliasChoices('principal_fullname', 'principal'))
    """ФИО директора"""

    phone_number: str | None = Field(default=None, validation_alias='phone')
    """Номер телефона школы без первой цифры"""

    # TODO: Описать
    global_school_id: int

    # TODO: Описать
    municipal_unit_name: Any | None


class FamilyChildSubject(BaseModel):
    """Школьный предмет ребёнка в семье"""

    id: int
    """ID предмета"""

    name: str
    """Название предмета"""

    # TODO: Описать
    subject_id: Any | None

    # TODO: Описать
    is_fake: bool


class FamilyChildRepresentative(BaseModel):
    """Законный редставитель ребёнка (к примеру, родитель)"""

    person_id: UUID
    """UID закон. представителя"""

    last_name: str
    """Фамилия закон. преддставителя"""

    first_name: str
    """Имя закон. представителя"""

    middle_name: str | None = None
    """Отчество закон. представителя"""

    # TODO: Описать. Возможно, ID роли (у родителя 1). Позже заменить на переменную role
    type_id: int

    # TODO: Создать enum-класс. Возможные значения: "Родитель",
    type: str
    """Тип законного представителя"""

    email: str | None = None
    """Электронный адрес почты закон. представителя"""

    phone_number: str | None = Field(default=None, validation_alias='phone')
    """Номер телефона закон. представителя без первой цифры"""

    snils: str
    """СНИЛС законного представителя"""


class ProfileDeatail(BaseModel):
    """Детальнвя информация о профиле"""
    model_config = ConfigDict(extra='ignore')

    #TODO: Описать
    user_id: int = Field(validation_alias='userId')

    info: ProfileDetailInfo
    """Детальная информация о профиле"""

    roles: list[ProfileDetailRole]
    """Роли пользователя"""

    login: str
    """Логин пользователя"""


class ProfileDetailInfo(BaseModel):
    """Детальная информация о профиле"""
    model_config = ConfigDict(extra='ignore')

    birth_date: date = Field(validation_alias='birthdate')
    """День рождение"""

    @field_validator('birth_date', mode='before')
    @classmethod
    def parse_birth_date(cls, value: Any) -> Any:
        if isinstance(value, str) and '.' in value:
            return datetime.strptime(value, '%d.%m.%Y').date()
        return value

    email: str | None = Field(default=None, validation_alias='mail')
    """Почта"""

    sex: UserSex | None = Field(default=None, validation_alias='gender')
    """Пол пользователя"""

    #TODO: Описать
    trusted: bool

    first_name: str = Field(validation_alias='FirstName')
    """Имя"""

    phone_number: str | None = Field(default=None, validation_alias='mobile')
    """Номер телефона без первой цифры"""

    #TODO: Описать
    guid: UUID

    #TODO: Описать
    failed: bool

    last_name: str = Field(validation_alias='LastName')
    """Фамилия"""

    #TODO: Описать
    error: Any | None

    middle_name: str | None = Field(default=None, validation_alias='MiddleName')
    """Отчество"""

    snils: str
    """СНИЛС"""


class ProfileDetailRole(BaseModel):
    """Роль пользователя в детальной информации"""
    model_config = ConfigDict(extra='ignore')

    id: int
    """ID роли"""

    title: str
    """Название роли"""

    subsystems: list[dict]
    """Подсистемы, доступные для данной роли"""