FROM python:3.8-slim AS build

RUN DEBIAN_FRONTEND=noninteractive \
	&& apt-get update -yqq \
        && apt-get install -yqq \
    python3 \
    python3-pip \
    libavcodec*-extra \
    curl \
    git \
    swig \
    ffmpeg \
    libsndfile1 \
        && rm -rf /var/lib/{apt,dpkg,log,cache}/

WORKDIR /app
# We can't use the pinned and hashed deps in requirements.bazel.txt since some
# of the dependencies depend on vcs refs with commit sha1 hashes which pip
# doesn't in conjuction with hashed deps
COPY requirements.bazel.in ./requirements.txt
RUN pip install -r requirements.txt
RUN pip install grpcio-tools==1.40.0 grpcio==1.40.0
ARG TTS_FRONTEND_API_COMMIT_ID=54ae2943375dd368ea94e5d869f71bdcc671a3cd
RUN curl -L https://github.com/grammatek/tts-frontend-api/archive/$TTS_FRONTEND_API_COMMIT_ID.tar.gz | tar zxvf - \
    && mv tts-frontend-api-$TTS_FRONTEND_API_COMMIT_ID/messages /app/ \
    && mv tts-frontend-api-$TTS_FRONTEND_API_COMMIT_ID/services /app/ \
    && rm -rf tts-frontend-api-$TTS_FRONTEND_API_COMMIT_ID
RUN python -m grpc_tools.protoc --python_out=. -I. messages/tts_frontend_message.proto
RUN python -m grpc_tools.protoc --python_out=.  --grpc_python_out=. -I. services/tts_frontend_service.proto
COPY main.py /app/
COPY src/ /app/src
COPY proto/ /app/proto
RUN python -m grpc_tools.protoc --python_out=. -I. proto/tiro/tts/voice.proto
COPY conf/ /app/conf

FROM build as runtime-prod

# The server is configured using environment variables (see src/config.py) and
# enabled voices are configured with a SynthesisSet text protobuf (see
# proto/tiro/tts/voice.proto and the default conf/synthesis_set.pbtxt)

EXPOSE 8000
VOLUME /models

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--access-logformat", "%(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"", \
    "--threads", "8", "--timeout", "1000", "main:app"]
