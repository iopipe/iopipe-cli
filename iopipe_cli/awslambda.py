from . import layers
from . import utils


def list_functions(region, quiet, filter_choice):
    AwsLambda = utils.get_lambda_client(region)

    # set all if the filter_choice is "all" or there is no filter_choice active.
    all = filter_choice == "all" or not filter_choice

    pager = AwsLambda.get_paginator("list_functions")

    for func_resp in pager.paginate():
        funcs = func_resp.get("Functions", [])
        for f in funcs:
            for layer in f.get("Layers", []):
                if layer.get("Arn", "").startswith(utils.get_arn_prefix(region)):
                    f["-x-iopipe-enabled"] = True
            if all:
                yield f
            elif filter_choice == "installed" and f["-x-iopipe-enabled"]:
                yield f
            elif filter_choice == "not_installed" and not f["-x-iopipe-enabled"]:
                yield f


class MultipleLayersException(Exception):
    pass


class UpdateLambdaException(Exception):
    pass


def _add_iopipe(
    config, region, function_arn, layer_arn, token, java_type, allow_upgrade
):
    info = config.copy()
    runtime = info.get("Configuration", {}).get("Runtime", "")
    orig_handler = info.get("Configuration", {}).get("Handler")
    runtime_handler = utils.RUNTIME_CONFIG.get(runtime, {}).get("Handler")

    if not token:
        raise (UpdateLambdaException("Token missing from parameters."))

    if runtime.startswith("java"):
        # Special case of multiple legal handlers for Java
        if not java_type:
            raise UpdateLambdaException(
                "Must specify a handler type for java functions."
            )
        runtime_handler = (
            utils.RUNTIME_CONFIG.get(runtime, {}).get("Handler", {}).get(java_type)
        )

    if not allow_upgrade and orig_handler == runtime_handler:
        raise (
            UpdateLambdaException(
                "Already installed. Pass --upgrade (or -u) to allow upgrade or reinstall to latest layer version."
            )
        )
    if runtime == "provider" or runtime not in utils.RUNTIME_CONFIG.keys():
        raise UpdateLambdaException("Unsupported Lambda runtime: %s" % (runtime,))

    def _filter_iopipe_layers(layer_arn):
        if layer_arn.startswith(utils.get_arn_prefix(region)):
            return False
        return True

    def _map_response_to_arns(layer):
        return layer.get("Arn")

    existing_layers = list(
        filter(
            _filter_iopipe_layers,
            map(_map_response_to_arns, info.get("Configuration", {}).get("Layers", [])),
        )
    )

    iopipe_layers = []
    if layer_arn:
        iopipe_layers = [layer_arn]
    else:
        # discover compatible layers...
        disco_layers = utils.get_layers(region, runtime)
        if len(iopipe_layers) > 1:
            print("Discovered layers for runtime (%s)" % (runtime,))
            for layer in disco_layers:
                print(
                    "%s\t%s"
                    % (
                        layer.get("LatestMatchingVersion", {}).get(
                            "LayerVersionArn", ""
                        ),
                        layer.get("Description", ""),
                    )
                )
            raise MultipleLayersException()
        iopipe_layers = [
            disco_layers[0].get("LatestMatchingVersion", {}).get("LayerVersionArn", "")
        ]

    # print(json.dumps(info, indent=2))
    update_kwargs = {
        "FunctionName": function_arn,
        "Handler": runtime_handler,
        "Environment": {
            "Variables": info.get("Configuration", {})
            .get("Environment", {})
            .get("Variables", {})
        },
        "Layers": iopipe_layers + existing_layers,
    }

    # Update the token
    update_kwargs["Environment"]["Variables"]["IOPIPE_TOKEN"] = token

    # Update the IOPIPE_HANDLER envvars only when it's a new install.
    if orig_handler != runtime_handler:
        if runtime.startswith("java"):
            update_kwargs["Environment"]["Variables"][
                "IOPIPE_GENERIC_HANDLER"
            ] = orig_handler
        else:
            update_kwargs["Environment"]["Variables"]["IOPIPE_HANDLER"] = orig_handler

    return update_kwargs


def install(region, function_arn, layer_arn, token, java_type, allow_upgrade):
    AwsLambda = utils.get_lambda_client(region)
    info = AwsLambda.get_function(FunctionName=function_arn)
    update_kwargs = _add_iopipe(
        info, region, function_arn, layer_arn, token, java_type, allow_upgrade
    )
    return AwsLambda.update_function_configuration(**update_kwargs)


def _remove_iopipe(config, region, function_arn, layer_arn):
    info = config.copy()
    runtime = info.get("Configuration", {}).get("Runtime", "")
    orig_handler = info.get("Configuration", {}).get("Handler", "")

    if runtime == "provider" or runtime not in utils.RUNTIME_CONFIG.keys():
        raise UpdateLambdaException("Unsupported Lambda runtime: %s" % (runtime,))

    # Detect non-IOpipe handler and error if necessary.
    if not utils.is_valid_handler(runtime, orig_handler):
        raise UpdateLambdaException(
            "IOpipe installation (via layers) not auto-detected for the specified function.\n"
            "Error: Unrecognized handler in deployed function."
        )

    env_handler = (
        info.get("Configuration", {})
        .get("Environment", {})
        .get("Variables", {})
        .get("IOPIPE_HANDLER")
    )
    env_alt_handler = (
        info.get("Configuration", {})
        .get("Environment", {})
        .get("Variables", {})
        .get("IOPIPE_GENERIC_HANDLER")
    )
    env_handler = env_handler or env_alt_handler
    if not env_handler:
        raise UpdateLambdaException(
            "IOpipe installation (via layers) not auto-detected for the specified function.\n"
            + "Error: Environment variable IOPIPE_HANDLER or IOPIPE_GENERIC_HANDLER not found."
        )

    # Delete IOpipe env vars
    for key in ["IOPIPE_HANDLER", "IOPIPE_GENERIC_HANDLER", "IOPIPE_TOKEN"]:
        try:
            del info["Configuration"]["Environment"]["Variables"][key]
        except KeyError:
            pass

    # Remove IOpipe layers
    layers = info.get("Configuration", {}).get("Layers", [])
    for layer_idx, layer_arn in enumerate(layers):
        if layer_arn["Arn"].startswith(utils.get_arn_prefix(region)):
            del layers[layer_idx]

    return {
        "FunctionName": function_arn,
        "Handler": env_handler,
        "Environment": info["Configuration"]["Environment"],
        "Layers": layers,
    }


def uninstall(region, function_arn, layer_arn):
    AwsLambda = utils.get_lambda_client(region)
    info = AwsLambda.get_function(FunctionName=function_arn)
    update_kwargs = _remove_iopipe(info, region, function_arn, layer_arn)
    return AwsLambda.update_function_configuration(**update_kwargs)
