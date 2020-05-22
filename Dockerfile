FROM arm64v8/python

ENV LIBRARY_PATH=/lib:/usr/lib

ADD src/requirements.txt /
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

WORKDIR /app
COPY src /app

CMD ["python", "-u", "/app/main.py"]
