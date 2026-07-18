FROM quay.io/jupyter/scipy-notebook

USER root
RUN mamba install -y polars && mamba clean -afy
RUN pip install --no-cache-dir keras torch
USER jovyan

ENV KERAS_BACKEND=torch \
    JUPYTER_ENABLE_LAB=yes \
    JUPYTER_TOKEN="" \
    NB_UID=1000 \
    NB_GID=1000
