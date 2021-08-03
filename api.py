from flask import Flask, jsonify, request, render_template
from flask_wtf import FlaskForm
from pydantic import BaseModel, ValidationError, validator
from wtforms import StringField
import re
from typing import Union, Dict, List, Type, Any
from loguru import logger
from api_requests import ApiRequest


app = Flask(__name__)
JSON = Union[Dict[str, Any], List[Any], int, str, float, bool, Type[None]]
logger.add(sink='logs/log.txt', level="DEBUG", encoding='UTF-8')

class User(BaseModel):
    """
    User model for validate data
    """

    name: str
    surname: str
    email: str
    phone: str
    user_id = ''
    course_id: str

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


class RegistrationForm(FlaskForm):  #TODO добавить нужную валидацию
    """
    Form for user data from POST form request
    """

    name = StringField()
    surname = StringField()
    email = StringField()
    phone = StringField()
    course_id = StringField()


@app.route("/api/register_post", methods=["POST"])
# @cross_origin()
def ispring_registration():
    """
    Endpoint to registration a new user in iSpring by post_request

    :return: json, status code
    """

    try:
        new_user = User.parse_raw(request.data)
        processing_requests = ApiRequest(new_user)
        processing_requests.api_requests()
        logger.debug(f'User created. User data:{new_user}')
        response = {}
        response_code = 201  # для успешной регистрации нового пользователя
        return jsonify(response), response_code
    except ValidationError as e:
        logger.debug(f'Validation errors: {e.json()}')
        response_code = 422  # ошибки валидации, либо существование пользователя по email или phone
        response = {"errors": [str(e.json())]}
        return jsonify(response), response_code
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        response = {"message": "У нас технические сложности, но скоро все заработает! Попробуйте повторить операцию немного позже"}
        response_code = 500  # разные ошибки выполнения запросов к ISPING, ошибки в работе API
        return jsonify(response), response_code


@app.route("/api/register_form", methods=['POST', "GET"])
def ispring_registration_from_form():
    """
    Endpoint to registration a new user in iSpring by web_form
    :return:  json, status code
    """
    """example http://127.0.0.1:5000/api/register_form?course_id=cc624f10-cf4b-11eb-82aa-4e8520552baf"""

    logger.debug(f'request.form = {request.form}')
    if request.method == 'POST':
        logger.debug('Ветка FORM данные')
        form = RegistrationForm()
        try:
            form.validate_on_submit()
            new_user = User(name=form.name.data, surname=form.surname.data, email=form.email.data,
                            phone=form.phone.data, course_id=form.course_id.data)

            req = ApiRequest(new_user)
            req.api_requests()
            logger.debug(f'User created. User data:{new_user}')
            response = {}
            response_code = 201  # для успешной регистрации нового пользователя
            return jsonify(response), response_code
        except ValidationError as e:
            logger.debug(f'Validation errors: {e.json()}')
            response_code = 422  # ошибки валидации, либо существование пользователя по email или phone
            response = {"errors": [str(e.json())]}
            return jsonify(response), response_code
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            response = {"message": "У нас технические сложности, но скоро все заработает! Попробуйте повторить операцию немного позже"}
            response_code = 500  # разные ошибки выполнения запросов к ISPING, ошибки в работе API
            return jsonify(response), response_code

    return render_template('register_form.html', course_id=request.args.get('course_id'))


if __name__ == '__main__':
    app.config["WTF_CSRF_ENABLED"] = False  # TODO включить после этапа прототипа и использовать SECRET_KEY
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', debug=True, port=5000)  # TODO убрать DEBUG после этапа прототипа