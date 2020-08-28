import flask
import urllib.parse
import jwt

app = flask.Flask(__name__)

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
      <h2>Mock app</h2>
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
    <div class="alert alert-dark">
    Got token.
    </div>
    {% endif %}

    <div class="button-group">
     {% for k, v in links %}
     <a class="btn btn-primary" href="{{ v }}">{{ k }}</a>
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
        <tr><td>Header:</td><td><pre>{{ token.header | pprint }}</pre></td></tr>
        <tr><td>Unverified body:</td><td><pre>{{ token.raw | pprint }}</pre></td></tr>
      </table>
      <pre>
      </pre>
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

TODO_IDP_URL = '/auth/realms/keysight/'
TODO_CLIENT_ID = 'mock-web-app'

def render_page(**kw):
    d = dict(
        args=flask.request.args,
        form=flask.request.form,
        headers=flask.request.headers,
        what=None,
        links=[],
        debug_links=[],
    )
    d.update(kw)
    return flask.render_template_string(HTML, **d)

def login_url(**kw):
    args = dict(
      client_id=TODO_CLIENT_ID,
      redirect_uri=self_href() + 'callback/',
      response_type='token',
      scope='openid',
      nonce='beef',
    )
    args.update(kw)
    return TODO_IDP_URL + \
        'protocol/openid-connect/auth?' + \
         urllib.parse.urlencode(args)

@app.route("/")
def index():
    return render_page(what='index', links=[
        ('Login', login_url(response_mode='form_post')),
    ], debug_links=[
        ('Login (fragment)', login_url(reponse_mode='fragment')),
        ('Login (query)', login_url(response_mode='query')),
        ('Login (form_post)', login_url(response_mode='form_post')),
    ])

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
    return render_page(what='login callback', links=links + [
        ('Back to index', '..'),
    ])

@app.route("/introspect/")
def introspect():
    token = flask.request.args['token']
    hdr = jwt.get_unverified_header(token)
    raw = jwt.decode(token, verify=False)
    return render_page(what='token introspection',
        token = dict(
            header=hdr,
            raw=raw,
        ),
        links=[('Back to index', '..')],
    )
