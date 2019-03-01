# Installer for IOpipe

Applies the IOpipe layers to functions in your
AWS account. Uses credentials as configured
for the AWS CLI.

# Installation

On your system CLI:
`pip3 install git+https://github.com/iopipe/iopipe-install.git`

# Configuration

This tool assumes the AWS cli tool is configured correctly. Install and configure the AWS CLI as such:

## Install the AWS CLI
`pip3 install awscli --upgrade --user`

## Run the configuration wizard
`aws configure`

Refer to the [AWS CLI User Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html) for advanced configuration options and support for the aws cli tool.

# Basic Usage

## Update deployed Lambda function

`iopipe-install remote lambda-update --function-arn <name or arn>`

Note that if your Lambda has been deployed by Cloudformation, this will cause stack drift. If drift is a consideraton for you, use the `iopipe-install remote stack-update` command instead.

# Advanced usage

## Update deployed function /w specific layer

`iopipe-install remote lambda-update --function-arn <name|arn> --layer-arn <arn>`

## Updating cloudformation (experimental)

### modify a CF yaml file

`iopipe-install local template-update`

### modify a running CF stack

`iopipe-install remote stack-update`

# Troubleshooting

## Error: `botocore.exceptions.NoRegionError: You must specify a region.`

The AWS cli tool is not configured for a region. You may run `aws configure` or set the environment variable `AWS_DEFAULT_REGION` on the cli.

To set the env var on the cli:

`export AWS_DEFAULT_REGION=us-east-1`

## Error: `botocore.exceptions.NoCredentialsError: Unable to locate credentials`

The AWS cli tool is not configured for an AWS account. You may run `aws configure` to configure your AWS environment.

If you have multiple credential configurations in `$HOME/.aws/credentials`, but none is set as a default, you may specify a profile using `export AWS_PROFILE=<name>`.
