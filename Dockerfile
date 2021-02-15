FROM python:3.8-slim AS build

RUN DEBIAN_FRONTEND=noninteractive \
	&& apt-get update -yqq \
        && apt-get install -yqq \
             python3 python3-pip espeak-ng espeak-ng-data git swig \
        && rm -rf /var/lib/{apt,dpkg,log,cache}/

WORKDIR /app
COPY lib/fastspeech/requirements.txt lib/fastspeech/requirements.txt
RUN pip install -r lib/fastspeech/requirements.txt
COPY lib/fastspeech/melgan/requirements.txt lib/fastspeech/melgan/requirements.txt
RUN pip install -r lib/fastspeech/melgan/requirements.txt
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . /app

FROM build as runtime-prod

EXPOSE 8000
VOLUME /app/generated

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
CMD ["app:app"]
