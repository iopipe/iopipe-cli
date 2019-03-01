#!/usr/bin/env python
import boto3
import collections
import itertools
import json

from . import layers
from .combine_dict import combine_dict

AwsLambda = boto3.client('lambda')
CloudFormation = boto3.client('cloudformation')

RUNTIME_CONFIG = {
    'nodejs': {
        'Handler': 'node_modules/@iopipe/iopipe/handler'
    },
    'nodejs4.3': {
        'Handler': 'node_modules/@iopipe/iopipe/handler'
    },
    'nodejs6.10': {
        'Handler': 'node_modules/@iopipe/iopipe/handler'
    },
    'nodejs8.10': {
        'Handler': 'node_modules/@iopipe/iopipe/handler'
    },
    'java8': {
        'Handler': 'java.handler'
    },
    'python2.7': {
        'Handler': 'iopipe.handler'
    },
    'python3.0.6': {
        'Handler': 'iopipe.handler'
    },
    'python3.7': {
        'Handler': 'iopipe.handler'
    }
}

def get_region():
    session = boto3.session.Session()
    return session.region_name

def get_layers(runtime):
    return layers.index(get_region(), runtime)

def list_functions():
    AwsLambda.list_functions()

class MultipleLayersException(Exception):
    None

def apply_function_api(function_arn, layer_arn, token):
    info = AwsLambda.get_function(FunctionName=function_arn)
    runtime = info.get('Configuration', {}).get('Runtime', '')
    orig_handler = info.get('Configuration', {}).get('Handler', '')
    new_handler = RUNTIME_CONFIG.get(runtime, {}).get('Handler', None)

    if runtime == 'provider' or runtime not in RUNTIME_CONFIG.keys():
        print("Unsupported Lambda runtime: %s" % (runtime,))
        return
    if orig_handler == new_handler:
        print("Already configured.")
        return

    iopipe_layers = []
    existing_layers = []
    if layer_arn:
        iopipe_layers = [layer_arn]
    else:
        # compatible layers:
        disco_layers = get_layers(runtime)
        if len(iopipe_layers) > 1:
            print("Discovered layers for runtime (%s)" % (runtime,))
            for layer in disco_layers:
                print("%s\t%s" % (layer.get("LatestMatchingVersion", {}).get("LayerVersionArn", ""), layer.get("Description", "")))
            raise MultipleLayersException()
        iopipe_layers = [ disco_layers[0].get("LatestMatchingVersion", {}).get("LayerVersionArn", "") ]
        existing_layers = info.get('Configuration', {}).get('Layers', [])

    AwsLambda.update_function_configuration(
        FunctionName=function_arn,
        Handler=new_handler,
        Environment={
            'Variables': {
                'IOPIPE_HANDLER': orig_handler,
                'IOPIPE_TOKEN': token
            }
        },
        Layers=iopipe_layers + existing_layers
    )

def get_stack_ids():
    def stack_filter(stack_id):
        resources = CloudFormation.list_stack_resources(
            StackName=stack_id
        )
        for resource in resources['StackResourceSummaries']:
            if resource['ResourceType'] == 'LambdaResourceType-PLACEHOLDER':
                return True
    def map_stack_ids():
        for stack in stacks['StackSummaries']:
            return stack['StackId']

    token = None
    stack_id_pages = []
    while True:
        stacks = CloudFormation.list_stacks(NextToken=token)
        stack_id_pages += map(map_stack_ids, stacks)
        token = stacks['NextToken']
        if not token:
            break
    return filter(stack_filter, itertools.chain(*stack_id_pages))

def get_template(stackid):
    # DOC get_template: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.get_template
    template_body = CloudFormation.get_template(StackName=stackid)
    #    example_get_template_body = '''
    #    {
    #    'TemplateBody': {},
    #    'StagesAvailable': [
    #        'Original'|'Processed',
    #    ]
    #    }
    #    '''
    return template_body #apply_function_cloudformation(template_body)

def modify_cloudformation(template_body, function_arn, token):
    ##runtime = info.get('Configuration', {}).get('Runtime', '')
    ##orig_handler = info.get('Configuration', {}).get('Handler', '')
    func_template = template_body.get('Resources', {}).get(function_arn, {})
    orig_handler = func_template.get('Properties', {}).get('Handler', None)
    runtime = func_template.get('Properties', {}).get('Runtime', None)
    new_handler = RUNTIME_CONFIG.get(runtime, {}).get('Handler', None)

    if runtime == 'provider' or runtime not in RUNTIME_CONFIG.keys():
        print("Unsupported Lambda runtime: %s" % (runtime,))
        return None
    if orig_handler == new_handler:
        print("Already configured.")
        return None

    updates = {
        'Resources': {
            function_arn: {
                'Properties': {
                    'Handler': new_handler
                },
                'Environment': {
                    'Variables': {
                        'IOPIPE_HANDLER': orig_handler,
                        'IOPIPE_TOKEN': token 
                    }
                }
            }
        }
    }
    #context = DeepChainMap({}, updates, template_body)
    context = combine_dict(template_body, updates)
    return context

def update_cloudformation_file(filename, function_arn, output, token):
    # input options to support:
    # - cloudformation template file (json and yaml)
    # - cloudformation stack (deployed on AWS)
    # - SAM file
    # - Serverless.yml
    orig_template_body=""
    with open(filename) as yml:
        orig_template_body=json.loads(yml.read())
    cf_template = modify_cloudformation(orig_template_body, function_arn, token)
    if output == "-":
        print(json.dumps(cf_template, indent=2))
    else:
        with open(output, 'w') as yml:
            yml.write(json.dumps(cf_template, indent=2))

def update_cloudformation_stack(stack_id, function_arn):
    #stackid = get_stack_ids(function_arn)
    orig_template=get_template(stack_id)
    template_body=modify_cloudformation(orig_template, function_arn)
    # DOC update_stack: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.update_stack
    CloudFormation.update_stack(
        StackName=stack_id,
        TemplateBody=template_body
    )
