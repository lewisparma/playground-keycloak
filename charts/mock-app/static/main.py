import flask
import urllib.parse

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
      <p class="lead">This is a mock web app</p>
    </div>

    <div class="button-group">
      <a class="btn btn-primary" href="{{ login_url }}">Log in</a>
      <button type="button" class="btn btn-outline-info" data-toggle="collapse" data-target="#debugInfo">Debug info</button>
    </div>

    <div class="collapse" id="debugInfo">
      <hr class="mt-4">

      <h1>URL arguments:</h1>
      <table border="1">
      {% for k, v in args.items() %}
        <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
      {% endfor %}
      </table>

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
    return flask.render_template_string(HTML,
        args=flask.request.args,
        headers=flask.request.headers,
        login_url=TODO_IDP_URL +
            'protocol/openid-connect/auth?' +
            urllib.parse.urlencode(dict(
                client_id=TODO_CLIENT_ID,
                redirect_uri=self_href(),
                response_mode='query',
                response_type='token',
                scope='openid',
                nonce='beef',
            ))
    )

@app.route("/")
def index():
    return render_page()
