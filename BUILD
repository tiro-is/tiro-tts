load("@rules_python//python:defs.bzl", "py_binary", "py_library") # "py_test"
load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("@io_bazel_rules_docker//python:image.bzl", "py_layer")
load("@io_bazel_rules_docker//python3:image.bzl", "py3_image")
load(
    "@io_bazel_rules_docker//docker/package_managers:download_pkgs.bzl",
    "download_pkgs"
)
load(
    "@io_bazel_rules_docker//docker/package_managers:install_pkgs.bzl",
    "install_pkgs"
)
load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_image",
)
load("//tools/py:py_repl.bzl", "py_repl2")
load("//tools/py:py_pytest_test.bzl", "py_pytest_test")

# Use bazel run //:pip_compile.update to update requirements.bazel.txt
compile_pip_requirements(
    name = "pip_compile",
    requirements_in = "requirements.bazel.in",
    requirements_txt = "requirements.bazel.txt",
    extra_args = ["--allow-unsafe"],  # for setuptools
)

py_library(
    name = "melgan",
    srcs = glob(["src/lib/fastspeech/melgan/**/*.py"]),
    imports = ["src/lib/fastspeech/melgan"],
    srcs_version = "PY3",
    deps = [
        requirement("torch"),
        requirement("pyyaml"),
        requirement("numpy"),
    ],
)

# Convert PyTorch MelGAN model to TorchScript
py_binary(
    name = "melgan_convert",
    srcs = ["src/scripts/melgan_convert.py"],
    python_version = "PY3",
    deps = [":melgan"],
)

# Preprocess WAV files, i.e. convert to mel. Necessary for :melgan_convert.
py_binary(
    name = "melgan_preprocess",
    srcs = ["src/lib/fastspeech/melgan/preprocess.py"],
    main = "src/lib/fastspeech/melgan/preprocess.py",
    deps = [
        ":melgan",
        requirement("librosa"),
        requirement("tqdm"),
    ],
)

py_library(
    name = "fastspeech",
    srcs = glob(["src/lib/fastspeech/**/*.py"], exclude=["src/lib/fastspeech/melgan"]),
    imports = ["src/lib/fastspeech"],
    srcs_version = "PY3",
    deps = [
        requirement("torch"),
        requirement("pyyaml"),
        requirement("numpy"),
        requirement("tgt"),
        requirement("scipy"),
        requirement("numba"),
        requirement("inflect"),
        requirement("unidecode"),
        ":melgan",
    ],
)

# Convert PyTorch Fastspeech2 model to TorchScript
py_binary(
    name = "fastspeech_convert",
    srcs = ["src/scripts/fastspeech_convert.py"],
    python_version = "PY3",
    deps = [
        requirement("torch"),
        ":fastspeech",
        ":frontend"
    ],
)

py_library(
    name = "auth",
    srcs = glob(["src/auth/**/*.py"], exclude=["**/tests"]),
    srcs_version = "PY3",
    deps = [
        requirement("flask"),
    ],
)

py_library(
    name = "frontend",
    srcs = glob(["src/frontend/**/*.py"], exclude=["**/tests"]),
    srcs_version = "PY3",
    deps = [
        requirement("sequitur-g2p"),
        requirement("tokenizer"),
        requirement("ice-g2p"),
        "@com_github_grammatek_tts_frontend_api//:tts_frontend_service_python_grpc",
    ],
)

py_library(
    name = "voices",
    srcs = glob(["src/voices/**/*.py"], exclude=["**/tests"]),
    srcs_version = "PY3",
    deps = [
        requirement("boto3"),
        requirement("flask"),    # required for access to current_app.config
        requirement("torch"),    # TODO(rkjaran): select on whether we support cuda
        requirement("espnet"),
        requirement("espnet_model_zoo"),
        requirement("parallel_wavegan"),
        ":frontend",
        "//proto/tiro/tts:voice_python_proto",
    ],
)

py_library(
    name = "main",
    srcs = glob(["src/*.py"], exclude=["*_test.py"]),
    srcs_version = "PY3",
    deps = [
        requirement("flask"),
        requirement("flask-apispec"),
        requirement("flask-cors"),
        requirement("flask-env"),
        requirement("flask-migrate"),
        requirement("flask-sqlalchemy"),
        ":voices",
        ":auth",
    ],
)

py_library(
    name = "app_lib",
    data = glob(["src/templates/*.dhtml"]) + glob(["conf/*.pbtxt"]),
    srcs_version = "PY3",
    deps = [
        ":main",
        ":frontend",
        ":voices",
    ],
)

py_binary(
    name = "main",
    srcs = ["main.py"],
    python_version = "PY3",
    deps = [":app_lib"],
)

py_binary(
    name = "gunicorn_runner",
    srcs = ["src/gunicorn_runner.py"],
    python_version = "PY3",
    deps = [
        ":app_lib",
        requirement("gunicorn"),
    ],
)

py_pytest_test(
    name = "test_frontend",
    srcs = glob(
        ["src/frontend/tests/test_*.py"], 
        exclude=["src/frontend/tests/test_mdl_*.py"],
    ),
    deps = [":app_lib"],
    args = glob(
        ["src/frontend/tests/test_*.py"], 
        exclude=["src/frontend/tests/test_mdl_*.py"],
    ),
    size = "large",
)

py_pytest_test(
    name = "test_frontend_model_dependent",
    srcs = glob(["src/frontend/tests/test_mdl_*.py"]),
    deps = [":app_lib"],
    args = glob(["src/frontend/tests/test_mdl_*.py"]),
    data = ["@test_models//:models"],
    tags = ["needs-models"],
    size = "large",
)

py_pytest_test(
    name = "test_end2end",
    srcs = glob(["src/tests/test_*.py"]),
    deps = [":app_lib"],
    args = glob(["src/tests/test_*.py"]),
    data = [
        "@test_models//:models",
        "src/tests/synthesis_set_test.pbtxt",
    ],
    tags = ["needs-models"],
    size = "large",
)

py_pytest_test(
    name = "test_voices",
    srcs = glob(["src/voices/tests/test_*.py"]),
    deps = [":app_lib"],
    args = glob(["src/voices/tests/test_*.py"]),
    data = ["@test_models//:models"],
    tags = ["needs-models"],
    size = "large",
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


download_pkgs(
    name = "system_pkgs",
    image_tar = "@py3_8_image_base//image",
    packages = [
        "libsndfile1"
    ],
)

install_pkgs(
    name = "system_pkgs_image",
    image_tar = "@py3_8_image_base//image",
    installables_tar = ":system_pkgs.tar",
    installation_cleanup_commands = "rm -rf /var/lib/apt/lists/*",
    output_image_name = "system_pkgs_image",
)

container_image(
    name = "base_image",
    symlinks = {
        "/usr/bin/python": "/usr/local/bin/python",
        "/usr/bin/python3": "/usr/local/bin/python",
    },
    base = ":system_pkgs_image.tar",
)

py_layer(
    name = "external_deps_layer",
    deps = [":app_lib"],
    filter = "@",
)

py3_image(
    name = "app_image",
    main = "src/gunicorn_runner.py",
    srcs = ["src/gunicorn_runner.py"],
    layers = [
        ":external_deps_layer",
        requirement("gunicorn"),
        ":app_lib",
    ],
    base = ":base_image",
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

sh_binary(
    name = "fetch_models",
    srcs = ["fetch_models.sh"],
    visibility = ["//visibility:public"],
)
