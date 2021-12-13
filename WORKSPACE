workspace(
    name = "com_gitlab_tiro_is_tiro_tts"
)

load("@//:repositories.bzl", "tiro_tts_repositories")

tiro_tts_repositories()

load("@//:workspace1.bzl", "tiro_tts_workspace")

tiro_tts_workspace()

load("@//:workspace2.bzl", "tiro_tts_workspace")

tiro_tts_workspace()


load("@com_adobe_rules_gitops//gitops:deps.bzl", "rules_gitops_dependencies")

rules_gitops_dependencies()

load("@com_adobe_rules_gitops//gitops:repositories.bzl", "rules_gitops_repositories")

rules_gitops_repositories()

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")

http_file(
      name = "sequitur_model",
      urls = ["https://gitlab.com/tiro-is/g2p-service/-/raw/094825ae/is-IS.ipd_clean_slt2018.mdl"],
      sha256 = "b37d4fe5a397955a36b75ac1592560aaf560eedb71c5072531918114a2fa8204",
      downloaded_file_path = "sequitur.mdl"
  )
