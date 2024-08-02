FROM ubuntu:22.04

# parameters that might be provided at runtime by using the --env option
ENV BACKEND_URL=""
ENV SERVER_PORT=8501

# install dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -yq bash curl wget ca-certificates python3 python3-pip 

# copy the application files
COPY . /app
WORKDIR /app

# install python dependencies
RUN python3 --version
RUN python3 -m pip install --upgrade pip 
RUN python3 -m pip install -r requirements.txt

EXPOSE $SERVER_PORT

# set all environment variables
ENTRYPOINT ["sh", "-c", "\
    export BACKEND_URL=$BACKEND_URL \
    export SERVER_PORT=$SERVER_PORT \
    && echo \"BACKEND_URL: $BACKEND_URL\" \
    && echo \"SERVER_PORT: $SERVER_PORT\" \
    && streamlit run client.py --server.port=$SERVER_PORT --server.address=0.0.0.0 \
"]
