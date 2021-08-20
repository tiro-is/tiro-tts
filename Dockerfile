FROM python:3.8-slim AS build

RUN DEBIAN_FRONTEND=noninteractive \
	&& apt-get update -yqq \
        && apt-get install -yqq \
             python3 python3-pip libavcodec*-extra git swig ffmpeg protobuf-compiler \
        && rm -rf /var/lib/{apt,dpkg,log,cache}/

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY src /app/
COPY proto/ /app/proto
RUN protoc --python_out=. -I. proto/tiro/tts/voice.proto
COPY conf/ /app/conf

FROM build as runtime-prod

EXPOSE 8000
VOLUME /app/generated

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--access-logformat", "%(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\""]
CMD ["app:app"]
