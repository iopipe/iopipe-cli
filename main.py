#/usr/bin/env python
import boto3

RUNTIME_CONFIG = {
    'nodejs': {
        handler: 'node_modules/@iopipe/iopipe/handler'
    },
    'nodejs4.3': {
        handler: 'node_modules/@iopipe/iopipe/handler'
    },
    'nodejs6.10': {
        handler: 'node_modules/@iopipe/iopipe/handler'
    },
    'nodejs8.10': {
        handler: 'node_modules/@iopipe/iopipe/handler'
    },
    'java8': {
        handler: 'java.handler'
    },
    'python2.7': {
        handler: 'iopipe.handler'
    },
    'python3.6': {
        handler: 'iopipe.handler'
    },
    'python3.7': {
        handler: 'iopipe.handler'
    }
}

def list_functions():
    lambda.list_functions()

def apply_function(func):
    info = lambda.get_function(FunctionName=func)
    runtime = info.get('Configuration', {}).get('Runtime', '')
    orig_handler = info.get('Configuration', {}).get('Handler', '')
    new_handler = RUNTIME_CONFIG.get(runtime, {}).get('handler', '')

    if runtime == 'provider' or runtime not in RUNTIME_CONFIG.keys():
        print("Unsupported Lambda runtime: %s" % (runtime,))
    if orig_handler == new_handler:
        print("Already configured.")

    lambda.update_function_configuration(
        Handler=new_handler,
        Environment={
            'Variables': {
                'IOPIPE_HANDLER': orig_handler 
            }
        }
    )
    
