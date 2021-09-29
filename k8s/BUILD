load("@com_adobe_rules_gitops//gitops:defs.bzl", "k8s_deploy")

CLUSTER = "tullius"
USER = CLUSTER
NAMESPACE = "default"
REGISTRY = "eu.gcr.io"
REPOSITORY_PREFIX = "talgreining-is/k8s"

k8s_deploy(
    name = "dev",
    cluster = CLUSTER,
    image_digest_tag = True,
    image_registry = REGISTRY,
    image_repository_prefix = REPOSITORY_PREFIX,
    image_repository = "tiro-tts",
    images = {
        "tiro-tts": "//:tiro-tts_image",
    },
    manifests = [
        "base/deployment.yaml",
        "base/ingress.yaml",
        "base/service.yaml",
    ],
    patches = glob(
        ["overlays/dev/**/*.yaml"],
        exclude = ["**/kustomization.yaml", "**/configmap.yaml"]
    ),
    common_labels = {
        "environment": "dev",
    },
    name_prefix = "dev-",
    user = USER,
    namespace = NAMESPACE,
    deployment_branch = "master",
    release_branch_prefix = "master",
)


PROD_CLUSTER = "gke_talgreining-is_europe-west1-b_talgreinir-is-cluster"
PROD_USER = PROD_CLUSTER
k8s_deploy(
    name = "prod",
    cluster = PROD_CLUSTER,
    image_digest_tag = True,
    image_registry = REGISTRY,
    image_repository_prefix = REPOSITORY_PREFIX,
    image_repository = "tiro-tts",
    images = {
        "tiro-tts": "//:tiro-tts_image",
    },
    manifests = [
        "base/deployment.yaml",
        "base/ingress.yaml",
        "base/service.yaml",
    ],
    patches = glob(
        ["overlays/prod/**/*.yaml"],
        exclude = ["**/kustomization.yaml", "**/configmap.yaml"]
    ),
    user = PROD_USER,
    namespace = NAMESPACE,
    deployment_branch = "master",
    release_branch_prefix = "master",
)
