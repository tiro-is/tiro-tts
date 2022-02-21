load("@com_adobe_rules_gitops//gitops:defs.bzl", "k8s_deploy")

CLUSTER = "tullius"
USER = CLUSTER
NAMESPACE = "default"
REGISTRY = "eu.gcr.io"
REPOSITORY_PREFIX = "talgreining-is/k8s"

# This is a bit hacky but gets the job done. We're injecting the contents of
# /fetch_models.sh into the initContainers command
genrule(
    name = "expanded_base_deployment_yaml",
    srcs = [
        "base/deployment.yaml",
    ],
    tools = [
        "//:fetch_models",
    ],
    outs = ["expanded_deployment.yaml"],
    local = True,
    cmd = """\
sed 's/^/          /' $(location //:fetch_models) > indented_fetch_models.sh
sed "/{{FETCH_MODELS_SCRIPT}}/{
 r indented_fetch_models.sh
 d
}" $(location base/deployment.yaml) > $(location expanded_deployment.yaml)
    """,
)


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
        ":expanded_base_deployment_yaml",
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


PROD_CLUSTER = "gitlab-deploy"
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
        ":expanded_base_deployment_yaml",
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
