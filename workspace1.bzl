load("@rules_pkg//:deps.bzl", "rules_pkg_dependencies")
load("@rules_python//python:pip.bzl", "pip_parse")
load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")
load("@rules_proto_grpc//:repositories.bzl", "rules_proto_grpc_toolchains", "rules_proto_grpc_repos")
load("@rules_proto_grpc//python:repositories.bzl", rules_proto_grpc_python_repos = "python_repos")
load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    container_repositories = "repositories",
)
load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")


def tiro_tts_workspace():
    pip_parse(
        name = "pip_deps",
        requirements_lock = "//:requirements.bazel.txt",
    )
    container_repositories()

    grpc_deps()

    rules_proto_grpc_toolchains()
    rules_proto_grpc_repos()
    rules_proto_dependencies()
    rules_proto_toolchains()
    rules_proto_grpc_python_repos()
    rules_pkg_dependencies()
