load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:git.bzl", "new_git_repository")

def maybe(repo_rule, name, **kwargs):
    if not native.existing_rule(name):
        repo_rule(name = name, **kwargs)
    else:
        print("Repository {} already declared.".format(name))

def tiro_tts_repositories():
    rules_python()
    rules_proto()
    rules_proto_grpc()
    io_bazel_rules_docker()
    com_adobe_rules_gitops()

def rules_python():
    RULES_PYTHON_VERSION = "0.2.0"
    RULES_PYTHON_SHA256 = "778197e26c5fbeb07ac2a2c5ae405b30f6cb7ad1f5510ea6fdac03bded96cc6f"
    maybe(
        http_archive,
        name = "rules_python",
        sha256 = RULES_PYTHON_SHA256,
        url = "https://github.com/bazelbuild/rules_python/releases/download/{v}/rules_python-{v}.tar.gz".format(v = RULES_PYTHON_VERSION),
    )


#################################################
# rules_docker required to build container images
def io_bazel_rules_docker():
    IO_BAZEL_RULES_DOCKER_VERSION = "0.17.0"
    IO_BAZEL_RULES_DOCKER_SHA256 = "59d5b42ac315e7eadffa944e86e90c2990110a1c8075f1cd145f487e999d22b3"
    maybe(
        http_archive,
        name = "io_bazel_rules_docker",
        sha256 = IO_BAZEL_RULES_DOCKER_SHA256,
        strip_prefix = "rules_docker-{}".format(IO_BAZEL_RULES_DOCKER_VERSION),
        urls = [
            "https://github.com/bazelbuild/rules_docker/releases/download/v{v}/rules_docker-v{v}.tar.gz".format(
                v = IO_BAZEL_RULES_DOCKER_VERSION,
            ),
        ],
    )


def rules_proto():
    RULES_PROTO_VERSION = "af6481970a34554c6942d993e194a9aed7987780"
    RULES_PROTO_SHA256 = "bc12122a5ae4b517fa423ea03a8d82ea6352d5127ea48cb54bc324e8ab78493c"
    maybe(
        http_archive,
        name = "rules_proto",
        sha256 = RULES_PROTO_SHA256,
        strip_prefix = "rules_proto-{}".format(RULES_PROTO_VERSION),
        urls = ["https://github.com/bazelbuild/rules_proto/archive/{}.tar.gz".format(RULES_PROTO_VERSION)],
    )


def rules_proto_grpc():
    RULES_PROTO_GRPC_VERSION = "3.1.1"
    RULES_PROTO_GRPC_SHA256 = "7954abbb6898830cd10ac9714fbcacf092299fda00ed2baf781172f545120419"
    maybe(
        http_archive,
        name = "rules_proto_grpc",
        sha256 = RULES_PROTO_GRPC_SHA256,
        strip_prefix = "rules_proto_grpc-{}".format(RULES_PROTO_GRPC_VERSION),
        urls = ["https://github.com/rules-proto-grpc/rules_proto_grpc/archive/{}.tar.gz".format(RULES_PROTO_GRPC_VERSION)],
    )


########################################
# rules_gitops needed for k8s deployment
def com_adobe_rules_gitops():
    RULES_GITOPS_VERSION = "8d9416a36904c537da550c95dc7211406b431db9"
    RULES_GITOPS_SHA256 = "25601ed932bab631e7004731cf81a40bd00c9a34b87c7de35f6bc905c37ef30d"
    maybe(
        http_archive,
        name = "com_adobe_rules_gitops",
        sha256 = RULES_GITOPS_SHA256,
        strip_prefix = "rules_gitops-{}".format(RULES_GITOPS_VERSION),
        urls = ["https://github.com/adobe/rules_gitops/archive/{}.zip".format(RULES_GITOPS_VERSION)],
    )

# def pytorch(use_local = False):
#     if not use_local:
#         PYTORCH_VERSION = "1.9.0"
#         PYTORCH_SHA256 = "c35adb8b57fff435732f61bbf4004c5fffcd3681cbb9459a5afe6b6147ce8e24"
#         maybe(
#             http_archive,
#             name = "pytorch",
#             strip_prefix = "pytorch-{}".format(PYTORCH_VERSION),
#             urls = ["https://github.com/pytorch/pytorch/archive/v{}.zip".format(PYTORCH_VERSION)],
#             sha256 = PYTORCH_SHA256
#         )
#     else:
#         native.local_repository(
#             name = "pytorch",
#             path = "../pytorch",
#         )


# def pytorch_repositories():
#     BAZEL_SKYLIB_SHA256 = "97e70364e9249702246c0e9444bccdc4b847bed1eb03c5a3ece4f83dfe6abc44"
#     maybe(
#         http_archive,
#         name = "bazel_skylib",
#         urls = [
#             "https://github.com/bazelbuild/bazel-skylib/releases/download/1.0.2/bazel-skylib-1.0.2.tar.gz",
#         ],
#         sha256 = BAZEL_SKYLIB_SHA256,
#     )

#     GOOGLETEST_SHA256 = "720614598ba49dd214d9d0c40b8ac4b1352fff7f2bb387a3f24bf080383828cb"
#     maybe(
#         http_archive,
#         name = "com_google_googletest",
#         strip_prefix = "googletest-cd6b9ae3243985d4dc725abd513a874ab4161f3e",
#         urls = [
#             "https://github.com/google/googletest/archive/cd6b9ae3243985d4dc725abd513a874ab4161f3e.tar.gz",
#         ],
#         sha256 = GOOGLETEST_SHA256,
#     )

#     maybe(
#         http_archive,
#         name = "pybind11_bazel",
#         strip_prefix = "pybind11_bazel-7f397b5d2cc2434bbd651e096548f7b40c128044",
#         urls = ["https://github.com/pybind/pybind11_bazel/archive/7f397b5d2cc2434bbd651e096548f7b40c128044.zip"],
#         sha256 = "e4a9536f49d4a88e3c5a09954de49c4a18d6b1632c457a62d6ec4878c27f1b5b",
#     )

#     PYBIND11_VERSION = "2.6.2"
#     PYBIND11_SHA256 = "8ff2fff22df038f5cd02cea8af56622bc67f5b64534f1b83b9f133b8366acff2"
#     maybe(
#         http_archive,
#         name = "pybind11",
#         strip_prefix = "pybind11-{}".format(PYBIND11_VERSION),
#         urls = ["https://github.com/pybind/pybind11/archive/v{}.tar.gz".format(PYBIND11_VERSION)],
#         sha256 = PYBIND11_SHA256,
#         build_file = "@pybind11_bazel//:pybind11.BUILD",
#     )

#     GLOG_VERSION = "0.4.0"
#     GLOG_SHA256 = "f28359aeba12f30d73d9e4711ef356dc842886968112162bc73002645139c39c"
#     maybe(
#         http_archive,
#         name = "com_github_glog",
#         strip_prefix = "glog-{}".format(GLOG_VERSION),
#         urls = [
#             "https://github.com/google/glog/archive/v{}.tar.gz".format(GLOG_VERSION),
#         ],
#         sha256 = GLOG_SHA256,
#     )

#     maybe(
#         http_archive,
#         name = "com_github_gflags_gflags",
#         strip_prefix = "gflags-2.2.2",
#         urls = [
#             "https://github.com/gflags/gflags/archive/v2.2.2.tar.gz",
#         ],
#         sha256 = "34af2f15cf7367513b352bdcd2493ab14ce43692d2dcd9dfc499492966c64dcf",
#     )

#     GLOO_VERSION = "c22a5cfba94edf8ea4f53a174d38aa0c629d070f"
#     GLOO_SHA256 = "53916c903b33284644e13f642948f868f0fa34e1b902f6875486ca55d1e96233"
#     maybe(
#         http_archive,
#         name = "gloo",
#         strip_prefix = "gloo-{}".format(GLOO_VERSION),
#         urls = [
#             "https://github.com/facebookincubator/gloo/archive/{}.zip".format(GLOO_VERSION),
#         ],
#         sha256 = GLOO_SHA256,
#         build_file = "@pytorch//third_party:gloo.BUILD",
#     )

#     ONNX_VERSION = "1.9.0"
#     ONNX_SHA256 = "7470f5482c9f29a8b5e54fc769c0ac565ec5ff6de7a35bbac7a0907ac01a8c45"
#     maybe(
#         http_archive,
#         name = "onnx",
#         strip_prefix = "onnx-{}".format(ONNX_VERSION),
#         urls = [
#             "https://github.com/onnx/onnx/archive/v{}.zip".format(ONNX_VERSION),
#         ],
#         sha256 = ONNX_SHA256,
#         build_file = "@pytorch//third_party:onnx.BUILD",
#     )

#     FOXI_VERSION = "c278588e34e535f0bb8f00df3880d26928038cad"
#     FOXI_SHA256 = "9b8631b54bd3d69247dd5580cb9ad1b27c7b596d6b3a474888605df4a620fd36"
#     maybe(
#         http_archive,
#         name = "foxi",
#         strip_prefix = "foxi-{}".format(FOXI_VERSION),
#         urls = [
#             "https://github.com/houseroad/foxi/archive/{}.zip".format(FOXI_VERSION),
#         ],
#         sha256 = FOXI_SHA256,
#         build_file = "@pytorch//third_party:foxi.BUILD",
#     )

#     PROTOBUF_VERSION = "3.15.1"
#     PROTOBUF_SHA256 = "5027403b91fea2376e26772bfd9ab323db1fe553c0f5bee502b8928ad1dd3bd2"
#     maybe(
#         http_archive,
#         name = "com_google_protobuf",
#         strip_prefix = "protobuf-{}".format(PROTOBUF_VERSION),
#         urls = [
#             "https://github.com/protocolbuffers/protobuf/archive/v{}.zip".format(PROTOBUF_VERSION),
#         ],
#         sha256 = PROTOBUF_SHA256,
#     )

#     EIGEN_VERSION = "d41dc4dd74acce21fb210e7625d5d135751fa9e5"
#     EIGEN_SHA256 = "d5b6ed3772704ed8cde27133ede0fecdd5bdabf12f4702b0523553d81596e18a"
#     maybe(
#         http_archive,
#         name = "eigen",
#         strip_prefix = "eigen-git-mirror-{}".format(EIGEN_VERSION),
#         urls = [
#             "https://github.com/eigenteam/eigen-git-mirror/archive/{}.zip".format(EIGEN_VERSION)
#         ],
#         sha256 = EIGEN_SHA256,
#         build_file = "@pytorch//third_party:eigen.BUILD",
#     )


#     FBGEMM_VERSION = "ae8ad8fd04eacdcfc5fd979170f0ca08a9e9f0fb"
#     FBGEMM_SHA256 = "b3cd79de326121d6729a94c488c4f20c30953f6545b2e6da7f53d6c4a1b3187e"
#     maybe(
#         http_archive,
#         name = "fbgemm",
#         strip_prefix = "FBGEMM-{}".format(FBGEMM_VERSION),
#         urls = [
#             "https://github.com/pytorch/FBGEMM/archive/{}.zip".format(FBGEMM_VERSION),
#         ],
#         sha256 = FBGEMM_SHA256,
#     )

#     IDEEP_VERSION = "9ca27bbfd88fa1469cbf0467bd6f14cd1738fa40"
#     IDEEP_SHA256 = "9febe8d8a06048731977d8e37008cbc51f5580f0a60c1564f2cc0e6dcac07256"
#     maybe(
#         http_archive,
#         name = "ideep",
#         strip_prefix = "ideep-{}".format(IDEEP_VERSION),
#         urls = [
#             "https://github.com/intel/ideep/archive/{}.zip".format(IDEEP_VERSION),
#         ],
#         sha256 = IDEEP_SHA256,
#         build_file = "@pytorch//third_party:ideep.BUILD",
#     )

#     MKL_DNN_VERSION = "7336ca9f055cf1bfa13efb658fe15dc9b41f0740"
#     MKL_DNN_SHA256 = "5b64339addcfc3586f0b85d3a34d319cd8253970d933f68e50f1b88b62acf39f"
#     maybe(
#         http_archive,
#         name = "mkl_dnn",
#         strip_prefix = "oneDNN-{}".format(MKL_DNN_VERSION),
#         urls = [
#             "https://github.com/oneapi-src/oneDNN/archive/{}.zip".format(MKL_DNN_VERSION),
#         ],
#         sha256 = MKL_DNN_SHA256,
#         build_file = "@pytorch//third_party:mkl-dnn.BUILD",
#     )


#     CPUINFO_VERSION = "5916273f79a21551890fd3d56fc5375a78d1598d"
#     CPUINFO_SHA256 = "2a160c527d3c58085ce260f34f9e2b161adc009b34186a2baf24e74376e89e6d"
#     maybe(
#         http_archive,
#         name = "cpuinfo",
#         strip_prefix = "cpuinfo-{}".format(CPUINFO_VERSION),
#         urls = [
#             "https://github.com/pytorch/cpuinfo/archive/{}.zip".format(CPUINFO_VERSION)
#         ],
#         sha256 = CPUINFO_SHA256,
#         build_file = "@pytorch//third_party:cpuinfo.BUILD",
#     )

#     ASMJIT_VERSION = "8b35b4cffb62ecb58a903bf91cb7537d7a672211"
#     ASMJIT_SHA256 = "3404db651051d48f31d0638c75346284929114e7038ac89353345db595f9e154"
#     maybe(
#         http_archive,
#         name = "asmjit",
#         strip_prefix = "asmjit-{}".format(ASMJIT_VERSION),
#         urls = [
#             "https://github.com/asmjit/asmjit/archive/{}.zip".format(ASMJIT_VERSION),
#         ],
#         sha256 = ASMJIT_SHA256,
#         build_file = "@fbgemm//:third_party/asmjit.BUILD",
#     )

#     SLEEF_VERSION = "e0a003ee838b75d11763aa9c3ef17bf71a725bff"
#     SLEEF_SHA256 = "07d957a5512718ba3df9a2db4562e0e03a4a5b1fbc62cac6cb44f6d7e1792656"
#     maybe(
#         http_archive,
#         name = "sleef",
#         strip_prefix = "sleef-{}".format(SLEEF_VERSION),
#         urls = [
#             "https://github.com/shibatch/sleef/archive/{}.zip".format(SLEEF_VERSION),
#         ],
#         sha256 = SLEEF_SHA256,
#         build_file = "@pytorch//third_party:sleef.BUILD",
#     )

#     FMT_VERSION = "cd4af11efc9c622896a3e4cb599fa28668ca3d05"
#     FMT_SHA256 = "ec792b71c30b871262894fd5cf64b8b0553ef7b7831ab84352db37e46b61b73e"
#     maybe(
#         http_archive,
#         name = "fmt",
#         strip_prefix = "fmt-{}".format(FMT_VERSION),
#         urls = [
#             "https://github.com/fmtlib/fmt/archive/{}.zip".format(FMT_VERSION),
#         ],
#         sha256 = FMT_SHA256,
#         build_file = "@pytorch//third_party:fmt.BUILD",
#     )

#     # load("@pytorch//tools/rules:workspace.bzl", "new_patched_local_repository")
#     # # new_patched_local_repository( ???
#     TBB_VERSION = "a51a90bc609bb73db8ea13841b5cf7aa4344d4a9"
#     TBB_SHA256 = "a2e2e6537820fe7864eb95ca3d0c4e54c0af59af1b49297c2fcff55a1ffe5bca"
#     maybe(
#         http_archive,
#         name = "tbb",
#         strip_prefix = "oneTBB-{}".format(TBB_VERSION),
#         urls = [
#             "https://github.com/oneapi-src/oneTBB/archive/{}.zip".format(TBB_VERSION)
#         ],
#         sha256 = TBB_SHA256,
#         patches = [
#             "@pytorch//third_party:tbb.patch",
#         ],
#         patch_args = ["-p1"],
#         build_file = "@pytorch//third_party:tbb.BUILD",
#     )

#     # We need to use new_git_repository instead of http_archive since the build
#     # file uses the submodules
#     TENSORPIPE_VERSION = "c0e7623adb05f36311c7cde6dac8fc4c290419d9"
#     maybe(
#         new_git_repository,
#         name = "tensorpipe",
#         remote = "https://github.com/pytorch/tensorpipe",
#         commit = TENSORPIPE_VERSION,
#         shallow_since = "1623752785 -0700",
#         init_submodules = True,
#         build_file = "@pytorch//third_party:tensorpipe.BUILD",
#     )

#     maybe(
#         http_archive,
#         name = "mkl",
#         build_file = "@pytorch//third_party:mkl.BUILD",
#         strip_prefix = "lib",
#         sha256 = "59154b30dd74561e90d547f9a3af26c75b6f4546210888f09c9d4db8f4bf9d4c",
#         urls = [
#             "https://anaconda.org/anaconda/mkl/2020.0/download/linux-64/mkl-2020.0-166.tar.bz2",
#         ],
#     )

#     maybe(
#         http_archive,
#         name = "mkl_headers",
#         build_file = "@pytorch//third_party:mkl_headers.BUILD",
#         sha256 = "2af3494a4bebe5ddccfdc43bacc80fcd78d14c1954b81d2c8e3d73b55527af90",
#         urls = [
#             "https://anaconda.org/anaconda/mkl-include/2020.0/download/linux-64/mkl-include-2020.0-166.tar.bz2",
#         ],
#     )

#     # Already loaded, should be a "maybe" (everything should be...)
#     # http_archive(
#     #     name = "rules_python",
#     #     url = "https://github.com/bazelbuild/rules_python/releases/download/0.0.1/rules_python-0.0.1.tar.gz",
#     #     sha256 = "aa96a691d3a8177f3215b14b0edc9641787abaaa30363a080165d06ab65e1161",
#     # )
#     # load("@rules_python//python:repositories.bzl", "py_repositories")

#     # py_repositories()

# def numpy():
#     NUMPY_VERSION = "1.19.0"    # NOTE: This has to be kept in sync with //:requirements.bazel.txt
#     NUMPY_SHA256 = "76766cc80d6128750075378d3bb7812cf146415bd29b588616f72c943c00d598"
#     maybe(
#         http_archive,
#         name = "numpy",
#         urls = [
#             "https://github.com/numpy/numpy/releases/download/v{v}/numpy-{v}.zip".format(v = NUMPY_VERSION)
#         ],
#         strip_prefix = "numpy-{}".format(NUMPY_VERSION),
#         sha256 = NUMPY_SHA256,
#         build_file_content = """
# cc_library(
#     name = "headers",
#     hdrs = glob(["numpy/core/include/**/*.h"]),
#     includes = ["numpy/core/include"],
#     visibility = ["//visibility:public"],
# )""",
#     )
