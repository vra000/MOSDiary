from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID
from typing import Any, Self

from .enums import UserType, UserSex
from .schemas import (
    ProfileSchema,
    UserSchema,
    FamilySchema,
    FamilyUserSchema,
    FamilyChildGroupSchema,
)


@dataclass(frozen=True, slots=True)
class User:
    id: int
    profiles: tuple[Profile, ...]

    guid: str
    person_id: UUID

    first_name: str
    last_name: str
    middle_name: str | None

    sex: UserSex
    regional_auth: str
    password_change_required: bool

    email: str | None = field(default=None, repr=False)
    phone_number: str | None = field(default=None, repr=False)
    birth_date: date | None = field(default=None, repr=False)

    auth_token: str = field(default="", repr=False)

    @classmethod
    def from_schema(cls, data: UserSchema) -> User:
        raw_birth_date = data.get("date_of_birth")

        return cls(
            id=data["id"],
            profiles=tuple(
                Profile.from_schema(profile)
                for profile in data["profiles"]
            ),
            guid=data["guid"],
            person_id=UUID(data["person_id"]),
            first_name=data["first_name"],
            last_name=data["last_name"],
            middle_name=data.get("middle_name"),
            sex=UserSex(data["sex"]),
            regional_auth=data["regional_auth"],
            password_change_required=data["password_change_required"],
            email=data.get("email"),
            phone_number=data.get("phone_number"),
            birth_date=(
                date.fromisoformat(raw_birth_date)
                if raw_birth_date is not None
                else None
            ),
            auth_token=data["authentication_token"],
        )


@dataclass(frozen=True, slots=True)
class Profile:
    id: int
    """ID в МЭШ"""

    type: UserType
    """Тип роли пользователя"""

    user_id: int

    school_id: int
    """ID школы"""

    school_short_name: str
    """Короткое название школы"""

    school_name: str
    """Название школы"""

    organization_id: str
    """ID организации"""

    personal_data_consent: bool
    subject_ids: tuple[int, ...]
    roles: tuple[object, ...]

    @classmethod
    def from_schema(cls, data: ProfileSchema) -> Profile:
        return cls(
            id=data["id"],
            type=UserType(data["type"]),
            user_id=data["user_id"],
            school_id=data["school_id"],
            school_short_name=data["school_shortname"],
            school_name=data["school_name"],
            organization_id=data["organization_id"],
            personal_data_consent=data["agree_pers_data"],
            subject_ids=tuple(data["subject_ids"]),
            roles=tuple(data["roles"]),
        )


@dataclass(slots=True, frozen=True)
class Family:
    """Семья"""

    profile: FamilyProfile
    """Ваш профиль в семье"""

    children: list[FamilyChild]
    """Профили детей в семье"""

    hash: str

    @classmethod
    def from_schema(cls, data: FamilySchema) -> Self:
        return cls(
            profile=FamilyProfile.from_schema(data["profile"]),
            children=tuple(
                FamilyChild.from_schema(child)
                for child in data["children"]
            )
        )


@dataclass(slots=True, frozen=True)
class FamilyProfile:
    """Ваш профиль в семье"""

    last_name: str
    """Фамилия"""

    first_name: str
    """Имя"""

    middle_name: str | None
    """Отчество"""

    birth_date: date | None = field(default=None, repr=False)
    """Дата рождения"""

    sex: UserSex
    """Пол"""

    # TODO: Описать
    user_id: int

    id: int
    """МЭШ ID"""

    phone_number: str
    """Номер телефона без первой цифры"""

    email: str
    """Электронный адрес почты"""

    snils: str
    """СНИЛС"""

    role: UserType
    """Роль"""

    @classmethod
    def from_schema(cls, data: FamilyUserSchema) -> Self:
        raw_birth_date = data.get("birth_date")

        return cls(
            last_name=data["last_name"],
            first_name=data["first_name"],
            middle_name=data.get("middle_name"),
            birth_date=(
                date.fromisoformat(raw_birth_date)
                if raw_birth_date is not None
                else None
            ),
            sex=UserSex(data["sex"]),
            user_id=data["user_id"],
            id=data["id"],
            phone_number=data.get("phone"),
            email=data.get("email"),
            snils=data["snils"],
            role=UserType(data["type"]),
        )


@dataclass(slots=True, frozen=True)
class FamilyChild:
    """Ребёнок в семье"""

    last_name: str
    """Фамилия ребёнка"""

    first_name: str
    """Имя ребёнка"""

    middle_name: str | None
    """Отчество ребёнка"""

    birth_date: date | None = field(default=None, repr=False)
    """Дата рождения ребёнка"""

    sex: UserSex
    """Пол ребёнка"""

    # TODO: Описать
    user_id: int

    id: int
    """МЭШ ID ребёнка"""

    phone_number: str
    """Номер телефона ребёнка без первой цифры"""

    email: str
    """Электронный адрес почты ребёнка"""

    snils: str
    """СНИЛС ребёнка"""

    role: UserType | None = field(default=None)
    """Роль ребёнка"""

    school: FamilyChildSchool
    """Школа ребёнка"""

    class_name: str
    """Название класса (к примеру, 4-Б2)"""

    class_level: int
    """Номер класса ребёнка"""

    # TODO: Описать
    class_unit_id: int

    class_uid: UUID
    """UID класса ребёнка (что бы это не значило)"""

    age: int
    """Возраст ребёнка"""

    subjects: list[FamilyChildSubject]
    """Школьные предметы ребёнка"""

    # TODO: Описать
    ec_groups: Any | None

    representatives: list[FamilyChildRepresentative]
    """Законные представители ребёнка (к примеру, родители)"""

    # TODO: Описать
    sections: list[FamilyChildSelection]
    """Что-то типа активных дополнительных кружков для ребёнка"""

    sudir_account_exists: bool
    """Есть аккаунт в СУДИР (Система управления доступом к информационным системам и ресурсам города Москвы)"""

    # TODO: Описать
    sudir_login: Any | None
    """Логин СУДИР (Система управления доступом к информационным системам и ресурсам города Москвы)"""

    # TODO: Описать
    is_legal_representetive: bool

    # TODO: Описать
    parallel_curriculum_id: Any | None

    # TODO: Описать
    contingent_guid: UUID

    # TODO: Конвертировать в datetime
    enrollment_date: str
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


@dataclass(slots=True, frozen=True)
class FamilyChildSchool:
    """Школа ребёнка в семье"""

    id: int
    """ID школы"""

    name: str
    """Полное название школы"""

    short_name: str
    """Короткое название школы"""

    county: str
    """Округ"""

    principal_fullname: str
    """ФИО директора"""

    phone_number: str
    """Номер телефона школы без первой цифры"""

    # TODO: Описать
    global_school_id: int

    # TODO: Описать
    municipal_unit_name: Any | None


@dataclass(slots=True, frozen=True)
class FamilyChildSubject:
    """Школьный предмет ребёнка в семье"""

    id: int
    """ID предмета"""

    name: str
    """Название предмета"""

    # TODO: Описать
    subject_id: Any | None

    # TODO: Описать
    is_fake: bool


@dataclass(slots=True, frozen=True)
class FamilyChildRepresentative:
    """Законный редставитель ребёнка (к примеру, родитель)"""

    person_id: UUID
    """UID закон. представителя"""

    last_name: str
    """Фамилия закон. преддставителя"""

    first_name: str
    """Имя закон. представителя"""

    middle_name: str
    """Отчество закон. представителя"""

    # TODO: Описать. Возможно, ID роли (у родителя 1). Позже заменить на переменную role
    type_id: int

    # TODO: Создать enum-класс. Возможные значения: "Родитель",
    type: str
    """Тип законного представителя"""

    email: str
    """Электронный адрес почты закон. представителя"""

    phone_number: str
    """Номер телефона закон. представителя без первой цифры"""

    snils: str
    """СНИЛС законного представителя"""


# TODO: Дать нормальное описание
class FamilyChildSelection:
    """Что-то типа активных дополнительных кружков для ребёнка"""

    id: int
    """ID """

    name: str
    """Название """

    # TODO: Описать
    subject_id: Any | None

    # TODO: Описать
    is_fake: bool