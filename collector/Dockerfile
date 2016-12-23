###
# collector dockerfile
#
# Build: docker build -t collector .
# Run:   docker run -it -p 6379:6379 -p 5555:5555 collector
#
###

FROM    debian:stretch-slim
RUN     apt-get update && apt-get upgrade -y
RUN     apt-get install --no-install-recommends -y \
        python3 python3-pip python3-setuptools redis-server supervisor
COPY    supervisor/ /etc/supervisor/
COPY    . /home/collector/
RUN     pip3 install wheel && pip3 install -r /home/collector/requirements.txt
RUN     mkdir /home/torrents && chown -R redis:redis /home
VOLUME  ["/home/torrents"]

EXPOSE  5555 6379
CMD     supervisord -n -c /etc/supervisor/supervisord.conf
