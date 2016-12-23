#!/bin/bash -eu
cd "$(dirname "${BASH_SOURCE}")/.."

TOKEN=`aws ecr get-login`
$TOKEN
REPOSITORY=`echo $TOKEN | sed -E 's/.*(http|https):\/\/([^ ]+)/\2/'`

read -p "ECS repository URI? " -e -i "$REPOSITORY" REPOSITORY

docker build -t collector collector/
docker tag collector:latest $REPOSITORY/collector:latest
docker push $REPOSITORY/collector:latest

docker build -t crawler crawler/
docker tag crawler:latest $REPOSITORY/crawler:latest
docker push $REPOSITORY/crawler:latest
