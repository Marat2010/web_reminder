FROM python:3.10

COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "app.py"]

#ENTRYPOINT ["/bin/bash", "start.sh"]
