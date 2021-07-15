load("@rules_python//python:pip.bzl", "pip_parse")
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
