FROM tensorflow/tensorflow:2.13.0rc0-gpu
MAINTAINER Sen Na <sen.na@realai.ai>

WORKDIR /code

ARG pip_registry='https://mirrors.aliyun.com/pypi/simple/'
ARG pip_dependencies=' \
      absl-py \
      contextlib2 \
      dm-tree>=0.1.5 \
      google-api-python-client \
      h5py \
      numpy \
      mock \
      oauth2client \
      pandas \
      termcolor \
      portpicker \
      dm-launchpad[reverb] \
      kubernetes'

RUN pip --no-cache-dir install -i $pip_registry $pip_dependencies

COPY . .
RUN pip install -i $pip_registry .
