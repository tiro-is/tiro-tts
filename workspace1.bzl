load("@rules_python//python:pip.bzl", "pip_parse")
load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")
load("@rules_proto_grpc//:repositories.bzl", "rules_proto_grpc_toolchains", "rules_proto_grpc_repos")
load("@rules_proto_grpc//python:repositories.bzl", rules_proto_grpc_python_repos = "python_repos")
load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    container_repositories = "repositories",
)

def tiro_tts_workspace():
    pip_parse(
        name = "pip_deps",
        requirements_lock = "//:requirements.bazel.txt"
    )
    container_repositories()

    rules_proto_grpc_toolchains()
    rules_proto_grpc_repos()
    rules_proto_dependencies()
    rules_proto_toolchains()
    rules_proto_grpc_python_repos()
