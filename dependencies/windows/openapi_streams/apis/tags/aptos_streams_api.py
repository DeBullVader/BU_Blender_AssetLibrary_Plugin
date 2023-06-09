# coding: utf-8

"""
    Streams Api

    API that provides access to Moralis Streams  # noqa: E501

    The version of the OpenAPI document: 1.0.0
    Generated by: https://openapi-generator.tech
"""

from openapi_streams.paths.streams_aptos_id_address.post import AptosStreamsAddAddresses
from openapi_streams.paths.streams_aptos.put import AptosStreamsCreate
from openapi_streams.paths.streams_aptos_id.delete import AptosStreamsDelete
from openapi_streams.paths.streams_aptos_id_address.delete import AptosStreamsDeleteAddresses
from openapi_streams.paths.streams_aptos_id.get import AptosStreamsGet
from openapi_streams.paths.streams_aptos_id_address.get import AptosStreamsGetAddresses
from openapi_streams.paths.streams_aptos.get import AptosStreamsGetAll
from openapi_streams.paths.streams_aptos_id.post import AptosStreamsUpdate
from openapi_streams.paths.streams_aptos_id_status.post import AptosStreamsUpdateStatus


class AptosStreamsApi(
    AptosStreamsAddAddresses,
    AptosStreamsCreate,
    AptosStreamsDelete,
    AptosStreamsDeleteAddresses,
    AptosStreamsGet,
    AptosStreamsGetAddresses,
    AptosStreamsGetAll,
    AptosStreamsUpdate,
    AptosStreamsUpdateStatus,
):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """
    pass
