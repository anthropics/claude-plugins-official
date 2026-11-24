# Claude Security Plugin for Claude Code in GitHub Actions

## Getting started

This action scans code for security vulnerabilities in two ways. You can use either or both.

| | [Pull request review](#pull-request-reviews) | [Scheduled scan](#scheduled-scans) |
| --- | --- | --- |
| Use it to | Catch flaws before they merge | Find flaws in existing code |
| Scans | Each pull request's changes | The whole repository |
| Result | A review, and later its suggested fixes | A report in the job summary |
| Time | Minutes to tens of minutes, based on PR size | Minutes to hours, based on repository size and model |

**Before you start,** read these points and the [Limits](#limits):

- Use the action only where you trust everyone who can push (see [SECURITY.md](SECURITY.md)). Text in a pull request can steer the scan, and the scan can run the pull request's code. Anyone who can push can also edit the workflow, use its model credential and pass the check.
- By default, a pull request from a fork fails the job. See [External branches](#external-branches).
- On a public repository, a review or job summary can disclose a live vulnerability. If that is a concern, [scan locally](README.md) instead of in CI.
- Scanning in a merge queue, or on push events, is not supported.
- Use GitHub-hosted Linux runners on GitHub.com. GHE.com (data residency) and GitHub Enterprise Server are not supported.

## Prerequisites

The samples below use a Claude API key to authenticate requests. It's recommended that you set up [Workload identity federation](#setup-with-workload-identity-federation) and use that instead, because it keeps no secret in the repository. For [alternative authentication methods](#alternative-authentication-and-providers), such as Google Cloud, Bedrock or Foundry, follow their respective section in place of step 1.

1. **Create a Claude API key** in the [Claude Console](https://platform.claude.com/docs/en/get-api-key). It's recommended that you create the key in a standalone workspace for this job alone, with a monthly spend limit, rather than in the Default Workspace. Scope the key: select the workspace in its form. Unscoped keys aren't limited to one workspace and fail this job (HTTP 400). Save it as the repository secret `ANTHROPIC_API_KEY` (**Settings** → **Secrets and variables** → **Actions**).
2. **If your organization [allows only listed actions](https://docs.github.com/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization#allowing-select-actions-and-reusable-workflows-to-run),** also allow `anthropics/claude-code-action`, `oven-sh/setup-bun` and `actions/upload-artifact`.

## Pull request reviews

Catch flaws while they are cheap to fix. The author sees each finding on the pull request, often with a suggested fix, and you can block the merge on serious ones.

Save this as `.github/workflows/claude-security.yml`:

```yaml
name: Claude Security plugin

on:
  pull_request:
    # Scan when a pull request opens, gets commits, leaves draft or changes its base branch.
    # Keep ready_for_review: drafts pass with no scan, so a draft must be scanned when it is marked ready.
    types: [opened, synchronize, reopened, ready_for_review, edited]
  # With a merge queue, uncomment the next line: the job is skipped there, which counts as passing.
  # merge_group:

permissions:
  actions: read
  contents: read
  pull-requests: write

concurrency:
  group: claude-security-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event.action != 'edited' || github.event.changes.base != null }}

jobs:
  # To block merges, make this job a required status check. First read "Blocking the merge".
  claude-security:
    # Keep this: it skips the merge queue, and Dependabot's runs on branches of your repository. Skipped runs pass.
    if: >-
      github.event_name != 'merge_group'
      && (github.actor != 'dependabot[bot]'
      || github.event.pull_request.head.repo.full_name != github.repository)
    runs-on: ubuntu-24.04 # Keep this: only GitHub-hosted Linux runners work.
    timeout-minutes: 240
    outputs:
      report: ${{ steps.claude-security.outputs.report }}
    steps: &steps
      # Keep this step as it is.
      - uses: actions/checkout@v5
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          fetch-depth: 0
          persist-credentials: false

      - id: claude-security
        uses: anthropics/claude-plugins-official/plugins/claude-security
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # Draft fixes in the second job. "false" leaves them out.
          suggest_patches: later
          # Empty in the first job. The second job passes the first job's report.
          report: ${{ needs.claude-security.outputs.report }}
          # Uncomment an input to use it. "Inputs" lists all options.
          #
          # Which findings fail the job. If it is a required check, they block the merge.
          #   confident-high  CRITICAL or HIGH, of high confidence
          #   high            any CRITICAL or HIGH (the default)
          #   medium          any CRITICAL, HIGH or MEDIUM
          #   any             any finding
          #   never           no finding
          # fail_on: medium
          #
          # change_scan_effort: high  # Search harder, at a higher cost.
          # scan_drafts: "true"       # Also scan draft pull requests.
          # model: opus               # See "Choosing the model".
          # fast_mode: "true"         # Faster scans at a higher price. See "Inputs".

      # Keep this step as it is: without it, "Re-run all jobs" posts the comments again.
      - name: Receipt ${{ steps.claude-security.outputs.receipt }}
        if: always()
        run: "true"

  # Suggested fixes, after the first job has ended. The same steps.
  # To draft fixes in the first job, delete this job, the first job's outputs, and the
  # lines suggest_patches and report with their comments.
  claude-security-fixes:
    needs: claude-security
    if: ${{ !cancelled() && needs.claude-security.outputs.report != '' }}
    runs-on: ubuntu-24.04
    timeout-minutes: 240
    steps: *steps
```

**Try it.** Open a pull request, not a draft, that adds the workflow file. To see a finding fail the check, take code that your product runs and add an obvious flaw, such as a shell command built from a request parameter. A flaw in unused code can go unreported. Keep the flaw out of preview deployments, and remove it before you merge.

Each scan posts one comment review, never an approval or a request for changes, and uploads a small artifact as its receipt. With `suggest_patches: later`, a second review brings the suggested fixes later (about 9 to 13 minutes after the first review, on a small pull request), with a receipt of its own. The line under the review's heading says whether the check passes, and why. AI agents write each suggested fix: review it before you commit it.

### Blocking the merge

A failed job blocks the merge only if it is a required status check. In the sample, that is the first job, `claude-security`. The job fails unless the verdict is `pass`, or the run passes without one (`skipped`). The sample above lists the values of `fail_on`.

- AI agents set each severity and confidence, and both can change between runs. `fail_on: medium` catches more flaws, and blocks more merges. `confident-high` blocks fewer, and passes a real CRITICAL or HIGH finding of medium or low confidence.
- A finding that an earlier run commented can still count, at its earlier severity, in a run that neither reports it again nor finds it fixed. That ends when the commented lines change and their code leaves the diff.
- An unverified report, or a scan that lost agents, fails the job under every value but `never`. A scan that fails, runs outside auto mode, or reports less than the job's `scan_effort`, fails it under `never` too. So does one that leaves no complete report, unless the pull request changes no files.
- A scan of a sparse checkout, or one that skipped a top-level folder, can still pass.
- Flaws that the review's agents judge older than the pull request do not fail the job by themselves.

**A required check can turn green on a commit whose scan failed**, for example by a manual run, a re-run, or another pull request with the same head. So:

- Keep `schedule:` and `workflow_dispatch:` in a [second workflow](#scheduled-scans), whose job has another name.
- After a change of base branch, do not re-run an older run.
- Do not skip the job for external branches: a skipped job counts as passing.
- Run one copy of the job on pull requests.
- Do not build a step's name from a pull request's text.
- After a force-push of the base branch, or a change of base with `GITHUB_TOKEN`, push a commit.

### External branches

By default, the job fails for a pull request whose branch is in another repository, such as a fork. Its author needs no push rights, yet could steer the scan to run the branch's code and spend your model credential.

`dangerously_scan_external_branches: true` lets the action go on for every such branch. We do not encourage it. Use it only if a person with write access trusts the submitter. Better: that person reads the change, and opens a pull request from a branch of your repository.

- Leave GitHub's [settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository) "Send write tokens to workflows from pull requests" and "Send secrets to workflows from pull requests" off.
- Your own steps before the action run for an external branch too. Give each install or sign-in step this condition:

```yaml
        if: github.event.pull_request.head.repo.full_name == github.repository || !github.event.pull_request
```

## Scheduled scans

A pull request review looks for flaws in the change. A scheduled scan looks at the whole repository, so it can also find flaws in code that merged before you added the action, or that a review missed.

Save this as a second file, `.github/workflows/claude-security-scheduled.yml`:

```yaml
name: Claude Security plugin (scheduled)

on:
  schedule:
    - cron: "23 4 * * 1" # Mondays at 04:23 UTC, on the default branch. Pick your own day and time.
  workflow_dispatch: # A manual run, on a branch that you choose.

permissions:
  contents: read

jobs:
  # Keep this name different from the pull request job's. See "Blocking the merge".
  claude-security-scheduled:
    runs-on: ubuntu-24.04 # Keep this: only GitHub-hosted Linux runners work.
    timeout-minutes: 360
    steps:
      # Keep this step as it is.
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
          persist-credentials: false

      - uses: anthropics/claude-plugins-official/plugins/claude-security
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # scan_effort: low                       # low, medium (the default) or high.
          model: opus                              # See "Choosing the model".
          # scheduled_fail_on: never               # Do not fail on findings. See "Inputs".
          # allowed_bots: github-merge-queue[bot]  # See "Scheduled scans".
```

**Try it.** Merge the file, then start the workflow from the **Actions** tab. A whole-repository scan can take hours and cost much more than a review, even on a small repository. It can also outrun the job's time limit, and then leaves no report. Fable, the default model, costs several times as much as Opus here, so this sample uses Opus. Check the first run's time and cost. To cut both, lower `scan_effort` or change `model`.

- The report is in the job summary, with no suggested fixes. If a finding is a hard-coded credential, the summary gives only each finding's place, severity and CWE.
- The scan can set aside folders with no product code, such as tests. The report's Coverage section names them.
- GitHub usually runs a schedule as whoever last changed its `cron` line. If that is an app, such as a merge queue, the job fails unless `allowed_bots` names it.
- To track findings as alerts, add [code scanning](#code-scanning).

## Alternative authentication and providers

Each method changes a few lines of your workflow files. For example, with Bedrock:

```diff
 permissions:
   contents: read
+  id-token: write

       - uses: actions/checkout@v5
         # ...

+      - uses: aws-actions/configure-aws-credentials@v4
+        # ...

       - uses: anthropics/claude-plugins-official/plugins/claude-security
         with:
-          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
+          use_bedrock: "true"
+          # ...
```

Each section below has the full lines to copy. Keep the action's other inputs. To check the provider after a scan, run `gh run view RUN_ID --log | grep -oE 'ALLOWED: [a-z0-9.-]+:[0-9]+'`. It prints the one host that model requests can reach.

### OIDC subject and IDs

Federation and the cloud providers need these values. The commands print `<subject>`, then `<owner-id>` and `<repo-id>`:

```bash
gh api repos/OWNER/REPO/actions/oidc/customization/sub --jq .sub_claim_prefix
gh api repos/OWNER/REPO --jq '.owner.id, .id'
```

`<subject>` is `repo:<owner>@<owner-id>/<repo>@<repo-id>`, or `repo:<owner>/<repo>` for an older repository without [immutable subject claims](https://docs.github.com/en/actions/reference/security/oidc#immutable-subject-claims). A rename or a transfer can change the form, and the wrong form fails the sign-in. This page assumes GitHub's default subject template.

Bedrock and Foundry match **full subjects**: `<subject>:pull_request`, and `<subject>:ref:refs/heads/<branch>` for each branch of a scheduled or manual scan.

### Setup with workload identity federation

<details>
<summary>Show the steps</summary>

**Set it up** as an organization admin, in the Claude Console ([full guide](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions)), with your [OIDC subject and IDs](#oidc-subject-and-ids).

1. It's recommended that you create a standalone workspace for this job alone, with a monthly spend limit, rather than sharing the Default Workspace. Decide on a workspace, then open **Settings** → **Workload identity** → **Connect workload**.
2. **Issuer:** choose **New provider** → **GitHub Actions**. If that tile reads **Registered**, choose **Registered issuer** instead.
3. **Rule:** make one rule for each repository.
   - **GitHub organization:** the owner. **Organization numeric ID:** `<owner-id>`.
   - **Repository:** the name alone. Never leave it blank: that matches every repository of the owner.
   - **Branch / ref:** empty.
   - **Allowed events:** **Any event**. The default, **Only push**, refuses pull requests.
   - **Advanced match options** → **Subject pattern:** set `<subject>:*`. The Console fills in the form without IDs: replace it if yours differs.
   - **Enable in workspaces:** only that workspace.
   - Leave the token lifetime at 10 minutes, and the scope as it is.
4. **Target:** choose **New account**, and name the service account.
5. **Test:** copy the organization, rule, service account and workspace IDs, and choose **Done**. Skip the workflow that it shows.
6. Save the IDs as the four repository variables below.

**Update the workflow.** Add `id-token: write` to `permissions`. Do not also pass `anthropic_api_key`: a key takes precedence over federation.

```yaml
      - id: claude-security
        uses: anthropics/claude-plugins-official/plugins/claude-security
        with:
          anthropic_organization_id: ${{ vars.ANTHROPIC_ORGANIZATION_ID }}
          anthropic_federation_rule_id: ${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}
          anthropic_service_account_id: ${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}
          anthropic_workspace_id: ${{ vars.ANTHROPIC_WORKSPACE_ID }}
```

</details>

### Setup with a cloud provider

For console details, use "Configure cloud authentication" in the [cloud providers guide](https://code.claude.com/docs/en/github-actions-cloud-providers), and skip its GitHub App. Where that page differs, follow this one.

The account must serve three models:

- Claude Fable 5.2 runs the scan, unless `model` names another model. To start without it, set `model:` to the value of `default_opus_model`.
- Claude Sonnet 5 (`default_sonnet_model`) runs supporting steps and auto mode's [classifier](https://code.claude.com/docs/en/permission-modes#default-classifier-model), which checks the scan's commands. The classifier needs Sonnet 5 even if that input names a 5.5 model.
- Claude Opus 4.8 (`default_opus_model`) is the fallback in a Fable scan, for the classifier too. Without that input, the classifier falls back to an Opus model. Behind a model gateway, set `default_opus_model` to the gateway's name for Claude Opus 4.8.

#### Google Cloud's Agent Platform

<details>
<summary>Show the steps</summary>

**Set it up.**

1. Decide which project you'd like to use. The job's role can call every model and endpoint in it. Enable these `.googleapis.com` APIs: `iam`, `cloudresourcemanager`, `iamcredentials`, `sts`, and `aiplatform`. In Model Garden, enable the three models in your `vertex_region`. [Regional endpoints](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed#global-multi-region-and-regional-endpoints) serve only older models. For Fable, first accept Google's Advanced AI Safety Addendum, and enable prompt-response sharing with Anthropic.
2. Make sure that the organization policy constraint `constraints/vertexai.allowedPartnerModelFeatures` does not allow `web_search` for the project.
3. Create a Workload Identity Pool with a GitHub provider. Issuer: `https://token.actions.githubusercontent.com`. Map `google.subject=assertion.sub,attribute.repository_id=assertion.repository_id`. In its attribute condition, test `assertion.repository_id` against [`<repo-id>`](#oidc-subject-and-ids).
4. Create a service account. On it, grant `roles/iam.workloadIdentityUser` to `principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/attribute.repository_id/<repo-id>`.
5. Give the service account the role below, not the guide's `roles/aiplatform.user`, which can also run code in your project.
6. Create the variables `GCP_WORKLOAD_IDENTITY_PROVIDER` (the provider's full resource name) and `GCP_SERVICE_ACCOUNT` (the account's email address).

```bash
gcloud iam roles create claudeSecurityPredict --project=PROJECT_ID \
  --title="Claude Security plugin" --permissions=aiplatform.endpoints.predict --stage=GA
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="projects/PROJECT_ID/roles/claudeSecurityPredict"
```

**Update the workflow.** Add `id-token: write` to `permissions`.

```yaml
      - uses: google-github-actions/auth@v2
        if: github.event.pull_request.head.repo.full_name == github.repository || !github.event.pull_request
        with:
          workload_identity_provider: ${{ vars.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ vars.GCP_SERVICE_ACCOUNT }}

      - id: claude-security
        uses: anthropics/claude-plugins-official/plugins/claude-security
        with:
          use_vertex: "true"
          vertex_project_id: your-project-id
          vertex_region: global
          default_sonnet_model: claude-sonnet-5
          default_opus_model: claude-opus-4-8
```

</details>

#### Amazon Bedrock

<details>
<summary>Show the steps</summary>

**Set it up.**

1. As an AWS admin, submit Anthropic's use case form, and accept each model's offer (`aws bedrock create-foundation-model-agreement`). The job's role cannot. For Fable, first set the data retention mode that AWS's model card names.
2. If the account has no IAM OIDC identity provider for GitHub, create one. Provider URL: `https://token.actions.githubusercontent.com`. Audience: `sts.amazonaws.com`.
3. Create an IAM role for this job alone that trusts that provider. In its trust policy, require these three conditions with `StringEquals`. Each key starts with `token.actions.githubusercontent.com:`.
   - `aud`: `sts.amazonaws.com`.
   - `repository_id`: `<repo-id>`.
   - `sub`: each [full subject](#oidc-subject-and-ids).
4. Give the role only the policy below.
5. Set the role's maximum session duration to 4 hours, or to 6 hours if you use the scheduled sample. A job's temporary AWS credentials stay valid for `role-duration-seconds`, even if the job ends sooner, and a longer scan fails. If you change `timeout-minutes`, match `role-duration-seconds` to it, and keep this maximum at least as long.
6. Create the variable `AWS_ROLE_TO_ASSUME` with the role's ARN.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": [
        "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-*",
        "arn:aws:bedrock:*:*:inference-profile/global.anthropic.claude-*",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
        "arn:aws:bedrock:::foundation-model/anthropic.claude-*"
      ]
    }
  ]
}
```

**Update the workflow.** Add `id-token: write` to `permissions`.

```yaml
      - uses: aws-actions/configure-aws-credentials@v4
        if: github.event.pull_request.head.repo.full_name == github.repository || !github.event.pull_request
        with:
          role-to-assume: ${{ vars.AWS_ROLE_TO_ASSUME }}
          aws-region: us-west-2
          # In the scheduled workflow: 21600.
          role-duration-seconds: 14400

      - id: claude-security
        uses: anthropics/claude-plugins-official/plugins/claude-security
        with:
          use_bedrock: "true"
          default_sonnet_model: us.anthropic.claude-sonnet-5
          default_opus_model: us.anthropic.claude-opus-4-8
```

- For another region, change `aws-region`. If its [prefix](https://code.claude.com/docs/en/amazon-bedrock#cross-region-inference-profile-prefixes) is not `us.`, change the prefix in both model lines and in the policy.
- For application inference profiles, put each ARN in the policy and in its model's line, and set `model: opus`: an ARN in `model` alone is refused.
- A Bedrock API key with an expiry can replace the sign-in step: set `AWS_BEARER_TOKEN_BEDROCK` in `env:` from a secret, and set `aws_region`.

</details>

#### Microsoft Foundry

<details>
<summary>Show the steps</summary>

**Set it up.**

1. Decide which [Foundry resource](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry#provisioning) and project you'd like to use, in a region that serves Claude, such as East US 2. The job's role can call every model in that resource. If nothing else uses its API keys, turn them off (`disableLocalAuth`). Check its name and region: the portal can pick its own.
2. Deploy the three models under their own names: `claude-fable-5-2`, `claude-sonnet-5`, and `claude-opus-4-8`. Accept the Marketplace terms at the first deployment.
3. Create a Microsoft Entra application for this job alone. With the CLI, also create its service principal (`az ad sp create`). Add one federated credential for each [full subject](#oidc-subject-and-ids). Issuer: `https://token.actions.githubusercontent.com`. Audience: `api://AzureADTokenExchange`.
4. Create the custom role below (`az role definition create`), and assign it to the application on the Foundry resource alone. Do not use the guide's Foundry User, which can also read the resource's API keys.
5. Create the variables `AZURE_CLIENT_ID` and `AZURE_TENANT_ID` with the application's IDs.

```json
{
  "Name": "Claude Security plugin scan",
  "Actions": [],
  "DataActions": ["Microsoft.CognitiveServices/accounts/AIServices/providers/action"],
  "AssignableScopes": ["/subscriptions/SUBSCRIPTION_ID/resourceGroups/RESOURCE_GROUP"]
}
```

**Update the workflow.** Add `id-token: write` to `permissions`.

```yaml
      - uses: azure/login@v2
        if: github.event.pull_request.head.repo.full_name == github.repository || !github.event.pull_request
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          allow-no-subscriptions: true

      - id: claude-security
        uses: anthropics/claude-plugins-official/plugins/claude-security
        with:
          use_foundry: "true"
          foundry_resource: your-resource-name
          default_sonnet_model: claude-sonnet-5
          default_opus_model: claude-opus-4-8
```

</details>

### Setup with a model gateway

<details>
<summary>Show the steps</summary>

**Set it up.** Create one secret, such as `MODEL_GATEWAY_KEY`, with a key that can make model requests and nothing more.

- The gateway must meet Claude Code's [requirements](https://code.claude.com/docs/en/llm-gateway-rollout#gateway-requirements). It must route the models under [Setup with a cloud provider](#setup-with-a-cloud-provider) and the [aliases](https://code.claude.com/docs/en/model-config#model-aliases).
- Use a host name whose DNS your organization controls: the action's relay reaches each of its IPv4 addresses, private ones too. The key goes only as a bearer token.

**Update the workflow.**

```yaml
      - id: claude-security
        uses: anthropics/claude-plugins-official/plugins/claude-security
        with:
          model_base_url: https://{your-gateway}
          model_auth_token: ${{ secrets.MODEL_GATEWAY_KEY }}
```

For another protocol, add `use_bedrock: "true"` and `aws_region`; or `use_vertex: "true"`, `vertex_project_id` and `vertex_region`; or `use_foundry: "true"`. For Google Cloud, end the URL in `/v1`.

</details>

## Advanced

### Choosing the model

Fable is the default, and we recommend it. Sonnet 5.5 or Opus 5.5 also performs well on smaller pull-request scans and may be a worthwhile tradeoff for development speed. We recommend a final scan on Fable before merging whenever possible.

Set `model` to an alias or a full name; on a cloud, give the full name, or an alias whose full name `default_opus_model` or `default_sonnet_model` gives. Choose a model that [supports auto mode](https://code.claude.com/docs/en/permission-modes#eliminate-prompts-with-auto-mode). Build `model` only from text that people with write access choose. The action does not read `ANTHROPIC_MODEL` from `env:`.

### Letting the job run your tests

Agents that check a fix may run your tests in the sandbox, where downloads and services fail and the home folder is hidden.

- Install what the tests need in an earlier step, with the condition under [External branches](#external-branches). Change no tracked file there.
- With the sample's two jobs, only the second runs tests. There, use the condition `(github.event.pull_request.head.repo.full_name == github.repository || !github.event.pull_request) && github.job != 'claude-security'`.
- If auto mode's classifier denies a test command, add a rule, such as `claude_args: --allowedTools "Bash(npm test:*)"`. Claude Code drops some, such as `Bash(npm run:*)`.
- Name more job variables for the tests, such as `NODE_ENV`, in `scan_variables`. Name no secret.

### Code scanning

To record findings as [code scanning](https://docs.github.com/en/code-security/code-scanning) alerts, add `security-events: write` to `permissions` (and `actions: read` in the scheduled workflow), and these two steps after the action step. An alert can close because a later scan did not report it again. So after some scans whose own records show a gap, these steps get no report. The job's log says why.

```yaml
      - name: Find the report
        id: claude-security-report
        # Runs even when the job fails on findings.
        if: ${{ !cancelled() }}
        run: |
          REPORT="$(cat "$RUNNER_TEMP/claude-security-report-dir" 2>/dev/null || true)"
          echo "sarif=${REPORT:+$REPORT/CLAUDE-SECURITY-RESULTS.sarif}" >> "$GITHUB_OUTPUT"

      - uses: github/codeql-action/upload-sarif@v4
        if: ${{ !cancelled() && steps.claude-security-report.outputs.sarif != '' }}
        with:
          sarif_file: ${{ steps.claude-security-report.outputs.sarif }}
```

### Inputs

| Input | What it does | Default |
| --- | --- | --- |
| `anthropic_organization_id` | Federation: organization ID. | none |
| `anthropic_federation_rule_id` | Federation: rule ID. | none |
| `anthropic_service_account_id` | Federation: service account ID. | none |
| `anthropic_workspace_id` | Federation: workspace ID. | none |
| `anthropic_api_key` | A Claude API key. The action takes no Claude subscription token. | none |
| `use_bedrock` | `true` uses Amazon Bedrock. | `false` |
| `aws_region` | With `use_bedrock`: the region. | the job's `AWS_REGION` |
| `use_vertex` | `true` uses Google Cloud's Agent Platform. | `false` |
| `vertex_project_id` | With `use_vertex`: the project ID. | none |
| `vertex_region` | With `use_vertex`: the region, such as `global`. | none |
| `use_foundry` | `true` uses Microsoft Foundry. | `false` |
| `foundry_resource` | With `use_foundry`: the resource's name. | none |
| `model_base_url` | The https URL of a model gateway. Without it, a base URL in the job's environment or in a Claude Code settings file can fail the job. | none |
| `model_auth_token` | The gateway's key. A gateway for Google Cloud needs it. With another provider and no key, your provider's credential goes to the gateway. | none |
| `allowed_bots` | The apps and bots whose events may start a scan, comma-separated. The job fails for any other app. Anyone whose text can make such an app push can steer a scan: name only apps you trust, and never `*`. | none |
| `scan_effort` | The scan's tier: `low`, `medium`, or `high`. | `medium` |
| `change_scan_effort` | `low` or `high`. `high` searches pull requests harder, overrides `scan_effort` there, and costs more. | `low` |
| `model` | The scan's model. | `fable` |
| `model_effort` | The lead session's effort: `low`, `medium`, `high`, `xhigh`, or `max`. | `high` |
| `fast_mode` | `true` turns on [fast mode](https://code.claude.com/docs/en/fast-mode): the same model, faster, at about twice the price per token. The provider, the model (such as Fable 5.2 on the Claude API) and your organization's admin must allow it, or the log warns and the scan runs at standard speed. Behind a model gateway, or on a model that has lost fast mode, it can fail the scan. With the sample's two jobs, `true` also runs the second job's session fast. | `false` |
| `default_sonnet_model` | The full model name behind the alias `sonnet`. | none |
| `default_opus_model` | The full model name behind the alias `opus`. | none |
| `claude_args` | Arguments for Claude Code, added after the action's own. | none |
| `scan_variables` | Names of more job variables for the scan, separated by spaces or line breaks. | none |
| `fail_on` | Which findings fail the job: `confident-high`, `high`, `medium`, `any` or `never`. The [pull request sample](#pull-request-reviews) explains them. | `high` |
| `suggest_patches` | `false` leaves out suggested fixes. `later` leaves them to a second job. | `true` |
| `report` | The first job's output `report`. The job then drafts and posts only the fixes. | none |
| `scheduled_fail_on` | As `fail_on`, for scheduled and manual runs. | follows `fail_on` |
| `scan_drafts` | `true` has draft pull requests scanned. If GitHub does not say that the author has write access, a draft goes on to the scan anyway, and the job fails if whoever caused the event has none. Such an author's closed, unmerged pull request fails the job. | `false` |
| `dangerously_scan_external_branches` | `true` lets the job go on for an external branch. | `false` |
| `scan_agents` | How many scan agents may run at once: a whole number from 1 to 256. | `8` |

### Outputs

- `skipped` is `true` on a run that passes without a verdict, and on every run given the input `report`.
- `report` is for the second job, and `receipt` for the step `Receipt`.
- `$RUNNER_TEMP/claude-security-verdict` holds `key=value` lines: `verdict` (`pass` or `fail`), and the counts `findings`, `critical`, `high`, `medium` and `low` of the findings in the verdict. `findings=0` alone does not show a clean scan.
- The report stays on the runner, under `$RUNNER_TEMP/claude-security-out/reports/`. Read its files as data, and run nothing from the `$RUNNER_TEMP/claude-security-*` folders.
- With `suggest_patches: later`, where a finding needs a new fix, an artifact hands the report to the second job, and is kept for one day. Anyone who can read the repository can download it.

### Limits

Rules:

- Pin a release's full commit, never a branch: the action runs with `sudo`. Nothing warns you of a newer release. The [plugin's page](https://code.claude.com/docs/en/claude-security#scan-pull-requests-in-github-actions) gives the latest commit: put it after the `@` in each workflow.
- Keep unrelated steps and jobs in another workflow: the action changes the runner, and trusts earlier runs of its own workflow. Give every `actions/checkout` step `persist-credentials: false`.
- Do not use `pull_request_target`, `uses: ./...` or `services:`, and start no server in the job.
- In `claude_args`, pass no `--settings`, and allow no git command, `Skill` tool or GitHub MCP tool.
- Leave no credential in the checkout, `claude_args` or `model_base_url`. Keep no other secret in a variable whose name begins with `CLAUDE_` or `LC_`.
- The action needs no GitHub App. Install the Claude GitHub App only for another Claude feature: with `id-token: write`, a step outside the scan's sandbox can get that App's token, which can write to the repository.

What to expect:

- The scan runs in a sandbox: no network, no `sudo`, not the job's token. It can spend the model credential but does not hold it. What it reads can leave by a model request or the review.
- A scan loads none of the repository's Claude Code settings, hooks, skills or MCP servers. To keep a deny rule, pass it in `claude_args`, such as `--disallowedTools "Read(./secrets/**)"`. A `Read` rule does not stop every shell command, so keep secrets out of the repository.
- Remote managed settings and policy limits do not reach a scan, and it loads no `CLAUDE.md` file, not even a managed one.
- A review, job summary, code scanning upload or report handed to a second job can show a credential from your code: masking is a model's best effort.
- A clean review is not proof of absence.

## Troubleshooting

Check the run's error annotations, the job summary and the failed step's log first. If those give no reason, upload the session's record, `${{ runner.temp }}/claude-execution-output.json`, as an artifact, in a last step under `if: always()`. Do this, or turn on step debug logging, in a private test repository only. The record can hold a credential from your code: do not print it, and delete it after use.

### If authentication fails

- If the step "Get the Claude API token" fails, read the reason in the Console's [Authentication events tab](https://platform.claude.com/settings/workload-identity-federation?tab=history). No entry after a 401 usually means a wrong rule ID. `match_subject_prefix` means a wrong subject pattern (see [OIDC subject and IDs](#oidc-subject-and-ids)).
- On Foundry, `AADSTS70025` at `azure/login` means the application has no federated credential. That step's log prints the subject that it sent.

### Other problems

| Symptom | What to do |
| --- | --- |
| A short run after a title or description edit | Nothing, if its summary links a review: it repeats that verdict. |
| The warning `The session changed files that later steps trust, so they were restored: .git/config` | Nothing. Each scan shows it. |
| The scan fails within seconds of its start | Check that the account serves the models: on Foundry, that they are deployed in `foundry_resource`. |
| TLS errors from your own certificate authority | With `sudo`, copy its file to `/usr/local/share/ca-certificates/` as a `.crt` file, and run `update-ca-certificates`. |
| The job times out | Raise `timeout-minutes` (at most 360; on [Bedrock](#amazon-bedrock), also `role-duration-seconds` and the role's maximum session duration) or `scan_agents`, lower `scan_effort` or `change_scan_effort`, or set `suggest_patches: false`. |
