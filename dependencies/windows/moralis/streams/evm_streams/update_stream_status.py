import json
import typing
import typing_extensions
from .api_instance import get_api_instance
from openapi_streams.paths.streams_evm_id_status.post import RequestPathParams, SchemaForRequestBodyApplicationJson





class Params(RequestPathParams,):
    pass

def update_stream_status(api_key: str, params: Params, body: SchemaForRequestBodyApplicationJson):
    api_instance = get_api_instance(api_key, params)
    path_params: typing.Any = {k: v for k, v in params.items() if k in RequestPathParams.__annotations__.keys()}
    api_response = api_instance.update_stream_status(
        body=body,
        path_params=path_params,
        accept_content_types=(
            'application/json; charset=utf-8',
        ),
        skip_deserialization=True
    )

    return json.loads(api_response.response.data)
