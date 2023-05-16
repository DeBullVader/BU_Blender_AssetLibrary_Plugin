import json
import typing
import typing_extensions
from .api_instance import get_api_instance
from openapi_streams.paths.streams_aptos_id_address.delete import RequestPathParams, SchemaForRequestBodyApplicationJson





class Params(RequestPathParams,):
    pass

def aptos_streams_delete_addresses(api_key: str, params: Params, body: SchemaForRequestBodyApplicationJson):
    api_instance = get_api_instance(api_key, params)
    path_params: typing.Any = {k: v for k, v in params.items() if k in RequestPathParams.__annotations__.keys()}
    api_response = api_instance.aptos_streams_delete_addresses(
        body=body,
        path_params=path_params,
        accept_content_types=(
            'application/json; charset=utf-8',
        ),
        skip_deserialization=True
    )

    return json.loads(api_response.response.data)
