load("@pip_deps//:requirements.bzl", install_pip_requirements = "install_deps")
load("@io_bazel_rules_docker//repositories:deps.bzl", container_deps = "deps")
load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_pull",
)
load(
    "@io_bazel_rules_docker//python3:image.bzl",
    _py3_image_repos = "repositories",
)

def tiro_tts_workspace():
    install_pip_requirements()
    container_deps()
    container_pull(
        name = "py3_8_image_base",
        registry = "docker.io",
        repository = "library/python",

        # Python 3.8.9-slim
        digest = "sha256:9a88d644ef19ab2b16061d4aa8ea5cb140a5fd2e76e6b858b0f139e68f40f984",

        # distroless 3.7
        # digest = "sha256:80a90be7e33b931284194ba32c3af8fd8745017cfee18ba22c8269ae286f16f8",
    )
    _py3_image_repos()
