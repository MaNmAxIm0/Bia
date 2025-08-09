FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get install -y \
    ffmpeg \
    libimage-exiftool-perl \
    libblas3 \
    ghostscript \
    libreoffice-impress \
    sudo     curl     unzip &&     rm -rf /var/lib/apt/lists/*

RUN curl https://rclone.org/install.sh | sudo bash

RUN apt-get update -y &&     apt-get install -y python3 python3-venv python3-pip &&     rm -rf /var/lib/apt/lists/*COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt --break-system-packages

WORKDIR /app

COPY . /app

