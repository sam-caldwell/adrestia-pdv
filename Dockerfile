FROM ubuntu:latest

ENV ADRESTIA_PDV_SVC_HOST="0.0.0.0"
ENV ADRESTIA_PDV_SVC_PORT="8080"
ENV ADRESTIA_PDV_DATADIR='/tmp/pdv_data/'
ENV PYTHONPATH=$PYTHONPATH:/opt/

COPY ./ /opt/

WORKDIR /opt/

RUN apt-get update -y --fix-missing && \
    apt-get upgrade -y && \
    apt-get install python3 python3-pip -y && \
    pip3 install -r requirements.txt && \
    addgroup --system --gid 1337 adrestia && \
    adduser --system \
            --home /opt/ \
            --shell /bin/bash \
            --no-create-home \
            --uid 1337 \
            --ingroup adrestia \
            --disabled-password \
            --disabled-login adrestia && \
    chown -R adrestia:adrestia /opt/* && \
    mkdir -p ${ADRESTIA_PDV_DATADIR} && \
    chown -R adrestia:adrestia ${ADRESTIA_PDV_DATADIR} && \
    chmod -R 1777 ${ADRESTIA_PDV_DATADIR} && \
    id adrestia

WORKDIR /opt/

USER adrestia

RUN pytest --verbose --exitfirst  # Run the tests as the prod user.

USER adrestia
WORKDIR /opt/
ENTRYPOINT [ "python3", "/opt/src/app.py" ]
