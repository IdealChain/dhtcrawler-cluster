###
# crawler dockerfile
#
# Build: docker build -t crawler .
# Run:   docker run -it -p 6881:6881 -p 6881:6881/udp --link collector -e BROKER=redis://collector:6379/0 crawler
#
###

FROM    debian:stretch-slim
RUN     apt-get update && apt-get upgrade -y
RUN     apt-get install --no-install-recommends -y \
        gnupg git ca-certificates
ADD     https://deb.nodesource.com/setup_8.x /tmp/node_setup
RUN     /bin/bash /tmp/node_setup
RUN     apt-get install --no-install-recommends -y nodejs
RUN     useradd -ms /bin/bash crawler
WORKDIR /home/crawler
COPY    . ./
RUN     chown -R crawler:crawler . && \
        npm install

USER    crawler
EXPOSE  6881 6881/udp
ENV     BROKER ""
CMD     npm start
