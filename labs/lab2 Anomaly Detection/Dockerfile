FROM quay.io/jupyter/scipy-notebook

USER root
RUN mamba install -y polars && mamba clean -afy
USER jovyan

ENV JUPYTER_ENABLE_LAB=yes \
    JUPYTER_TOKEN="" \
    NB_UID=1000 \
    NB_GID=1000