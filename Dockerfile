FROM python:3.8-slim AS build

RUN DEBIAN_FRONTEND=noninteractive \
	&& apt-get update -yqq \
        && apt-get install -yqq \
             python3 python3-pip libavcodec*-extra curl git swig ffmpeg \
        && rm -rf /var/lib/{apt,dpkg,log,cache}/

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
RUN pip install grpcio-tools==1.40.0
RUN curl -L https://github.com/grammatek/tts-frontend-api/archive/54ae2943375dd368ea94e5d869f71bdcc671a3cd.tar.gz | tar zxvf - \
    && mv tts-frontend-api-54ae2943375dd368ea94e5d869f71bdcc671a3cd/messages /app/ \
    && mv tts-frontend-api-54ae2943375dd368ea94e5d869f71bdcc671a3cd/services /app/ \
    && rm -rf tts-frontend-api-54ae2943375dd368ea94e5d869f71bdcc671a3cd
RUN python -m grpc_tools.protoc --python_out=. -I. messages/tts_frontend_message.proto
RUN python -m grpc_tools.protoc --python_out=.  --grpc_python_out=. -I. services/tts_frontend_service.proto
COPY src/ /app/src
COPY proto/ /app/proto
RUN python -m grpc_tools.protoc --python_out=. -I. proto/tiro/tts/voice.proto
COPY conf/ /app/conf

FROM build as runtime-prod

EXPOSE 8000
VOLUME /app/generated

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--access-logformat", "%(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\""]
CMD ["src.app:app"]
