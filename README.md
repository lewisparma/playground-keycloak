# keycloak-operator playground

## Notes

* `Ingress` provided by operator has wrong hostname; workaround: provide our own `Ingress`
* there doesn't seem to be a way to supply an initial keycloak-admin password;  use e.g.
  `kubectl get secret -n auth credential-sso-my-keycloak -o go-template='{{ .data.ADMIN_PASSWORD | base64decode }}'`
* don't see a way to supply themes (might need to customize the docker image)
* only watches a single namespace -- deploy all Keycloak* CRDs into a designated one?
