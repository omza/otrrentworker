FROM ubuntu:latest
MAINTAINER oliver@app-workshop.de

# Update & Upgrade & Prerequisites
# -------------------------------------------------------
RUN \
	apt-get update && \
	apt-get -y upgrade && \
	apt-get -y install wget bzip2 python3 python3-pip


# Install otr Easy Decoder (Console 64bit)
# -------------------------------------------------------
ENV OTR_DECODER otrdecoder-bin-x86_64-unknown-linux-gnu-0.4.1133

RUN \
	wget -P /tmp http://www.onlinetvrecorder.com/downloads/$OTR_DECODER.tar.bz2 && \
	tar -jxf /tmp/$OTR_DECODER.tar.bz2 -C ~/ && \
	cd ~/$OTR_DECODER && \
	ls -l && \
	./install.sh && \
	cd / && \
	rm -rf /tmp/$OTR_DECODER.tar.bz2

ENV PATH $PATH:/root/bin


# Install bittorrentclient requirements
# -------------------------------------------------------

# Make directories & volumes
RUN \
	mkdir -p /usr/app && \
	#mkdir -p /usr/otrkey && \
	mkdir -p /usr/log

VOLUME /usr/app/
VOLUME /usr/log/
VOLUME /tmp/
#VOLUME /usr/otrkey/	
	
# install pip requirements	
COPY ./otrrentworker /usr/app/
RUN pip3 install --no-cache-dir -r /usr/app/requirements.txt

# Start/Stop
STOPSIGNAL SIGTERM
ENTRYPOINT ["python3", "/usr/app/otrrentworker.py"]
