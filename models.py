import re

from flask_wtf import FlaskForm
from pydantic import BaseModel, validator
from wtforms import StringField


class User(BaseModel):
    """
    User model for validate data
    """

    name: str
    surname: str
    email: str
    phone: str
    user_id: str = ''

    # TODO уточнить валидации
    @validator("name")
    def validate_name(cls, name: str) -> str:
        name = name.strip()
        if not re.search('^(?P<name>[а-яА-Я]{2,})$', name):
            raise ValueError("Incorrect name")
        return name.capitalize()

    @validator("surname")
    def validate_surname(cls, surname: str) -> str:
        surname = surname.strip()
        if not re.search('^(?P<surname>[а-яА-Я]{2,})$', surname):
            raise ValueError("Incorrect surname")
        return surname.capitalize()

    @validator("phone")
    def validate_phone(cls, phone: str) -> str:
        founds_phone = re.search('^(?P<phone>(?P<pre>\+7|8|)(?P<num>\d{10}))$', phone, re.M|re.S)
        if founds_phone is None:
            raise ValueError("Incorrect phone")
        phone = f"+7{founds_phone.group('num')}"
        return phone

    @validator("email")
    def validate_email(cls, email: str) -> str:
        if not re.search('^(?P<email>(?P<mnaim>\S+)\@(?P<host>\S+)\.(?P<domain>\w+))$', email):
            raise ValueError("Incorrect email")
        return email.lower()


class RegistrationForm(FlaskForm):
    """
    Form for user data from POST form request
    """

    name = StringField()
    surname = StringField()
    email = StringField()
    phone = StringField()
