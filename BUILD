load("@rules_python//python:defs.bzl", "py_binary")
load("@pip_deps//:requirements.bzl", "all_requirements")

py_binary(
    name = "app",
    main = "src/app.py",
    srcs = glob(["src/**/*.py"]),
    python_version = "PY3",
    deps = all_requirements,
)
