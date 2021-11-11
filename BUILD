load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("@io_bazel_rules_docker//python:image.bzl", "py_layer")
load("@io_bazel_rules_docker//python3:image.bzl", "py3_image")
load("@pip_deps//:requirements.bzl", "all_requirements", "requirement")
load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_image",
)
load("//tools/py:py_repl.bzl", "py_repl2")

# Use bazel run //:pip_compile.update to update requirements.bazel.txt
compile_pip_requirements(
    name = "pip_compile",
    requirements_in = "requirements.bazel.in",
    requirements_txt = "requirements.bazel.txt",
    extra_args = ["--allow-unsafe"],  # for setuptools
)

py_library(
    name = "app_lib",
    srcs = glob(["src/**/*.py"]),
    data = glob(["src/templates/*.dhtml"]) + glob(["conf/*.pbtxt"]),
    srcs_version = "PY3",
    deps = all_requirements + [
        "//proto/tiro/tts:voice_python_proto",
        "@com_github_grammatek_tts_frontend_api//:tts_frontend_service_python_grpc",
    ],
)

py_binary(
    name = "app",
    srcs = ["src/app.py"],
    python_version = "PY3",
    deps = [":app_lib"],
)

py_binary(
    name = "gunicorn_runner",
    srcs = ["src/gunicorn_runner.py"],
    python_version = "PY3",
    deps = [
        ":app_lib",
        # Technically this is included in ``all_requirements``, but let's be
        # explicit
        requirement("gunicorn"),
    ],
)

# Defines a runnable REPL with the same environment as :app
# Something like:
#   echo "import os; print(os.environ['PYTHONPATH'])" | bazel run //:repl
# will return the PYTHONPATH to allow for integration with most
# editors/tools/IDEs
py_repl2(
    name = "repl",
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
    main = "src/gunicorn_runner.py",
    srcs = ["src/gunicorn_runner.py"],
    layers = [
        ":app_deps_image_layer",
        requirement("gunicorn"),
        ":app_lib",
    ],
    base = ":py3_8_image",
)

container_image(
    name = "tiro-tts_image",
    base = ":app_image",
    labels = {
        "maintainer": "Tiro <tiro@tiro.is>",
        "description": "Runtime image for the Tiro TTS service",
    },
    tars = [
        "@ffmpeg//:cli_pkg",
    ],
    ports = ["8000"],
    volumes = ["/models"],
    cmd = [
        "--bind", "0.0.0.0:8000",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "--access-logformat", "%(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"",
        "app:app",
    ],
    visibility = ["//visibility:public"],
)
