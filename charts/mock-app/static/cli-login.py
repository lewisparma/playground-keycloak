#!/usr/bin/env python3

import os
import sys
import random
import string
import requests
import time
import jwt
import pprint
import socket

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

    spin = 0
    while True:
       # TODO: inotify
       buf = ''
       with open(fname, 'r') as fp:
           buf = fp.read()
       if buf:
          break
       sys.stdout.write('/-\|'[spin & 3] + chr(8))
       sys.stdout.flush()
       spin += 1
       time.sleep(0.1)
    print("\nGot one!\n\n%s\n" % buf)

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
