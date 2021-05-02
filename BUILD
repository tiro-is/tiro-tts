load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@io_bazel_rules_docker//python:image.bzl", "py_layer")
load("@io_bazel_rules_docker//python3:image.bzl", "py3_image")
load("@pip_deps//:requirements.bzl", "all_requirements")
load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_image",
)

py_library(
    name = "app_lib",
    srcs = glob(["src/**/*.py"], exclude=["src/app.py"]),
    data = glob(["src/templates/*.dhtml"]),
    srcs_version = "PY3",
    deps = all_requirements,
)

py_binary(
    name = "app",
    srcs = ["src/app.py"],
    python_version = "PY3",
    deps = [":app_lib"],
)

container_image(
    name = "py3_8_image",
    symlinks = {
        "/usr/bin/python": "/usr/local/bin/python",
        "/usr/bin/python3": "/usr/local/bin/python",
    },
    base = "@py3_8_image_base//image",
)

py_layer(
    name = "app_deps_image_layer",
    deps = all_requirements,
)

py3_image(
    name = "app_image",
    main = "src/app.py",
    srcs = ["src/app.py"],
    layers = [
        ":app_deps_image_layer",
        ":app_lib"
    ],
    base = ":py3_8_image",
)
