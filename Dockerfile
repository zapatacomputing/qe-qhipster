# ------ Aliases ------

# Nowadays we don't have access to the full toolchain needed to build native qHipster
# binaries. We can copy the built binaries from previous versions of this image, though.
FROM zapatacopmuting/qe-qhipster@sha256:558d25915f002e0cc0460cd0d65a010f3a45e862dcae614fcc7e5c85d42136ea as old-qe-qhipster


# ------ Main image ------

# Using z-quantum-default as the base because it contains preinstalled pip dependencies for
# z-quantum-core and this way we may reuse them.
FROM zapatacomputing/z-quantum-default:latest

# Use toolchain and built simulator binaries cached in previous version of this image.
COPY --from=old-qe-qhipster /opt/intel/psxe_runtime_2019.3.199/linux /opt/intel/psxe_runtime_2019.3.199/linux
COPY --from=old-qe-qhipster /app/zapata /app/zapata
COPY --from=old-qe-qhipster /app/json_parser /app/json_parser

RUN apt update
RUN apt install -y \
    git \
    wget \
    curl

WORKDIR /app

