# keycloak-operator playground

## What's this?

It's a sandbox to try out interfacing with Keyclock as oauth2 IdP, and
the keycloak-operator for deployment as well.

Under `charts/`:
* [keycloak-operator](charts/keycloak-operator/) is just a repackage of the
  upstream operator deployment yamls (because it's a lot easier to
  `helmfile sync` the whole thing)
* [my-keycloak](charts/my-keycloak/) deploys (configs for the operator in
  order to get) a [`Keycloak`](charts/my-keycloak/templates/keycloak.yaml)
  service instance, as well as a single
  [`KeycloakRealm`](charts/my-keycloak/templates/basic_realm.yaml) -- we'd
  expect exactly one of these per appliance
* [mock-app](charts/mock-app/) deploys a sample application, as well as a
  [`KeycloakClient`](charts/mock-app/templates/keycloak-client.yaml) for
  itself in The One `KeycloakRealm`; there can be several of these per
  appliance

There's also a main [helmfile.yaml](helmfile.yaml) to tie them all together.
`helmfile sync` on a bare cluster (but with nginx-ingress and CNI installed)
for a quickstart.

## Notes

* `Ingress` provided by operator has wrong hostname; workaround: provide our own
  [`Ingress`](charts/my-keycloak/templates/ingress.yaml); also needed to set a
  larger `nginx.ingress.kubernetes.io/proxy-buffer-size` on it
* there doesn't seem to be a way to supply an initial keycloak-admin password;  use e.g.
  > `kubectl get secret -n auth credential-sso-my-keycloak -o go-template='{{ .data.ADMIN_PASSWORD | base64decode }}'`
* don't see a way to supply themes (might need to customize the docker image)
* only watches a single namespace -- deploy all `Keycloak*` CRDs into a designated one?
* `Secret` objects with client secrets are created in the single namespace,
  too -- can't mount them as volumes in the app namespace(s)
* operator doesn't handle all cases, e.g. `KeycloakRealm` created after `KeycloakClient`
  (client is not created -- it is after restarting the operator though)
* account/ page operations seem to say "An internal server error has occurred" on any changes
* to enable debugging, one can set `$KEYCLOAK_LOGLEVEL=DEBUG` and/or
  `$ROOT_LOGLEVEL=DEBUG` on the `StatefulSet` `env`; but! need to kill the operator,
  otherwise it nukes them off
