###
# crawler dockerfile
#
# Build: docker build -t crawler .
# Run:   docker run -it -p 6881:6881 -p 6881:6881/udp crawler
#
###

FROM    debian:stretch-slim
RUN     apt-get update && apt-get upgrade -y
RUN     apt-get install --no-install-recommends -y \
        nodejs nodejs-legacy npm git
RUN     useradd -ms /bin/bash crawler
WORKDIR /home/crawler
COPY    . ./
RUN     chown -R crawler:crawler . && \
        npm install

USER    crawler
EXPOSE  6881 6881/udp
ENV     BROKER ""
CMD     npm start
