###
# collector dockerfile
#
# Build: docker build -t collector .
# Run:   docker run -it -p 6379:6379 -p 5555:5555 collector
#
###

FROM    debian:stretch-slim
ARG     DEBIAN_FRONTEND="noninteractive"
RUN     apt-get update && apt-get upgrade -y
RUN     apt-get install --no-install-recommends -y \
        python3 python3-pip python3-setuptools locales redis-server supervisor && \
        apt-get clean && rm -rf /var/lib/apt/lists/*
ENV     LANG C.UTF-8
RUN     pip3 install wheel pipenv

COPY    supervisor/ /etc/supervisor/
COPY    . /home/collector/
RUN     mkdir /home/torrents && \
        chown -R redis:redis /home
VOLUME  ["/home/torrents"]
RUN     cd /home/collector && \
        su -s "/bin/sh" -c "pipenv install && pipenv graph" redis

EXPOSE  5555 6379
CMD     supervisord -n -c /etc/supervisor/supervisord.conf
