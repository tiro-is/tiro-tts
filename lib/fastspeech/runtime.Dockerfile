FROM python:3.7

RUN apt-get update -y && \
  apt-get install git python3-pip idle3 libsndfile1-dev swig -y && \
  pip3 install --no-cache-dir --upgrade pip

WORKDIR /opt/fastspeech2
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install git+https://github.com/sequitur-g2p/sequitur-g2p@master

RUN git clone https://github.com/seungwonpark/melgan.git
RUN pip3 install -r melgan/requirements.txt

COPY . .

ENTRYPOINT ["python3", "./synthesize.py"]
CMD ["--model-fs", "models/checkpoint_490000.pth.tar", "--model-melgan", "models/vocoder_aca5990_3350.pt", "--model-g2p", "models/ipd_clean_slt2018.mdl"]
