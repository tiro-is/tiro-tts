workspace(
    name = "com_gitlab_tiro_is_tiro_tts"
)

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

rules_python_version = "0.2.0"

http_archive(
    name = "rules_python",
    sha256 = "778197e26c5fbeb07ac2a2c5ae405b30f6cb7ad1f5510ea6fdac03bded96cc6f",
    url = "https://github.com/bazelbuild/rules_python/releases/download/{v}/rules_python-{v}.tar.gz".format(v = rules_python_version),
)

###########################################
# Python dependencies from requirements.txt
load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "pip_deps",
    requirements_lock = "//:requirements.bazel.txt"
)

load("@pip_deps//:requirements.bzl", "install_deps")
install_deps()


#################################################
# rules_docker required to build container images
io_bazel_rules_docker_version = "0.17.0"

http_archive(
    name = "io_bazel_rules_docker",
    sha256 = "59d5b42ac315e7eadffa944e86e90c2990110a1c8075f1cd145f487e999d22b3",
    strip_prefix = "rules_docker-{}".format(io_bazel_rules_docker_version),
    urls = [
        "https://github.com/bazelbuild/rules_docker/releases/download/v{v}/rules_docker-v{v}.tar.gz".format(
            v = io_bazel_rules_docker_version,
        ),
    ],
)

###############################
# Dependencies for rules_docker
load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    container_repositories = "repositories",
)

container_repositories()

load("@io_bazel_rules_docker//repositories:deps.bzl", container_deps = "deps")

container_deps()

# pull in a custom base image to use Python 3.8
load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_pull",
)

container_pull(
    name = "py3_8_image_base",
    registry = "docker.io",
    repository = "library/python",

    # Python 3.8.9-slim
    digest = "sha256:9a88d644ef19ab2b16061d4aa8ea5cb140a5fd2e76e6b858b0f139e68f40f984",

    # distroless 3.7
    # digest = "sha256:80a90be7e33b931284194ba32c3af8fd8745017cfee18ba22c8269ae286f16f8",
)

load(
    "@io_bazel_rules_docker//python3:image.bzl",
    _py3_image_repos = "repositories",
)

_py3_image_repos()


########################################
# rules_gitops needed for k8s deployment
rules_gitops_version = "8d9416a36904c537da550c95dc7211406b431db9"

http_archive(
    name = "com_adobe_rules_gitops",
    sha256 = "25601ed932bab631e7004731cf81a40bd00c9a34b87c7de35f6bc905c37ef30d",
    strip_prefix = "rules_gitops-{}".format(rules_gitops_version),
    urls = ["https://github.com/adobe/rules_gitops/archive/{}.zip".format(rules_gitops_version)],
)

###########################
# rules_gitops dependencies
load("@com_adobe_rules_gitops//gitops:deps.bzl", "rules_gitops_dependencies")

rules_gitops_dependencies()

load("@com_adobe_rules_gitops//gitops:repositories.bzl", "rules_gitops_repositories")

rules_gitops_repositories()
