FROM python:3.10.11
MAINTAINER Sen Na <sen.na@realai.ai>

ARG pip_registry='https://mirrors.aliyun.com/pypi/simple/'
RUN pip install -i $pip_registry --upgrade pip

RUN pip --no-cache-dir install -i $pip_registry dm-launchpad[reverb,tensorflow] cloudpickle

WORKDIR /build

COPY . .

RUN pip install .

RUN rm -rf * && rm -rf .*; exit 0

CMD ['python', '-u', '-mlaunchpad_kubernetes.process_entry']
