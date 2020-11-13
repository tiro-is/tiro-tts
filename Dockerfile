FROM python:3.7-slim

RUN apt-get update -yqq && apt-get install -yqq \
        python3 python3-pip espeak-ng espeak-ng-data \
        && rm -rf /var/lib/{apt,dpkg,log,cache}/

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app

EXPOSE 8000
VOLUME /app/generated
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
CMD ["app:app"]
