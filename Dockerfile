FROM python:3.11-alpine

COPY requirements.txt ./

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# set timezone
RUN ln -s -f /usr/share/zoneinfo/Brazil/East /etc/localtime

COPY . /opt/watcher/

WORKDIR /opt/watcher


CMD [ "python3", "watcher.py", "-o", "/tmp/watcher"]