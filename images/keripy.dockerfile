ARG BASE=python:3.12.15-alpine3.23@sha256:3d0ca66b723a0ff2a7a6e424cc2d01443e1b7c75ffcc110145f75d0f4daf6d63
FROM ${BASE} AS base

# Update platform trust and the system pip independently of application packages.
RUN apk upgrade --no-cache && apk add --no-cache bash ca-certificates libsodium-dev binutils \
    && update-ca-certificates
RUN python -m pip install --no-cache-dir \
    'pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70'

FROM base AS builder
RUN apk add --no-cache build-base libffi-dev libsodium-dev cargo
WORKDIR /keripy
COPY setup.py ./
COPY src/ src/
RUN python -m pip install --no-cache-dir 'setuptools>=84.1.0' 'wheel>=0.46.2' \
    && python -m pip wheel --no-build-isolation --no-deps --wheel-dir /wheels .
RUN python -m venv --without-pip /keripy/venv \
    && python -m pip --python /keripy/venv install --no-cache-dir /wheels/*.whl \
    && python -m pip --python /keripy/venv check

FROM base
WORKDIR /keripy
COPY --from=builder /keripy/venv /keripy/venv
# Runtime installation is complete; omit installers and ensurepip's old bundle.
RUN python -m pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.12/ensurepip
ENV PATH="/keripy/venv/bin:${PATH}"
ENTRYPOINT ["kli"]
