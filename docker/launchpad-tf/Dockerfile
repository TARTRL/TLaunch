FROM python:3.10.11
MAINTAINER Sen Na <sen.na@realai.ai>

WORKDIR /code

ARG pip_registry='https://mirrors.aliyun.com/pypi/simple/'
RUN pip install -i $pip_registry --upgrade pip

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
      dm-launchpad[tensorflow,reverb] \
      kubernetes'
RUN pip --no-cache-dir install -i $pip_registry $pip_dependencies

COPY . .
RUN pip install -i $pip_registry . --use-feature=in-tree-build
