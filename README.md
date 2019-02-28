# Installer for IOpipe

Applies the IOpipe layers to functions in your
AWS account. Uses credentials as configured
for the AWS CLI.

# Installation

`python setup.py install`

# Basic Usage

## Update deployed Lambda function

`iopipe-install update-function --function-arn <name or arn>`

# Advanced usage

## Update deployed function /w specific layer

`iopipe-install update-function --function-arn <name|arn> --layer-arn <arn>`

## Updating cloudformation (experimental)

### modify a CF yaml file

`iopipe-install cloudformation update-template`

### modify a running CF stack

`iopipe-install cloudformation update-stack`
