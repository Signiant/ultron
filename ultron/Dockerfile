FROM python:2.7-alpine

RUN apk --no-cache add ca-certificates

RUN mkdir /src

COPY ultron/ /src/

WORKDIR /src

RUN pip install -r requirements.txt

ENTRYPOINT ["python","/src/ultron.py"]
CMD ["-h"]