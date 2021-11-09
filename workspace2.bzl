load("@pip_deps//:requirements.bzl", install_pip_requirements = "install_deps")
load("@rules_python//python:pip.bzl", "pip_install")
load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")
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

        # Python 3.8-slim-bullseye 2021-11-09
        digest = "sha256:7b81bfd796e2786baf4af3319f305dd22d6cafbf64cef97a393deab99ebf9336",

        # distroless 3.7
        # digest = "sha256:80a90be7e33b931284194ba32c3af8fd8745017cfee18ba22c8269ae286f16f8",
    )
    _py3_image_repos()

    grpc_deps()

    native.register_toolchains("//tools/py:py_toolchain")
