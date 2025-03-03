FROM nvidia/cuda:11.4.1-devel-ubuntu20.04 

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y tzdata

ENV TZ=Asia/Tokyo 

RUN apt-get update &&\
    apt-get -y install build-essential yasm cmake libtool libc6 libc6-dev unzip wget libnuma1 libnuma-dev git pkg-config curl &&\
    apt-get clean  &&\
    rm -r /var/lib/apt/lists/*


WORKDIR /WORKDIR

RUN git clone https://github.com/FFmpeg/nv-codec-headers.git &&\
    cd nv-codec-headers && \
    make install && \
    cd /WORKDIR && \
    rm -r nv-codec-headers


RUN git clone https://github.com/FFmpeg/FFmpeg ffmpeg/ &&\
    cd ffmpeg && \
    ./configure \
        --enable-nonfree \
        --enable-cuda-nvcc \
        --enable-libnpp \
        --extra-cflags=-I/usr/local/cuda/include \
        --extra-ldflags=-L/usr/local/cuda/lib64 \
        --nvccflags="-gencode arch=compute_75,code=sm_75 -O2" &&\
    make -j$(nproc) && \
    make install && \
    cd /WORKDIR && \
    rm -r ffmpeg && \
    mkdir -p /opt/bin && \
    mv /usr/local/bin/ffmpeg /opt/bin/ffmpeg && \
    mv /usr/local/bin/ffprobe /opt/bin/ffprobe 


RUN apt-get update &&\
    apt-get -y install ffmpeg i965-va-driver-shaders intel-media-va-driver-non-free &&\
    apt-get clean  &&\
    rm -r /var/lib/apt/lists/*

RUN apt-get update &&\
    apt-get -y install python3-pip  &&\
    apt-get clean  &&\
    rm -r /var/lib/apt/lists/*

RUN pip3 install -U fastapi uvicorn[standard] aiohttp aiofiles python-multipart aiopath


WORKDIR /
CMD /bin/bash
