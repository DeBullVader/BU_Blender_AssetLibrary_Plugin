import json
import typing
import typing_extensions
from .api_instance import get_api_instance
from openapi_evm_api.paths.ipfs_upload_folder.post import SchemaForRequestBodyApplicationJson







def upload_folder(api_key: str, body: SchemaForRequestBodyApplicationJson):
    api_instance = get_api_instance(api_key)
    api_response = api_instance.upload_folder(
        body=body,
        accept_content_types=(
            'application/json; charset=utf-8',
        ),
        skip_deserialization=True
    )

    return json.loads(api_response.response.data)
