#!/usr/bin/env python3
from . import update

import boto3
import botocore
import click

@click.group()
def cli():
    None

@click.group()
def local():
    None

@click.group()
def remote():
    None

#@click.group()
#def sam():
#    None
#cli.add_command(sam)
#
#@click.group()
#def gosls():
#    None
#cli.add_command(gosls)

@click.command(name="template-update")
@click.option("--input", "-i", default='template.json', help="Cloudformation JSON file.")
@click.option("--function", "-f", required=True, help="Lambda Function name")
@click.option("--output", "-o", default='-', help="Output file for modified template.")
@click.option("--token", "-t", envvar="IOPIPE_TOKEN", required=True, help="IOpipe Token")
def cf_update_template(template, function, output, token):
    update.update_cloudformation_file(template, function, output, token)

@click.command(name="stack-update")
@click.option("--stack-id", "-s", required=True, help="Cloudformation Stack ID.")
@click.option("--function", "-f", required=True, help="Lambda Function name")
@click.option("--token", "-t", envvar="IOPIPE_TOKEN", required=True, help="IOpipe Token")
def cf_update_stack(stack_id, function, token):
    update.update_cloudformation_stack(stack_id, function, token)

@click.command(name="lambda-update")
@click.option("--function", "-f", required=True, help="Lambda Function name")
@click.option("--layer-arn", "-l", help="Layer ARN for IOpipe library (default: auto-detect)")
@click.option("--token", "-t", envvar="IOPIPE_TOKEN", required=True, help="IOpipe Token")
def lambda_update_function(function, layer_arn, token):
    try:
        update.apply_function_api(function, layer_arn, token)
    except update.MultipleLayersException:
        print ("Multiple layers found. Pass --layer-arn to specify layer ARN")
        None

@click.command(name="list")
def lambda_list_functions():
    AwsLambda = boto3.client('lambda')
    funcs = AwsLambda.list_functions().get("Functions", [])

    print("Function Name\t\t\tRuntime\t\tInstrumented")
    for f in funcs:
        runtime = f.get("Runtime")
        new_handler = update.RUNTIME_CONFIG.get(runtime, {}).get('Handler', None)
        if f.get("Handler") == new_handler:
            f["-x-iopipe-enabled"] = True
        print("%s\t\t%s\t%s" % (f.get("FunctionName"), f.get("Runtime"), f.get("-x-iopipe-enabled", False)))
        

def click_groups():
    cli.add_command(local)
    local.add_command(cf_update_template)

    cli.add_command(remote)
    remote.add_command(lambda_list_functions)
    remote.add_command(lambda_update_function)
    remote.add_command(cf_update_stack)

def main():
    click_groups()
    try:
        cli()
    except botocore.exceptions.NoRegionError:
        print("You must specify a region. Have you run `aws configure`?")
    except botocore.exceptions.NoCredentialsError:
        print("No AWS credentials configured. Have you run `aws configure`?")
