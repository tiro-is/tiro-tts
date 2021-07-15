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
