#!/bin/sh

# TODO: build our own docker image
pip install pyjwt==1.7.1 requests==2.24.0
pip install pyjwt[crypto]

mkdir -p /run/kcos/token

cp -vf cli-login.py /bin/mock-cli-login
chmod +x /bin/mock-cli-login
