load("@rules_proto//proto:defs.bzl", "proto_library")
load("@rules_proto_grpc//python:defs.bzl", "python_proto_library")
package(
    default_visibility = ["//visibility:public"],
)

proto_library(
    name = "voice_proto",
    srcs = ["voice.proto"],
)

python_proto_library(
    name = "voice_python_proto",
    protos = [":voice_proto"],
)
