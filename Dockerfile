# define alias so we can copy deps from it
FROM zapatacomputing/z-quantum-default:latest as zq-default


FROM ubuntu:focal

RUN apt update

RUN apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get install -y python3.7 && \
    apt-get install -y python3-pip && \
    apt-get install -y python3.7-dev

RUN apt install -y \
    git \
    wget \
    curl

# Use deps preinstalled in z-quantum-default.
# NOTE: if this breaks in the future consider using pip2py's local index for sharing prefetched
# dependencies (https://stackoverflow.com/a/12525448)
COPY --from=zq-default /usr/local/lib/python3.7/dist-packages/ /usr/local/lib/python3.7/dist-packages/

WORKDIR /app

RUN git clone https://github.com/zapatacomputing/z-quantum-core


RUN pip3 install z-quantum-core/

