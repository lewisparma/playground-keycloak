import flask
import urllib.parse
import jwt
import requests
import json
import os
import os.path

app = flask.Flask(__name__)

MOCKAPP_FULLNAME = os.environ.get('MOCKAPP_FULLNAME')
MOCKAPP_CLIENT_ID = os.environ.get('MOCKAPP_CLIENT_ID', 'todo-client-id')
# This could be absolute (but typically is not):
MOCKAPP_IDP_PATH = os.environ.get('MOCKAPP_IDP_PATH', '/todo-idp/')
MOCKAPP_INTERNAL_BASE_URL = os.environ.get('MOCKAPP_INTERNAL_BASE_URL', 'http://nginx-ingress.default.svc')

MOCKAPP_IDP_INTERNAL_URL = urllib.parse.urljoin(MOCKAPP_INTERNAL_BASE_URL, MOCKAPP_IDP_PATH)


def self_href():
    return '%s://%s%s' % (
        flask.request.headers.get('X-Scheme') or
        flask.request.headers.get('X-Forwarded-Proto') or
        'http',
        flask.request.headers.get('Host'),
        flask.request.headers.get('X-Original-Uri', '').split('?', 1)[0] or
        flask.request.path,
    )


HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    <title>Mock app</title>
  </head>
  <body class="bg-light">
    <div class="container" style="max-width: 90%">
      <div class="py-5 text-center">
      <h2>Mock app {{ fullname }}</h2>
      {% if what %}
      <p class="lead">This is the {{ what }} page.</p>
      {% endif %}
    </div>
    
    {% if args.error %}
    <div class="alert alert-danger">
      IdP said:<br>
      <b>Error:</b> {{ args.error }}<br>
      <b>Error description:</b> {{ args.error_description }}<br>
    </div>
    {% endif %}

    {% if token %}
      {% if token.ok %}
        <div class="alert alert-dark">
        Got legit token. Welcome, <i>{{ token.data.name }}</i>!
        {% if token.shell %}
        <h3>You may now return to your CLI terminal.</h3>
        {% endif %}
        </div>
      {% else %}
      <div class="alert alert-danger">
          <b>Token verification failed:</b> {{ token.err }}
      </div>
      {% endif %}
    {% endif %}

    <div class="button-group">
     {% for k, v in links %}
     <a class="btn btn-primary" href="{{ v }}">{{ k }}</a>
     {% endfor %}
     {% for k, v in extra_links %}
     <a class="btn btn-secondary" href="{{ v }}">{{ k }}</a>
     {% endfor %}

      <button type="button" class="btn btn-outline-info" data-toggle="collapse" data-target="#debugInfo">Debug info</button>
    </div>

    <div class="collapse" id="debugInfo">
      <hr class="mt-4">

      <div class="button-group">
        {% for k, v in debug_links %}
        <a class="btn btn-primary" href="{{ v }}">{{ k }}</a>
        {% endfor %}
      </div>

      {% if token %}
      <h1>Token:</h1>
      <table border="1">
        {% for k, v in token.dbg.items() %}
          <tr><td>{{ k }}:</td><td><pre>{{ v | pprint }}</pre></td></tr>
        {% endfor %}
      </table>
      {% endif %}

      {% if args %}
      <h1>URL arguments:</h1>
      <table border="1">
      {% for k, v in args.items() %}
        <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
      {% endfor %}
      </table>
      {% endif %}

      {% if form %}
      <h1>Form:</h1>
      <table border="1">
      {% for k, v in form.items() %}
        <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
      {% endfor %}
      </table>
      {% endif %}

      <h1>Headers:</h1>
      <table border="1">
      {% for k, v in headers.items() %}
        <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
      {% endfor %}
      </table>
      </div>
    </div>
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
  </body>
</html>
"""

def render_page(**kw):
    d = dict(
        args=flask.request.args,
        form=flask.request.form,
        headers=flask.request.headers,
        fullname=MOCKAPP_FULLNAME,
        what=None,
        links=[],
        debug_links=[],
    )
    d.update(kw)
    return flask.render_template_string(HTML, **d)

def login_url(**kw):
    args = dict(
      client_id=MOCKAPP_CLIENT_ID,
      redirect_uri=self_href() + 'callback/',
      response_type='token',
      scope='openid',
      nonce='beef',
    )
    args.update(kw)
    # TODO: get this path from .well-known authorization_endpoint
    return MOCKAPP_IDP_PATH + \
        'protocol/openid-connect/auth?' + \
         urllib.parse.urlencode(args)

@app.route("/")
def index():
    return render_page(what='index', links=[
        ('Login', login_url(response_mode='form_post')),
        # TODO: get this from .well-known end_session_endpoint
        # TODO: use XHR, this doesn't render a page
        ('Logout', MOCKAPP_IDP_PATH + 'protocol/openid-connect/logout'),
    ], extra_links=[
        # these are very keycloak specific
        ('Account page', MOCKAPP_IDP_PATH + 'account/'),
        ('Realm admin console', MOCKAPP_IDP_PATH.replace('/realms/', '/admin/') + 'console/'),
    ], debug_links=[
        ('Login (fragment)', login_url(reponse_mode='fragment')),
        ('Login (query)', login_url(response_mode='query')),
        ('Login (form_post)', login_url(response_mode='form_post')),
    ])

@app.route('/cli/<nonce>')
def cli_login(nonce):
    return flask.redirect(login_url(
        response_mode='form_post',
        nonce='shell.%s' % nonce,
        redirect_uri=urllib.parse.urljoin(self_href(), '../callback/'),
    ))

def verify_token(hdr, token, dbg):
    assert hdr['typ'] == 'JWT', "JWT type is not JWT"
    assert hdr['alg'] == 'RS256', "Only RS256 alg supported for now"
    kid = hdr['kid']
    # TODO: cache
    dbg['OpenID configuration URL'] = cfg_url = MOCKAPP_IDP_INTERNAL_URL + '.well-known/openid-configuration'
    dbg['OpenID configuration'] = openid_config = requests.get(cfg_url).json()
    dbg['JWKS URL'] = jwks_uri = openid_config['jwks_uri']
    dbg['JWKS data'] = jwks = requests.get(jwks_uri).json()
    for key in jwks['keys']:
        if key['kid'] == kid:
            pubkey = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
            # TODO: is that the right 'aud'?
            res = jwt.decode(token, pubkey, algorithms=[hdr['alg']], audience='account')
            azp = res['azp']
            assert azp == MOCKAPP_CLIENT_ID, "Token not for us (got %r, expected %r)" % (azp, MOCKAPP_CLIENT_ID)
            return res
    raise ValueError('kid %r not in JWKS keyring' % kid)

def do_introspect(what='token introspection', token_str=None):
    dbg = {}
    dbg['Header'] = hdr = jwt.get_unverified_header(token_str)
    dbg['Raw body'] = jwt.decode(token_str, verify=False)
    shell = False
    try:
        data = verify_token(hdr, token_str, dbg)
        nonce = data.get('nonce', '')
        if nonce.startswith('shell.'):
            fname = nonce.split('.', 1)[-1].replace('/', '_')
            fname = '/tmp/mock.token.%s' % fname
            if os.path.exists(fname):
                with open(fname, 'w') as fp:
                    fp.write(json.dumps(data))
                shell = True
                dbg['Token file'] = fname
        ok = True
        err = ''
    except Exception as e:
        ok = False
        err = '%r -- %s' % (e, e)
        data = {}
    return render_page(what=what,
        token = dict(
            dbg=dbg,
            ok=ok,
            err=err,
            data=data,
            shell=shell,
        ),
        links=[('Back to index', '..')],
    )

@app.route("/introspect/")
def introspect():
    return do_introspect(
        what='token introspection',
        token_str=flask.request.args['token'],
    )

@app.route("/callback/", methods=['GET', 'POST'])
def callback():
    links = []
    token = flask.request.form.get('access_token') or flask.request.args.get('access_token')
    if token:
        links += [
            ('Verify token', '../introspect/?' +
                urllib.parse.urlencode(dict(token=token)),
            ),
        ]
        if True: # HACK
          return do_introspect(what='login callback', token_str=token)
    return render_page(what='login callback', links=links + [
        ('Back to index', '..'),
    ])
