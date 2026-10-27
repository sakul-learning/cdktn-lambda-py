# CDKTN Python Lambda hello world

A minimal [CDK Terrain (CDKTN)](https://cdktn.io/) Python application that synthesizes and deploys an AWS Lambda returning `"hello world"` on a synchronous invocation.

It intentionally demonstrates an OpenTofu-only target and passing an ephemeral Terraform variable through `ephemeralasnull` into Lambda environment configuration. The ephemeral value is not persisted in the deployed Lambda environment or exposed in stack outputs.

## Prerequisites

- Python 3.11+
- Node.js 22.23.4+ (for `cdktn-cli@next`)
- [uv](https://docs.astral.sh/uv/)
- OpenTofu 1.11+ (the project targets the installed 1.12.6 floor)
- AWS credentials/profile that can create Lambda and IAM resources

## Install

```sh
uv venv .venv
uv pip install -r requirements.txt
```

## Test

```sh
.venv/bin/python -m pytest main-test.py
```

## Synthesize

The project has usage telemetry enabled in `cdktf.json` and declares only an OpenTofu target.

```sh
TERRAFORM_BINARY_NAME=tofu \
  npx --yes cdktn-cli@next synth hello-world
```

The stack uses an ephemeral `ephemeral_greeting` variable with `Fn.ephemeralasnull`. OpenTofu requires version 1.11 or newer for that function.

## Deploy

Set the profile and region appropriate for your AWS account. The sample currently uses `us-east-1` and creates a Lambda named `cdktn-python-hello-world`.

```sh
AWS_PROFILE=your-profile \
TERRAFORM_BINARY_NAME=tofu \
  npx --yes cdktn-cli@next deploy hello-world \
  --auto-approve \
  --var 'ephemeral_greeting=transient greeting'
```

## Invoke

```sh
AWS_PROFILE=your-profile \
aws lambda invoke \
  --region us-east-1 \
  --function-name cdktn-python-hello-world \
  --invocation-type RequestResponse \
  --payload '{}' \
  response.json

cat response.json
# "hello world"
```

## Clean up

This project creates billable AWS resources. Destroy them when finished:

```sh
AWS_PROFILE=your-profile \
TERRAFORM_BINARY_NAME=tofu \
  npx --yes cdktn-cli@next destroy hello-world \
  --auto-approve \
  --var 'ephemeral_greeting=transient greeting'
```

## Notes

- The app emits raw Terraform resources through CDKTN core constructs rather than generated AWS provider bindings.
- Local state, synth output, virtual environments, and deploy/invocation response artifacts are intentionally ignored by Git.
