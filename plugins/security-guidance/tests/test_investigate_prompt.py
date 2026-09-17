import review_api


def test_investigate_prompt_anchors_relative_paths_to_repo_root():
    root = "/tmp/project/worktrees/fix"

    prompt = review_api.build_investigate_prompt(
        ["envs/prod/main.tf"],
        [("envs/prod/main.tf", "+resource \"example\" \"test\" {}")],
        repo_root=root,
    )

    assert f"Repository root (your working directory): {root}" in prompt
    assert "  - envs/prod/main.tf" in prompt
    assert "Report filePath in the repo-relative form" in prompt


def test_investigate_prompt_without_root_is_backwards_compatible():
    prompt = review_api.build_investigate_prompt(
        ["app.py"], [("app.py", "+print('ok')")]
    )

    assert "Repository root" not in prompt
    assert "Changed files" in prompt
