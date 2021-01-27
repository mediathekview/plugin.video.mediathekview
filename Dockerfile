FROM linuxserver/mariadb

# fill variables from linuxserver/mariadb with mediathekview default (https://docs.linuxserver.io/images/docker-mariadb)
ENV MYSQL_DATABASE='mediathekview'
ENV MYSQL_USER='mediathekview'
ENV MYSQL_PASSWORD='mediathekview'
ENV MYSQL_ROOT_PASSWORD='mediathekview_root'

# custom variables
ENV CRON_TIMESPEC="0 4-22/1 * * *"
ENV RUN_ON_STARTUP='no'

# install dependencies
RUN apt update -y && \
    apt install python3-pip cron -y && \
    apt autoclean -y && \
    apt autoremove -y

RUN pip3 install mysql-connector-python

#cop mediathekview plugin
WORKDIR /plugin.video.mediathekview
ADD * ./
ADD resources/ ./resources/

#add a script that configures and starts cronjob
ADD docker/95_mediathekview_db /etc/cont-init.d/

#CMD and ENTRYPOINT are set by base image
