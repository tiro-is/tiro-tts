load("@rules_pkg//:deps.bzl", "rules_pkg_dependencies")
load("@rules_python//python:pip.bzl", "pip_parse")
load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")
load("@rules_proto_grpc//:repositories.bzl", "rules_proto_grpc_toolchains", "rules_proto_grpc_repos")
load("@rules_proto_grpc//python:repositories.bzl", rules_proto_grpc_python_repos = "python_repos")
load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    container_repositories = "repositories",
)
load("//tools/py:defs.bzl", "python_interpreter")


def tiro_tts_workspace():
    setup_mostly_hermetic_python_toolchain()

    pip_parse(
        name = "pip_deps",
        requirements_lock = "//:requirements.bazel.txt",
        python_interpreter_target = "@python_interpreter//:python_bin",
    )
    container_repositories()

    rules_proto_grpc_toolchains()
    rules_proto_grpc_repos()
    rules_proto_dependencies()
    rules_proto_toolchains()
    rules_proto_grpc_python_repos()
    rules_pkg_dependencies()


def setup_mostly_hermetic_python_toolchain():
    python_interpreter(
        name = "python_interpreter",
        py_version = "3.8.3",
        sha256 = "dfab5ec723c218082fe3d5d7ae17ecbdebffa9a1aea4d64aa3a2ecdd2e795864",
    )
