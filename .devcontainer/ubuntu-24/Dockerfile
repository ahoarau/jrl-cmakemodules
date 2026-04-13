FROM ubuntu:24.04

ARG USERNAME
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ${USERNAME}

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/home/${USERNAME}/.pixi/bin:${PATH}"
