FROM python:2-alpine
MAINTAINER Simon Westerdahl "simon.westerdahl@hotmail.se"

COPY . /src
RUN cd src && pip install -e .

WORKDIR /out

ENTRYPOINT ["/usr/local/bin/openapi2jsonschemasingleschema"]
CMD ["--help"]
