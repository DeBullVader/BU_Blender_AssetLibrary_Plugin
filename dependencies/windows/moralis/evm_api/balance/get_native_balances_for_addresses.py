import json
import typing
import typing_extensions
from .api_instance import get_api_instance
from openapi_evm_api.paths.wallets_balances.get import RequestQueryParams



class QueryParams(RequestQueryParams):
    pass

class Params(QueryParams,):
    pass

def get_native_balances_for_addresses(api_key: str, params: Params):
    api_instance = get_api_instance(api_key, params)
    query_params: typing.Any = {k: v for k, v in params.items() if k in RequestQueryParams.__annotations__.keys()}
    api_response = api_instance.get_native_balances_for_addresses(
        query_params=query_params,
        accept_content_types=(
            'application/json; charset=utf-8',
        ),
        skip_deserialization=True
    )

    return json.loads(api_response.response.data)
