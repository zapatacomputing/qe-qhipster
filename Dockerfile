# ------ Aliases ------

# Used to prepopulate pip dependencies
FROM zapatacomputing/z-quantum-default:latest as zq-default

# Nowadays we don't have access to the full toolchain needed to build native qHipster
# binaries. We can copy the built binaries from previous versions of this image, though.
FROM zapatacopmuting/qe-qhipster@sha256:558d25915f002e0cc0460cd0d65a010f3a45e862dcae614fcc7e5c85d42136ea as old-qe-qhipster


# ------ Main image ------

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

# TODO: rearrange the layers
RUN git clone https://github.com/zapatacomputing/z-quantum-core
RUN pip3 install z-quantum-core/

COPY . .
RUN pip3 install -e .[dev]

COPY --from=old-qe-qhipster /app/zapata /app/zapata
# RUN pytest tests

