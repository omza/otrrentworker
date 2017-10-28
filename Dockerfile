FROM ubuntu:latest
MAINTAINER oliver@app-workshop.de

# Environment
# -------------------------------------------------------
ENV OTR_DECODER otrdecoder-bin-x86_64-unknown-linux-gnu-0.4.1133
ENV PATH $PATH:/root/bin


# Update & Upgrade & Install Prerequisites
# -------------------------------------------------------
COPY ./otrrentworker/requirements.txt /usr/app/requirements.txt
RUN \
	apt-get update && \
	apt-get -y upgrade && \
	apt-get -y install wget bzip2 python3 python3-pip && \
	pip install --upgrade pip && \
	wget -P /tmp http://www.onlinetvrecorder.com/downloads/$OTR_DECODER.tar.bz2 && \
	tar -jxf /tmp/$OTR_DECODER.tar.bz2 -C ~/ && \
	cd ~/$OTR_DECODER && \
	ls -l && \
	./install.sh && \
	cd / && \
	rm -rf /tmp/$OTR_DECODER.tar.bz2 && \
	mkdir -p /usr/app && \
	mkdir -p /usr/torrents && \
	mkdir -p /usr/otrkeys && \
	mkdir -p /usr/videos && \
	mkdir -p /usr/log && \
	pip3 install --no-cache-dir -r /usr/app/requirements.txt && \
	apt-get autoremove -y && \
	rm -rf /var/lib/apt/lists/* && \
	apt-get clean

# Make directories & volumes
# -------------------------------------------------------
VOLUME /usr/app/
VOLUME /usr/app/config/secrets/
VOLUME /usr/log/
VOLUME /usr/torrents/
VOLUME /usr/otrkeys/
VOLUME /usr/videos/
	
# install app
# -----------------------------------------------------------
COPY ./otrrentworker /usr/app/

# Start/Stop
STOPSIGNAL SIGTERM
ENTRYPOINT ["python3", "/usr/app/otrrentworker.py"]
