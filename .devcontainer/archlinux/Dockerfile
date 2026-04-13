FROM archlinux:latest

ARG USERNAME
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm curl ca-certificates git && \
    pacman -Sc --noconfirm

RUN useradd -m -s /bin/bash ${USERNAME}

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/home/${USERNAME}/.pixi/bin:${PATH}"
