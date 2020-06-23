FROM python:3-alpine
ADD data-template /data-template
ADD src /src
RUN mkdir /data
RUN pip install pyyaml paho-mqtt yeelight
WORKDIR /
CMD [ "sh", "-c", "sh /src/fillEmpty.sh && python src/main.py" ]