#!/usr/bin/env python3
import update # relative import

import click

@click.command()
@click.option("--template", default='template.json', help="Cloudformation JSON file.")
@click.option("--function-name", help="Lambda Function name")
def main(template, function_name):
    update.update_cloudformation_file(template, function_name)

if __name__ == '__main__':
    main()