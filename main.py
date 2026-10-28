#!/usr/bin/env python3
import json
import os

from constructs import Construct
from cdktn import App, AssetType, Fn, TerraformAsset, TerraformOutput, TerraformStack, TerraformVariable
from cdktn_provider_aws.iam_role import IamRole
from cdktn_provider_aws.iam_role_policy_attachment import IamRolePolicyAttachment
from cdktn_provider_aws.lambda_function import LambdaFunction, LambdaFunctionEnvironment
from cdktn_provider_aws.provider import AwsProvider


class HelloWorldStack(TerraformStack):
    def __init__(self, scope: Construct, stack_id: str):
        super().__init__(scope, stack_id)

        aws = AwsProvider(self, "aws", region="us-east-1")

        ephemeral_greeting = TerraformVariable(
            self,
            "ephemeral_greeting",
            description="Ephemeral greeting passed through the Lambda environment configuration.",
            type="string",
        )
        # CDKTN does not yet expose `ephemeral` as a TerraformVariable constructor option.
        ephemeral_greeting.add_override("ephemeral", True)

        lambda_source = TerraformAsset(
            self,
            "lambda_source",
            path=os.path.join(os.path.dirname(__file__), "lambda_src"),
            type=AssetType.ARCHIVE,
        )

        role = IamRole(
            self,
            "lambda_execution_role",
            name="cdktn-python-hello-world-role",
            assume_role_policy=json.dumps(
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
            ),
            provider=aws,
        )

        basic_execution = IamRolePolicyAttachment(
            self,
            "lambda_basic_execution",
            role=role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            provider=aws,
        )

        function = LambdaFunction(
            self,
            "hello_world",
            function_name="cdktn-python-hello-world",
            role=role.arn,
            runtime="python3.12",
            handler="index.handler",
            filename=lambda_source.path,
            source_code_hash=lambda_source.asset_hash,
            environment=LambdaFunctionEnvironment(
                variables={
                    "STATIC_MESSAGE": "hello world",
                    "EPHEMERAL_GREETING": Fn.ephemeralasnull(ephemeral_greeting.value),
                }
            ),
            depends_on=[basic_execution],
            provider=aws,
        )

        TerraformOutput(
            self,
            "lambda_function_name",
            value=function.function_name,
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
