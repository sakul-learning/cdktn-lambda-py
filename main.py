#!/usr/bin/env python3
import json
import os

from constructs import Construct
from cdktn import (
    App,
    AssetType,
    Fn,
    TerraformAsset,
    TerraformOutput,
    TerraformProvider,
    TerraformProviderGeneratorMetadata,
    TerraformResource,
    TerraformStack,
    TerraformVariable,
)


class HelloWorldStack(TerraformStack):
    def __init__(self, scope: Construct, stack_id: str):
        super().__init__(scope, stack_id)

        aws = TerraformProvider(
            self,
            "aws",
            terraform_resource_type="aws",
            terraform_provider_source="hashicorp/aws",
            terraform_generator_metadata=TerraformProviderGeneratorMetadata(
                provider_name="aws", provider_version_constraint="~> 6.0"
            ),
        )
        aws.add_override("region", "us-east-1")

        ephemeral_greeting = TerraformVariable(
            self,
            "ephemeral_greeting",
            description="Ephemeral greeting passed through the Lambda environment configuration.",
            type="string",
        )
        # CDKTN has not yet added an `ephemeral` constructor option; emit the OpenTofu argument directly.
        ephemeral_greeting.add_override("ephemeral", True)

        lambda_source = TerraformAsset(
            self,
            "lambda_source",
            path=os.path.join(os.path.dirname(__file__), "lambda_src"),
            type=AssetType.ARCHIVE,
        )

        assume_role_policy = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        )
        role = TerraformResource(
            self,
            "lambda_execution_role",
            terraform_resource_type="aws_iam_role",
            provider=aws,
        )
        role.add_override("name", "cdktn-python-hello-world-role")
        role.add_override("assume_role_policy", assume_role_policy)

        basic_execution = TerraformResource(
            self,
            "lambda_basic_execution",
            terraform_resource_type="aws_iam_role_policy_attachment",
            provider=aws,
        )
        basic_execution.add_override("role", role.get_string_attribute("name"))
        basic_execution.add_override(
            "policy_arn",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        )

        function = TerraformResource(
            self,
            "hello_world",
            terraform_resource_type="aws_lambda_function",
            provider=aws,
            depends_on=[basic_execution],
        )
        function.add_override("function_name", "cdktn-python-hello-world")
        function.add_override("role", role.get_string_attribute("arn"))
        function.add_override("runtime", "python3.12")
        function.add_override("handler", "index.handler")
        function.add_override("filename", lambda_source.path)
        function.add_override("source_code_hash", lambda_source.asset_hash)
        function.add_override(
            "environment",
            [
                {
                    "variables": {
                        "STATIC_MESSAGE": "hello world",
                        "EPHEMERAL_GREETING": Fn.ephemeralasnull(
                            ephemeral_greeting.value
                        ),
                    }
                }
            ],
        )

        TerraformOutput(
            self,
            "lambda_function_name",
            value=function.get_string_attribute("function_name"),
            static_id=True,
        )
        TerraformOutput(
            self,
            "non_ephemeral_environment_variables",
            value={"STATIC_MESSAGE": "hello world"},
            static_id=True,
        )


app = App()
HelloWorldStack(app, "hello-world")
app.synth()
