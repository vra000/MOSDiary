from __future__ import annotations

from typing import NotRequired, TypedDict


class UserSchema(TypedDict):
    id: int
    email: NotRequired[str | None]
    snils: str
    profiles: list[ProfileSchema]
    guid: str
    first_name: str
    last_name: str
    middle_name: NotRequired[str | None]
    phone_number: NotRequired[str | None]
    authentication_token: str
    person_id: str
    password_change_required: bool
    regional_auth: str
    date_of_birth: NotRequired[str | None]
    sex: str


class ProfileSchema(TypedDict):
    id: int
    type: str
    # TODO: Типизировать
    roles: list[object]
    user_id: int
    agree_pers_data: bool
    school_id: int
    school_shortname: str
    school_name: str
    subject_ids: list[int]
    organization_id: str


class FamilySchema(TypedDict):
    profile: FamilyUserSchema
    children: list[FamilyChildSchema]
    hash: str


class FamilyUserSchema(TypedDict):
    last_name: str
    first_name: str
    middle_name: NotRequired[str | None]
    birth_date: NotRequired[str | None]
    sex: str
    user_id: int
    id: int
    phone: NotRequired[str | None]
    email: NotRequired[str | None]
    snils: str
    type: str


class FamilyChildSchema(TypedDict):
    last_name: str
    first_name: str
    middle_name: NotRequired[str | None]
    birth_date: str
    sex: str
    user_id: int
    id: int
    phone: NotRequired[str | None]
    email: NotRequired[str | None]
    snils: str
    type: NotRequired[str | None]
    school: FamilyChildSchoolSchema
    class_name: str
    class_level_id: int
    class_unit_id: int
    class_uid: str
    age: int
    groups: list[FamilyChildGroupSchema]
    ec_groups: NotRequired[object | None]
    representatives: list[FamilyChildRepresentativeSchema]
    sections: list[FamilyChildSectionSchema]
    sudir_account_exists: bool
    sudir_login: NotRequired[str | None]
    is_legal_representative: bool
    parallel_curriculum_id: int
    contingent_guid: str
    enrollment_date: str
    service_type_id: int
    profession_specialty_code: NotRequired[str | None]
    profession_specialty_name: NotRequired[str | None]
    grade_book_number: NotRequired[str | None]
    grade_book_date: NotRequired[str | None]
    education_level_id: int
    physical_training_health_group_id: int


class FamilyChildSchoolSchema(TypedDict):
    id: int
    name: str
    short_name: str
    county: str
    principal: str
    phone: str
    global_school_id: int
    municipal_unit_name: NotRequired[str | None]


class FamilyChildGroupSchema(TypedDict):
    id: int
    name: str
    subject_id: int
    is_fake: bool


class FamilyChildRepresentativeSchema(TypedDict):
    person_id: str
    last_name: str
    first_name: str
    middle_name: str
    type_id: int
    type: str
    email: str
    phone: str
    snils: str


class FamilyChildSectionSchema(TypedDict):
    id: int
    name: str
    subject_id: NotRequired[int | None]
    is_fake: bool