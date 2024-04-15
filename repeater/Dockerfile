FROM python:3.10

COPY . /repeater/

WORKDIR /repeater

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

ENTRYPOINT ["python3", "repeater.py"]