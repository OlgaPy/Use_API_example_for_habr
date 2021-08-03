from flask import Flask, jsonify, request, render_template, url_for, escape, make_response
from flask_wtf import FlaskForm
from loguru import logger
from pydantic import BaseModel, ValidationError, validator
from wtforms import StringField
from wtforms.validators import InputRequired, Email
import re, os
from api_requests import ApiRequest

import json
from typing import Union, Dict, List, Type, Any

from flask import Flask, jsonify, request
# from flask_cors import cross_origin
from loguru import logger
from pydantic import ValidationError

from api_requests import ApiRequest
# from exceptions import AddUserException, CheckExistUserException, CheckExistCourseException, \
#     AddUserCourseException, UserAlreadyExistsException, BadUserIdException, UnauthorizedException, \
#     PermissionDeniedException, BadRequestException, PhoneAlreadyExistsException
from models import User, RegistrationForm


app = Flask(__name__)
JSON = Union[Dict[str, Any], List[Any], int, str, float, bool, Type[None]]
logger.add(sink='logs/log.txt', level="DEBUG", encoding='UTF-8')

SUCCESSFUL_RESPONSE_CODE = 201  # для успешной регистрации нового пользователя
VALIDATION_DATA_ERROR_RESPONSE_CODE = 422  # ошибки валидации, либо существенование пользователя по email или phone
SERVER_ERROR_RESPONSE_CODE = 500  # разные ошибки выполнения запросов к ISPING, ошибки в работе API
VALIDATION_DATA_ERROR_RESPONSE_KEY = "errors"
SERVER_ERROR_RESPONSE_KEY = "message"
SERVER_ERROR_MESSAGE = "У нас технические сложности, но скоро все заработает! Попробуйте повторить операцию немного позже"

# app = Flask(__name__)


class User(BaseModel):  #TODO добавить нужную валидацию
    """Модель пользователя для валидации JSON данных"""

    name: str
    surname: str
    email: str
    phone: str
    user_id = ''
    course_id: str

    @validator("name")
    def validate_name(cls, name: str) -> str:
        if not re.search('^(?P<name>[а-яА-Я]{2,})($|)', name):
            raise ValueError("Incorrect name")
        return name.capitalize()

    @validator("surname")
    def validate_surname(cls, surname: str) -> str:
        if not re.search('^(?P<surname>[а-яА-Я]{2,})($|)', surname):
            raise ValueError("Incorrect surname")
        return surname.capitalize()

    @validator("phone")
    def validate_phone(cls, phone: str) -> str:
        founds_phone = re.search('^(?P<phone>(?P<pre>\+7|8|)(?P<num>\d{10}))($|)', phone, re.M|re.S)
        if founds_phone is None:
            raise ValueError("Incorrect phone")
        phone = f"8{founds_phone.group('num')}"
        return phone

    @validator("email")
    def validate_email(cls, email: str) -> str:
        if not re.search('^(?P<email>(?P<mnaim>\S+)\@(?P<host>\S+)\.(?P<domain>\w+))($|)', email):
            raise ValueError("Incorrect email")
        return email.lower()


class RegistrationForm(FlaskForm):  #TODO добавить нужную валидацию
    """Форма для вадиции данных пользователя из POST формы"""

    name = StringField()
    surname = StringField()
    email = StringField()
    phone = StringField()
    course_id = StringField()


@app.route("/api/register_post", methods=["POST"])
# @cross_origin()
def ispring_registration():
    """
    Endpoint to registration a new user in iSpring

    :return: json, status code
    """


    try:
        return process_registration_request()
    except ValidationError as e:
        logger.debug(f'Validation errors: {e.json()}')
        try:
            validation_errors = convert_validation_error_to_frontend_friendly_json(e.json())
        except Exception as e:
            logger.error(f"Error while converting to frontend_friendly_json: {str(e)}")
            return return_server_error_response()

        response_code = VALIDATION_DATA_ERROR_RESPONSE_CODE
        response = {VALIDATION_DATA_ERROR_RESPONSE_KEY: validation_errors}
        log_api_response(response_code=response_code, response=response)
        return jsonify(response), response_code
    except AddUserException as e:
        logger.error(f"Failed to add user. Error: {str(e)}")
        return return_server_error_response()
    except CheckExistUserException as e:
        logger.error(f"Failed to verify the existence of the user. Error:{str(e)}")
        return return_server_error_response()
    except CheckExistCourseException as e:
        logger.warning(f"Failed to check for course enrollment. Error: {str(e)}")
        return return_server_error_response()
    except AddUserCourseException as e:
        logger.warning(f"Failed to add course to user. Error: {str(e)}")
        return return_server_error_response()
    except UserAlreadyExistsException as e:
        logger.warning(f"UserAlreadyExistsException: {str(e)}")
        response = {VALIDATION_DATA_ERROR_RESPONSE_KEY: [{
            "loc": "email",
            "msg": "Пользователь с таким Email уже зарегистрирован",
            "type": "value_error"
        }]}
        response_code = VALIDATION_DATA_ERROR_RESPONSE_CODE
        log_api_response(response_code=response_code, response=response)
        return jsonify(response), response_code
    except BadUserIdException as e:
        logger.error(f"BadUserIdException: {str(e)}")
        return return_server_error_response()
    except UnauthorizedException as e:
        logger.error(f"UnauthorizedException: {str(e)}")
        return return_server_error_response()
    except PermissionDeniedException as e:
        logger.error(f"PermissionDeniedException: {str(e)}")
        return return_server_error_response()
    except BadRequestException as e:
        logger.error(f"BadRequestException : {str(e)}")
        return return_server_error_response()
    except PhoneAlreadyExistsException as e:
        logger.warning(f"PhoneAlreadyExistsException: {str(e)}")
        response = {VALIDATION_DATA_ERROR_RESPONSE_KEY: [{
            "loc": "phone",
            "msg": "Данный номер телефона уже зарегистрирован",
            "type": "value_error"
        }]}
        response_code = VALIDATION_DATA_ERROR_RESPONSE_CODE
        log_api_response(response_code=response_code, response=response)
        return jsonify(response), response_code
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return return_server_error_response()

def return_server_error_response() -> (JSON, int):
    """Method for return server error response"""

    response = {SERVER_ERROR_RESPONSE_KEY: SERVER_ERROR_MESSAGE}
    log_api_response(response_code=SERVER_ERROR_RESPONSE_CODE, response=response)
    return jsonify(response), SERVER_ERROR_RESPONSE_CODE


def process_registration_request() -> (JSON, int):
    """
    Method for validation request data and call isping api to registrate a new user

    :return: json, status code
    """

    logger.debug(f'request.data = {request.data}')
    logger.debug(f'request.form = {request.form}')

    if request.data:
        logger.debug('Branch JSON data')
        new_user = User.parse_raw(request.data)
        return call_isping_registration(new_user)

    if request.method == 'POST':
        logger.debug('Branch FORM data')
        form = RegistrationForm()
        if form.validate_on_submit():
            new_user = User(name=form.name.data, surname=form.surname.data, email=form.email.data,
                            phone=form.phone.data)
            new_user.validate()
            return call_isping_registration(new_user)

        # при нормальной работе системы этой код не достижим
        logger.error(f"Something went wrong. Branch FORM pass validate_on_submit block. forms error: {form.errors}")
        raise Exception("Something went wrong")

    # при нормальной работе системы этой код не достижим
    logger.error("Something went wrong. Branch JSON and branch FORM didn't work")
    raise Exception("Something went wrong")


def call_isping_registration(new_user: User) -> (JSON, int):
    """
    method for call isping api to registrate a new user

    :param new_user: User object
    :return: json, status code
    """
    req = ApiRequest(new_user)
    req.api_requests()
    logger.debug(f'User created. User data:{new_user}')
    response = {}
    response_code = SUCCESSFUL_RESPONSE_CODE
    log_api_response(response_code=response_code, response=response)
    return jsonify(response), response_code


def convert_validation_error_to_frontend_friendly_json(validation_errors: str) -> List:
    """Function for convert Pydantic validation error json to frontend friendly json format"""
    error_dict_list = json.loads(validation_errors)
    front_error_list = []
    for error_dict in error_dict_list:
        front_error_dict = {}
        for item, value in error_dict.items():
            if item == 'loc':
                front_error_dict[item] = value[0]
            else:
                front_error_dict[item] = value
        front_error_list.append(front_error_dict)

    return front_error_list


def log_api_response(response_code: int, response: Dict) -> None:
    """
    Method for logging api response

    :param response_code: int response code
    :param response: dict with response
    :return: None
    """

    logger.info(f"Api response {response_code}: {response}")


# @app.route("/api/register_form", methods=['POST', "GET"])
# def ispring_registration_from_form():
#     """example http://127.0.0.1:5000/api/register1?course_id=cc624f10-cf4b-11eb-82aa-4e8520552baf"""
#     # если данные из формы
#
#     logger.debug(f'request.form = {request.form}')
#     if request.method == 'POST':
#         logger.debug('Ветка FORM данные')
#         form = RegistrationForm()
#         if form.validate_on_submit():
#             new_user = User(name=form.name.data, surname=form.surname.data, email=form.email.data,
#                             phone=form.phone.data, course_id=form.course_id.data)
#             req = ApiRequest(new_user)
#             req.api_requests()
#             logger.debug(f'Данные пользователя: {new_user}')
#             # return new_user.json(ensure_ascii=False, indent=2), 200  # TODO временная заглушка
#             return make_response(new_user.json(ensure_ascii=False, indent=2), status_code=200)  # TODO временная заглушка
#
#         logger.debug(f'Ошибки валидации формы: {form.errors}')
#         return jsonify(form.errors), 400
#     return render_template('register.html', course_id=request.args.get('course_id'))


if __name__ == '__main__':
    app.config["WTF_CSRF_ENABLED"] = False  # TODO включить после этапа прототипа и использовать SECRET_KEY
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', debug=True, port=5000)  # TODO убрать DEBUG после этапа прототипа