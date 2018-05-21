###
# crawler dockerfile
#
# Build: docker build -t crawler .
# Run:   docker run -it -p 6881:6881 -p 6881:6881/udp --link collector -e BROKER=redis://collector:6379/0 crawler
#
###

FROM    debian:stretch-slim
ARG     DEBIAN_FRONTEND="noninteractive"
RUN     apt-get update && apt-get upgrade -y
RUN     apt-get install --no-install-recommends -y \
        gnupg git ca-certificates apt-transport-https curl lsb-release make python-dev && \
        apt-get clean && rm -rf /var/lib/apt/lists/*
RUN     curl https://deb.nodesource.com/setup_10.x | bash - && \
        apt-get install --no-install-recommends -y nodejs && \
        apt-get clean && rm -rf /var/lib/apt/lists/*

RUN     useradd -ms /bin/bash crawler
WORKDIR /home/crawler
COPY    . ./
RUN     chown -R crawler:crawler . && \
        npm install

USER    crawler
EXPOSE  6881 6881/udp
ENV     BROKER ""
CMD     npm start
