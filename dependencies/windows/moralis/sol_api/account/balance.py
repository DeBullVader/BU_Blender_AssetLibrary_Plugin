import json
import typing
import typing_extensions
from .api_instance import get_api_instance
from openapi_sol_api.paths.account_network_address_balance.get import RequestPathParams





class Params(RequestPathParams,):
    pass

def balance(api_key: str, params: Params):
    api_instance = get_api_instance(api_key, params)
    path_params: typing.Any = {k: v for k, v in params.items() if k in RequestPathParams.__annotations__.keys()}
    api_response = api_instance.balance(
        path_params=path_params,
        accept_content_types=(
            'application/json; charset=utf-8',
        ),
        skip_deserialization=True
    )

    return json.loads(api_response.response.data)
