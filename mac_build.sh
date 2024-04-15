#! /bin/bash

##### Build App image
docker buildx build -t reminder-app:{TAG} -f app/Dockerfile

##### Build Auth-bot image
docker buildx build -t reminder-auth-bot:{TAG} -f auth_bot/Dockerfile
