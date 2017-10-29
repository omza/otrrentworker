FROM ubuntu:latest
MAINTAINER oliver@app-workshop.de

# Install Python3 and pip
# -------------------------------------------------------
# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
		ca-certificates \
		libexpat1 \
		libffi6 \
		libgdbm3 \
		libsqlite3-0 \
		libssl1.0.0 \
	&& rm -rf /var/lib/apt/lists/*

ENV GPG_KEY 97FC712E4C024BBEA48A61ED3A5CA953F73C700D
ENV PYTHON_VERSION 3.5.4

RUN set -ex \
	&& buildDeps=' \
		dpkg-dev \
		gcc \
		libbz2-dev \
		libc6-dev \
		libexpat1-dev \
		libffi-dev \
		libgdbm-dev \
		liblzma-dev \
		libncurses-dev \
		libreadline-dev \
		libsqlite3-dev \
		libssl-dev \
		make \
		tcl-dev \
		tk-dev \
		wget \
		xz-utils \
		zlib1g-dev \
	' \
	&& apt-get update && apt-get install -y $buildDeps --no-install-recommends && rm -rf /var/lib/apt/lists/* \
	\
	&& wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz" \
	&& wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEY" \
	&& gpg --batch --verify python.tar.xz.asc python.tar.xz \
	&& rm -rf "$GNUPGHOME" python.tar.xz.asc \
	&& mkdir -p /usr/src/python \
	&& tar -xJC /usr/src/python --strip-components=1 -f python.tar.xz \
	&& rm python.tar.xz \
	\
	&& cd /usr/src/python \
	&& gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)" \
	&& ./configure \
		--build="$gnuArch" \
		--enable-loadable-sqlite-extensions \
		--enable-shared \
		--with-system-expat \
		--with-system-ffi \
		--without-ensurepip \
	&& make -j "$(nproc)" \
	&& make install \
	&& ldconfig \
	\
	&& apt-get purge -y --auto-remove $buildDeps \
	\
	&& find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' + \
	&& rm -rf /usr/src/python

# make some useful symlinks that are expected to exist
RUN cd /usr/local/bin \
	&& ln -s idle3 idle \
	&& ln -s pydoc3 pydoc \
	&& ln -s python3 python \
	&& ln -s python3-config python-config

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 9.0.1

RUN set -ex; \
	\
	apt-get update; \
	apt-get install -y --no-install-recommends wget; \
	rm -rf /var/lib/apt/lists/*; \
	\
	wget -O get-pip.py 'https://bootstrap.pypa.io/get-pip.py'; \
	\
	apt-get purge -y --auto-remove wget; \
	\
	python get-pip.py \
		--disable-pip-version-check \
		--no-cache-dir \
		"pip==$PYTHON_PIP_VERSION" \
	; \
	pip --version; \
	\
	find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' +; \
	rm -f get-pip.py

# Copy docker context to tmp
# ----------------------------------------------------------
COPY ./otrrentworker /tmp/

# Environment Variables
# -------------------------------------------------------
ENV OTR_DECODER otrdecoder-bin-x86_64-unknown-linux-gnu-0.4.1133
ENV PATH $PATH:/root/bin
ENV APPLICATION_ENVIRONMENT=Production

# install app & prerequisites
# -----------------------------------------------------------
RUN \
	apt-get update && \
	apt-get -y install bzip2 transmission-cli transmission-common transmission-daemon && \ 
	tar -jxf /tmp/$OTR_DECODER.tar.bz2 -C ~/ && \
	cd ~/$OTR_DECODER && \
	./install.sh && \
	cd / && \
	rm -rf /tmp/$OTR_DECODER.tar.bz2 && \
	mkdir -p /usr/app && \
	mkdir -p /usr/torrents && \
	mkdir -p /usr/otrkeys && \
	mkdir -p /usr/videos && \
	mkdir -p /usr/log && \
	mv /tmp/* /usr/app/ && \
	pip install --no-cache-dir -r /usr/app/requirements.txt && \
	rm -rf /var/lib/transmission-daemon/info/settings.json && \
	mv /usr/app/config/settings.json /var/lib/transmission-daemon/info/settings.json && \ 
	apt-get remove --purge -y --auto-remove bzip2 && \
	rm -rf /var/lib/apt/lists/* && \
	apt-get clean

# Make volumes
# -------------------------------------------------------
VOLUME /usr/app/
VOLUME /usr/app/config/secrets/
VOLUME /usr/log/
VOLUME /usr/torrents/
VOLUME /usr/otrkeys/
VOLUME /usr/videos/

# Start/Stop
# -------------------------------------------------------
STOPSIGNAL SIGTERM
WORKDIR /usr/app/
ENTRYPOINT ["python3", "/usr/app/otrrentworker.py"]
