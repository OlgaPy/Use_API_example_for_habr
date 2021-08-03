# Use_API_example_for_habr
Прототип микросервиса для регистрации в СДО isping.


Адрес endpoint /api/register  
Обрабатывает POST запрос  
Принимает на вход JSON вида  
{  
"name": "Иван",  
"surname": "Петров",  
"email": "email@email.com",  
"phone": "+78975678920"  
}

или данные html формы с полями: name, surname, email, phone

Формат ответов микросервиса:

-  при создании пользователя возвращается 201 код ответа без тела

- при ошибках валидации/существовании пользователя возвращается 422 код ответа и JSON, ключ "errors" и структура вида:
  {
  "errors": [
  {
  "loc": "name",
  "msg": "Incorrect name",
  "type": "value_error"
  },
  {
  "loc": "surname",
  "msg": "Incorrect surname",
  "type": "value_error"
  },
  {
  "loc": "phone",
  "msg": "field required",
  "type": "value_error.missing"
  }
  ]
  }

- при разных ошибках возвращается 500 код ответа и JSON, ключ "message" с ошибкой:

{
"message": "Internal Server Error"
}


Инструкция по сборке и запуску docker контейнера

* Перейти в папку register_api
* Собрать docker образ командой:  
  docker build -t <имя образа> .
* Запустить docker контейнер командой:  
  docker run -e X_AUTH_EMAIL=<email для авторизации в ispring> -e X_AUTH_PASSWORD=<пароль для авторизации в ispring> -d -p 80:5000 <название образа>


Для тестирования присутствует html форма.  
Для запуска:
* перейти в папку register_test_form
* открыть в браузере http://127.0.0.1:5000/api/register_form?course_id=подставить_id_курса_на_который_будем_регистрировать_пользователя