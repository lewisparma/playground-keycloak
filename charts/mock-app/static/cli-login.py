#!/usr/bin/env python3

import os
import sys
import random
import string
import requests
import requests.auth
import time
import jwt
import pprint
import socket
import getpass
import signal
import urllib.parse

# TODO: unify with flask app main.py
MOCKAPP_IDP_PATH = os.environ.get('MOCKAPP_IDP_PATH', '/todo-idp/')
MOCKAPP_INTERNAL_BASE_URL = os.environ.get('MOCKAPP_INTERNAL_BASE_URL', 'http://nginx-ingress.default.svc')
MOCKAPP_IDP_INTERNAL_URL = urllib.parse.urljoin(MOCKAPP_INTERNAL_BASE_URL, MOCKAPP_IDP_PATH)

def wait_login(fname):
    secret_dir = "/run/secrets/mock-app/client"
    client_creds = {}
    try:
      for what in "CLIENT_ID", "CLIENT_SECRET":
          with open(os.path.join(secret_dir, what), 'r') as fp:
              client_creds[what] = fp.read()
    except:
        pass

    if client_creds:
       auth = requests.auth.HTTPBasicAuth(client_creds['CLIENT_ID'], client_creds['CLIENT_SECRET'])
       # TODO: get this from .well-known/openid-configuration .token_endpoint
       token_url = MOCKAPP_IDP_INTERNAL_URL + 'protocol/openid-connect/token'

       print("\nOr, log in ye olde way.")
       while True:
           user = input("SSO login: ")
           passwd = getpass.getpass("SSO password: ")
           resp = requests.post(token_url, auth=auth, data=dict(
               grant_type = 'password',
               username = user,
               password = passwd,
           )).json()
           for what in 'error', 'error_description':
               if what in resp:
                   print("%s: %r" % (what, resp[what]))
           if 'access_token' in resp:
               with open(fname, 'w') as fp:
                   # TODO: validate against JWKS
                   # (but, we're calling Keycloak directly...)
                   fp.write(resp['access_token'])
               return 0
    else:
       print("\nW: this application does not have client credentials available")
       sys.stdout.write("waiting for web UI login... ")
       spin = 0
       while True:
         sys.stdout.write('/-\|'[spin & 3] + chr(8))
         sys.stdout.flush()
         spin += 1
         time.sleep(0.25)
    return 0

def rand_str(length):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join((random.choice(letters_and_digits) for i in range(length)))

def who_am_i():
    "The returned list is, by definition, incomplete."
    try:
        name = requests.get("http://kcos-framework-vital.kcos-framework.svc/v1/hostname").json()["name"]
    except:
        return []
    res = set([name])
    # TODO: query this from vital-service
    try:
        gai = socket.getaddrinfo(name, 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE | socket.AI_CANONNAME)
        for family, socktype, proto, canonname, (host, port) in gai:
            if family == socket.AF_INET6:
                host = '[%s]' % host
            res.add(host)
            res.add(canonname)
    except:
        pass
    return res

if __name__ == "__main__":
    nonce = rand_str(16)
    fname = "/tmp/mock.token.%s" % nonce
    with open(fname, 'w') as fp:
       pass

    # TODO: multiple Ingress paths? nah.
    self_path = os.environ.get("MOCKAPP_SELF_PATH_0", "/todo-app-path/")
    url = '%scli/%s' % (self_path, nonce)
    print("\nWelcome, adventurer!\nTo log in, please use your browser and navigate to:\n\n"
        "    <however you reach this machine> %s" % url)
    names = who_am_i()
    if names:
        print("\nFor example, one of the following:\n")
        for name in names:
            print("    https://%s%s" % (name, url))

    # this is just because we're too lazy to poll()/cancel input()
    pid = os.fork()
    if pid == 0:
        sys.exit(wait_login(fname))
    while True:
       # TODO: inotify
       buf = ''
       with open(fname, 'r') as fp:
           buf = fp.read()
       if buf:
          break
       time.sleep(0.1)
    print(" \nGot a token!\n\n%s\n" % buf)
    os.kill(pid, signal.SIGTERM)
    os.waitpid(pid, 0)

    # TODO: verify against JWKS
    # (in this particular skeleton, the web app already did that)
    # (but of course we're not protecting the token file in any meaningful way)
    data = jwt.decode(buf, verify=False)
    pprint.pprint(data)
    print()

    username = data.get('username', data.get('preferred_username'))
    name = data.get('name', username)
    if name:
        print("Welcome %s!" % name)
    if username:
        print("You seem to be logging in as '%s'" % username)
