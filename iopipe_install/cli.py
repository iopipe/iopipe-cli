#!/usr/bin/env python3
from . import update

import click

@click.group()
def cli():
    None

@click.group()
def cloudformation():
    None
cli.add_command(cloudformation)

#@click.group()
#def sam():
#    None
#cli.add_command(sam)
#
#@click.group()
#def gosls():
#    None
#cli.add_command(gosls)

@click.command(name="update-template")
@click.option("--template", default='template.json', help="Cloudformation JSON file.")
@click.option("--function-name", required=True, help="Lambda Function name")
@click.option("--output", default='-', help="Output file for modified template.")
def cf_update_template(template, function_name, output):
    update.update_cloudformation_file(template, function_name, output)

@click.command(name="update-stack")
@click.option("--stack-id", required=True, help="Cloudformation Stack ID.")
@click.option("--function-name", required=True, help="Lambda Function name")
def cf_update_stack(stack_id, function_name):
    update.update_cloudformation_stack(stack_id, function_name)

@click.command(name="update-function")
@click.option("--function-name", required=True, help="Lambda Function name")
def lambda_update_function(function_name):
    update.apply_function_api(function_name)

def click_groups():
    cli.add_command(cloudformation)
    cloudformation.add_command(cf_update_template)
    cloudformation.add_command(cf_update_stack)
    cli.add_command(lambda_update_function)

def main():
    click_groups()
    cli()