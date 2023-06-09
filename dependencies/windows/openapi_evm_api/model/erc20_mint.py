# coding: utf-8

"""
    EVM API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 2.1
    Generated by: https://openapi-generator.tech
"""

from datetime import date, datetime  # noqa: F401
import decimal  # noqa: F401
import functools  # noqa: F401
import io  # noqa: F401
import re  # noqa: F401
import typing  # noqa: F401
import typing_extensions  # noqa: F401
import uuid  # noqa: F401

import frozendict  # noqa: F401

from openapi_evm_api import schemas  # noqa: F401


class Erc20Mint(
    schemas.AnyTypeSchema,
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """


    class MetaOapg:
        required = {
            "to_wallet",
            "block_timestamp",
            "block_hash",
            "block_number",
            "transaction_index",
            "contract_address",
            "log_index",
            "value",
            "transaction_hash",
        }
        
        class properties:
            contract_address = schemas.StrSchema
            transaction_hash = schemas.StrSchema
            transaction_index = schemas.IntSchema
            log_index = schemas.IntSchema
            block_timestamp = schemas.StrSchema
            block_number = schemas.IntSchema
            block_hash = schemas.StrSchema
            to_wallet = schemas.StrSchema
            value = schemas.StrSchema
            __annotations__ = {
                "contract_address": contract_address,
                "transaction_hash": transaction_hash,
                "transaction_index": transaction_index,
                "log_index": log_index,
                "block_timestamp": block_timestamp,
                "block_number": block_number,
                "block_hash": block_hash,
                "to_wallet": to_wallet,
                "value": value,
            }

    
    to_wallet: MetaOapg.properties.to_wallet
    block_timestamp: MetaOapg.properties.block_timestamp
    block_hash: MetaOapg.properties.block_hash
    block_number: MetaOapg.properties.block_number
    transaction_index: MetaOapg.properties.transaction_index
    contract_address: MetaOapg.properties.contract_address
    log_index: MetaOapg.properties.log_index
    value: MetaOapg.properties.value
    transaction_hash: MetaOapg.properties.transaction_hash
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["contract_address"]) -> MetaOapg.properties.contract_address: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["transaction_hash"]) -> MetaOapg.properties.transaction_hash: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["transaction_index"]) -> MetaOapg.properties.transaction_index: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["log_index"]) -> MetaOapg.properties.log_index: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["block_timestamp"]) -> MetaOapg.properties.block_timestamp: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["block_number"]) -> MetaOapg.properties.block_number: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["block_hash"]) -> MetaOapg.properties.block_hash: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["to_wallet"]) -> MetaOapg.properties.to_wallet: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["value"]) -> MetaOapg.properties.value: ...
    
    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...
    
    def __getitem__(self, name: typing.Union[typing_extensions.Literal["contract_address", "transaction_hash", "transaction_index", "log_index", "block_timestamp", "block_number", "block_hash", "to_wallet", "value", ], str]):
        # dict_instance[name] accessor
        return super().__getitem__(name)
    
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["contract_address"]) -> MetaOapg.properties.contract_address: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["transaction_hash"]) -> MetaOapg.properties.transaction_hash: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["transaction_index"]) -> MetaOapg.properties.transaction_index: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["log_index"]) -> MetaOapg.properties.log_index: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["block_timestamp"]) -> MetaOapg.properties.block_timestamp: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["block_number"]) -> MetaOapg.properties.block_number: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["block_hash"]) -> MetaOapg.properties.block_hash: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["to_wallet"]) -> MetaOapg.properties.to_wallet: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["value"]) -> MetaOapg.properties.value: ...
    
    @typing.overload
    def get_item_oapg(self, name: str) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...
    
    def get_item_oapg(self, name: typing.Union[typing_extensions.Literal["contract_address", "transaction_hash", "transaction_index", "log_index", "block_timestamp", "block_number", "block_hash", "to_wallet", "value", ], str]):
        return super().get_item_oapg(name)
    

    def __new__(
        cls,
        *args: typing.Union[dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, bool, None, list, tuple, bytes, io.FileIO, io.BufferedReader, ],
        to_wallet: typing.Union[MetaOapg.properties.to_wallet, str, ],
        block_timestamp: typing.Union[MetaOapg.properties.block_timestamp, str, ],
        block_hash: typing.Union[MetaOapg.properties.block_hash, str, ],
        block_number: typing.Union[MetaOapg.properties.block_number, decimal.Decimal, int, ],
        transaction_index: typing.Union[MetaOapg.properties.transaction_index, decimal.Decimal, int, ],
        contract_address: typing.Union[MetaOapg.properties.contract_address, str, ],
        log_index: typing.Union[MetaOapg.properties.log_index, decimal.Decimal, int, ],
        value: typing.Union[MetaOapg.properties.value, str, ],
        transaction_hash: typing.Union[MetaOapg.properties.transaction_hash, str, ],
        _configuration: typing.Optional[schemas.Configuration] = None,
        **kwargs: typing.Union[schemas.AnyTypeSchema, dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, None, list, tuple, bytes],
    ) -> 'Erc20Mint':
        return super().__new__(
            cls,
            *args,
            to_wallet=to_wallet,
            block_timestamp=block_timestamp,
            block_hash=block_hash,
            block_number=block_number,
            transaction_index=transaction_index,
            contract_address=contract_address,
            log_index=log_index,
            value=value,
            transaction_hash=transaction_hash,
            _configuration=_configuration,
            **kwargs,
        )
