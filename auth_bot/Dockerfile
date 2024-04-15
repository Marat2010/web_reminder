FROM python:3.10

COPY . /auth_bot/

WORKDIR /auth_bot

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

ENTRYPOINT ["python3", "auth_bot.py"]

