FROM python:3.14-slim 
WORKDIR /src/app
#RUN apt-get update \
# && apt-get install -y docker.io \
# && rm -rf /var/lib/apt/lists/*

# Instead of obove installing entire docker, copying only docker cli should be faster and smaller:
COPY --from=docker:26-cli /usr/local/bin/docker /usr/local/bin/docker
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN mkdir -p received

ENV FLASK_RUN_PORT=8001
EXPOSE 8001
CMD ["flask", "run", "--debug", "--host=0.0.0.0"]
