# This container is for the flink taskmanager (worker) service. It adds the ability
# to execute docker properly via the worker.

ARG FLINK_VERSION=1.10

FROM flink:$FLINK_VERSION

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y libltdl7
RUN apt-get update; \
  apt-get -y install apt-transport-https ca-certificates curl gnupg software-properties-common; \
  curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -; \
  apt-key fingerprint 0EBFCD88; \
  add-apt-repository \
       "deb [arch=amd64] https://download.docker.com/linux/debian \
       $(lsb_release -cs) \
       stable" ;\
  apt-get update; \
  apt-get -y install docker-ce

# add flink user to docker group
RUN usermod -aG docker flink
