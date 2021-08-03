class AddUserException(Exception):
    """Исключение ошибки добавления пользователя"""
    pass


class CheckExistUserException(Exception):
    """Исключение ошибки проверки существования пользователя"""
    pass


class CheckExistCourseException(Exception):
    """Исключение ошибки проверки назначения пользователю"""
    pass


class AddUserCourseException(Exception):
    """Исключение ошибки добавления назначению пользователю"""
    pass


class UserAlreadyExistsException(Exception):
    """Исключегие ошибки сущестования пользователя"""
    pass


class BadUserIdException(Exception):
    """Исключегие получения плохого user_id"""
    pass


class UnauthorizedException(Exception):
    """Исключение для ошибок авторизации"""
    pass


class PermissionDeniedException(Exception):
    """Исключение для ошибок по правам"""
    pass


class BadRequestException(Exception):
    """Исключение для плохих запросов"""
    pass


class PhoneAlreadyExistsException(Exception):
    """Исключение наличия пользователя с указанным телефоном"""
    pass
