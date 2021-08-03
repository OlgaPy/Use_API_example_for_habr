from typing import List
from exceptions import AddUserException, CheckExistUserException, CheckExistCourseException, \
    AddUserCourseException, UserAlreadyExistsException, BadUserIdException, UnauthorizedException, \
    PermissionDeniedException, BadRequestException, PhoneAlreadyExistsException
from models import User
import re, os
import requests
from requests.structures import CaseInsensitiveDict
from config import Config
from lxml import etree
from loguru import logger


class ApiRequest:
    """
    Class for sending requests to the Isping API

    """
    def __init__(self, new_user):
        self.base_url = Config.base_url
        self.headers = CaseInsensitiveDict()
        self.headers["Host"] = Config.Host
        self.headers["X-Auth-Account-Url"] = Config.X_Auth_Account_Url
        self.headers["X-Auth-Email"] = Config.X_Auth_Email
        self.headers["X-Auth-Password"] = Config.X_Auth_Password
        self.new_user = new_user
        self.default_department_id = Config.default_department_id
        self.dueDate = Config.dueDate
        self.re_login = re.compile('(?P<login>\w+)\@', re.M | re.S)

    def api_requests(self) -> None:
        """
        Method for processing registration request on Ispring

        :return: None
        """

        self.check_exist_user()
        self.add_user()

        courses_to_add = Config.default_course_ids
        self.add_user_to_courses(courses_to_add)

    def check_exist_user(self) -> None:
        """
        Method for checking the existence of a user, checks by login = self.new_user.email or phone=self.new_user.phone

        :raise UserAlreadyExistsException if exists user with the same login
        :raise PhoneAlreadyExistsException if exists user with the same phone

        :return: bool check result

        """
        logger.debug(f"Checking user exists, user_data = {self.new_user}")

        url = f"{self.base_url}/user"
        email = self.new_user.email
        resp = requests.get(url, headers=self.headers)
        logger.debug(f"Isping Checking user exists response: status code={resp.status_code}, content={resp.content}")
        if resp.status_code == 400:  # Bad Request
            tree = etree.XML(resp.content)
            message = tree.xpath('/response/message')[0].text
            raise BadRequestException(message)
        elif resp.status_code == 401:  # Unauthorized
            raise UnauthorizedException(f"Unauthorized Error")
        elif resp.status_code == 403:  # Permission denied
            raise PermissionDeniedException(f"Permission denied")
        elif resp.status_code != 200:  # other bad response
            raise CheckExistUserException(f"Request check_exist_user failed {resp.status_code}")


        resp_xml_content = resp.content
        tree = etree.XML(resp_xml_content)
        user_by_email = tree.xpath(
            f'/response/userProfile/fields/field[name = "EMAIL" and value = "{email}"]')
        if user_by_email:
            self.new_user.user_id = (tree.xpath(
                f".//userProfile[./fields/field/name[contains(text(), 'LOGIN')] and ./fields/field/value[contains(text(), '{email}')]]/userId"))[
                0].text
            logger.warning(f"User with login {email} already exists, user_id: {self.new_user.user_id}")
            raise Exception(f"User with email '{self.new_user.email}' already exists")
        logger.info(f"User with login '{email}' doesn't exist yet")

        is_phone_already_exists = tree.xpath(
            f'/response/userProfile/fields/field[name = "PHONE" and value = "{self.new_user.phone}"]')
        if is_phone_already_exists:
            raise Exception(f"User with phone '{self.new_user.phone}' already exists")


    def add_user(self) -> bool:
        """
        Method for adding a new user to Ispring.
        raise BadUserIdException if Isping not returned user_id

        :return: bool success
        """
        logger.debug(f"Trying to create a new user, user_data = {self.new_user}")

        url = f"{self.base_url}/user"
        login = self.re_login.search(self.new_user.email).group('login')

        files = {
            'departmentId': (None, f'{self.default_department_id}'),
            'fields[email]': (None, f'{self.new_user.email}'),
            'fields[login]': (None, f'{login}'),
            'fields[first_name]': (None, f'{self.new_user.name}'),
            'fields[last_name]': (None, f'{self.new_user.surname}'),
            'fields[phone]': (None, f'{self.new_user.phone}'),
            'sendLoginEmail': (None, f'{True}'),
        }

        resp = requests.post(url=url, headers=self.headers, files=files)

        logger.debug(f"Isping create user response: status code={resp.status_code}, content={resp.content}")

        if resp.status_code == 400:  # Bad Request
            tree = etree.XML(resp.content)
            message = tree.xpath('/response/message')[0].text
            raise Exception(message)
        elif resp.status_code == 401:  # Unauthorized
            raise Exception(f"Unauthorized Error")
        elif resp.status_code == 403:  # Permission denied
            raise Exception(f"Permission denied")
        elif resp.status_code != 201:  # other bad response
            logger.error(f"Failed to create user")
            raise Exception(f"Request add_user failed {resp.status_code}")

        resp_xml_content = resp.content
        try:
            self.new_user.user_id = etree.XML(resp_xml_content).text
            logger.info(f"Add new user successful. User_id: {self.new_user.user_id}, user data: {self.new_user}")
            return True
        except Exception as ex:
            logger.error(f"Error get user_id from response {ex}")
            return False

    def check_exist_course_user(self, course_id: str) -> bool:
        """
        Checks if the user has a course by course_id.
        raise CheckExistCourseException if check failed.

        :param course_id: string, id of a course in Isping
        :return: bool success
        """
        logger.debug(f"Check user {self.new_user.user_id} for the purpose of the course {course_id}")
        url = f"{self.base_url}/enrollment"
        resp = requests.get(url, headers=self.headers)

        logger.debug(f"Isping check_exist_course_user response: status code={resp.status_code}, content={resp.content}")
        if resp.status_code == 400:  # Bad Request
            tree = etree.XML(resp.content)
            message = tree.xpath('/response/message')[0].text
            raise BadRequestException(message)
        elif resp.status_code == 401:  # Unauthorized
            raise UnauthorizedException(f"Unauthorized Error")
        elif resp.status_code == 403:  # Permission denied
            raise PermissionDeniedException(f"Permission denied")
        elif resp.status_code != 200:  # other bad response
            logger.error(f"Failed to check enrollment for user: {self.new_user.user_id} for course_id: {course_id}")
            raise CheckExistCourseException(f"Request check_exist_enrollment_user failed {resp.status_code}")

        resp_xml_content = resp.content
        tree = etree.XML(resp_xml_content)
        user_course_found = tree.xpath(
            f'/response/enrollment[./courseId="{course_id}" and ./learnerId="{self.new_user.user_id}"]')
        if user_course_found:
            logger.warning(f"User {self.new_user.user_id} already in list of learners on course {course_id}")
            return True
        logger.debug(f"User {self.new_user.user_id} has not yet been assigned a course {course_id}")
        return False

    def add_user_to_courses(self, courses: List[str]) -> bool:
        """
        Enroll the user to a courses.
        raise AddUserCourseException on failure.

        :param courses: list of courses id of a courses in Isping
        :return: bool success
        """
        if not courses:
            logger.warning('add_user_to_courses method passed an empty list of courses')
            return False

        logger.debug(f"Trying to add user {self.new_user.user_id} on courses {courses}")
        url = f"{self.base_url}/enrollment"

        files = {
            'learnerIds[id]': (None, f'{self.new_user.user_id}'),
            'dueDateType': (None, f'{self.dueDate}'),
        }
        for index, course_id in enumerate(courses):
            files[f'courseIds[id][{index}]'] = (None, course_id)

        resp = requests.post(url=url, headers=self.headers, files=files)

        logger.debug(f"Isping add user to courses response: status code={resp.status_code}, content={resp.content}")
        if resp.status_code == 400:  # Bad Request
            tree = etree.XML(resp.content)
            message = tree.xpath('/response/message')[0].text
            raise BadRequestException(message)
        elif resp.status_code == 401:  # Unauthorized
            raise UnauthorizedException(f"Unauthorized Error")
        elif resp.status_code == 403:  # Permission denied
            raise PermissionDeniedException(f"Permission denied")
        elif resp.status_code != 201:
            logger.debug(f"Error add user {self.new_user.user_id} for courses {courses}")
            raise AddUserCourseException(f"Request add_user_to_enrollment failed {resp.status_code}")

        logger.info(f"Add user {self.new_user.user_id} on courses {courses} successful. resp.content:{resp.content},"
                    f" resp.text={resp.text}")
        return True
