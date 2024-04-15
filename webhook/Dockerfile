FROM python:3.10

COPY . /webhook

WORKDIR /webhook

RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "webhook.py"]

