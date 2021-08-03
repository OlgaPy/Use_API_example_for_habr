FROM python:3.7.9-slim-stretch
COPY . /app/
WORKDIR /app
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt
ENTRYPOINT ["python", "api.py"]
