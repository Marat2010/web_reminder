#! /bin/bash

##### Build App image
docker build -f app/Dockerfile -t reminder-app:v1 .

##### Build Auth-bot image
docker build -f auth_bot/Dockerfile -t reminder-auth-bot:v1 .

##### Build Repeater image

docker build -f repeater/Dockerfile -t reminder-repeater:v1 .


##### Build Webhook image

docker build -f webhook/Dockerfile -t reminder-webhook:v1 .
