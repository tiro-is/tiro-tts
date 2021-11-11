load("@pip_deps//:requirements.bzl", "requirement")

# Borrowed from https://github.com/ali5h/rules_pip/blob/9ef4b2ad56ad3dbe6f154d0170e74a45a7bfa27f/defs.bzl#L165
def py_pytest_test(
        name,
        # This argument exists for back-compatibility with earlier versions
        pytest_args = [
            "--ignore=external",
            ".",
            "-p",
            "no:cacheprovider",
        ],
        **kwargs):
    """A macro that runs pytest tests by using a test runner.
    Args:
        name: A unique name for this rule.
        pytest_args: a list of arguments passed to pytest
        **kwargs: are passed to py_test, with srcs and deps attrs modified

    Example:

        load("//tools/py:py_pytest_test.bzl", "py_pytest_test")
        py_pytest_test(
            name = "my_test",
            srcs = ["test.py"],
            deps = [":my_app_lib"]
        )

    """

    if "main" in kwargs:
        fail("if you need to specify main, use py_test directly")

    deps = kwargs.pop("deps", []) + [
        "@//tools/py:pytest_helper",
        requirement("pytest"),
    ]
    srcs = kwargs.pop("srcs", []) + [
        "@//tools/py:pytest_helper",
        requirement("pytest"),
    ]
    args = kwargs.pop("args", []) + pytest_args

    # failsafe, pytest won't work otw.
    for src in srcs:
        if name == src.split("/", 1)[0]:
            fail("rule name (%s) cannot be the same as the" +
                 "directory of the tests (%s)" % (name, src))

    native.py_test(
        name = name,
        srcs = srcs,
        main = "pytest_helper.py",
        deps = deps,
        args = args,
        **kwargs
    )
