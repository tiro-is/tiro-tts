load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def python_interpreter(
        name = "python_interpreter",
        py_version = "3.8.3",
        sha256 = "dfab5ec723c218082fe3d5d7ae17ecbdebffa9a1aea4d64aa3a2ecdd2e795864",
):
    BUILD_DIR = '/tmp/bazel-python-{0}'.format(py_version)

    # Special logic for building python interpreter with OpenSSL from homebrew.
    # See https://devguide.python.org/setup/#macos-and-os-x
    _py_configure = """
    if [[ "$OSTYPE" == "darwin"* ]]; then
        cd {0} && ./configure --prefix={0}/bazel_install --with-openssl=$(brew --prefix openssl)
    else
        cd {0} && ./configure --prefix={0}/bazel_install
    fi
    """.format(BUILD_DIR)

    # Produce deterministic binary by using a fixed build timestamp and
    # running `ar` in deterministic mode. See #7
    #
    # The 'D' modifier is known to be not available on macos. For linux
    # distributions, we check for its existence. Note that it should be the default
    # on most distributions since binutils is commonly compiled with
    # --enable-deterministic-archives. See #9
    _ar_flags = """
    ar 2>&1 >/dev/null | grep '\\[D\\]'
    if [ "$?" -eq "0" ]; then
      cd {0} && echo -n 'rvD' > arflags.f527268b.txt
    else
      cd {0} && echo -n 'rv' > arflags.f527268b.txt
    fi
    """.format(BUILD_DIR)

    http_archive(
        name = name,
        urls = [
            "https://www.python.org/ftp/python/{0}/Python-{0}.tar.xz".format(py_version),
        ],
        sha256 = sha256,
        strip_prefix = "Python-{0}".format(py_version),
        patch_cmds = [
            # Create a build directory outside of bazel so we get consistent path in
            # the generated files. See #8
            "mkdir -p {0}".format(BUILD_DIR),
            "cp -r * {0}".format(BUILD_DIR),
            # Build python.
            _py_configure,
            _ar_flags,
            "cd {0} && SOURCE_DATE_EPOCH=0 make -j $(nproc) ARFLAGS=$(cat arflags.f527268b.txt)".format(BUILD_DIR),
            "cd {0} && make install".format(BUILD_DIR),
            # Copy the contents of the build directory back into bazel.
            "rm -rf * && mv {0}/* .".format(BUILD_DIR),
            "ln -s bazel_install/bin/python3 python_bin",
        ],
        build_file_content = """
exports_files(["python_bin"])
filegroup(
    name = "files",
    srcs = glob(["bazel_install/**"], exclude = ["**/* *"]),
    visibility = ["//visibility:public"],
)

cc_library(
   name = "python_headers",
   hdrs = glob(["bazel_install/include/python3.8/**/*.h"]),
   strip_include_prefix = "bazel_install/include/python3.8",
   visibility = ["//visibility:public"],
)
""",
    )
