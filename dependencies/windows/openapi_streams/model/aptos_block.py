# coding: utf-8

"""
    Streams Api

    API that provides access to Moralis Streams  # noqa: E501

    The version of the OpenAPI document: 1.0.0
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

from openapi_streams import schemas  # noqa: F401


class AptosBlock(
    schemas.DictSchema
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """


    class MetaOapg:
        required = {
            "lastVersion",
            "number",
            "firstVersion",
            "hash",
            "timestamp",
        }
        
        class properties:
            lastVersion = schemas.StrSchema
            firstVersion = schemas.StrSchema
            hash = schemas.StrSchema
            timestamp = schemas.StrSchema
            number = schemas.StrSchema
            __annotations__ = {
                "lastVersion": lastVersion,
                "firstVersion": firstVersion,
                "hash": hash,
                "timestamp": timestamp,
                "number": number,
            }
    
    lastVersion: MetaOapg.properties.lastVersion
    number: MetaOapg.properties.number
    firstVersion: MetaOapg.properties.firstVersion
    hash: MetaOapg.properties.hash
    timestamp: MetaOapg.properties.timestamp
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["lastVersion"]) -> MetaOapg.properties.lastVersion: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["firstVersion"]) -> MetaOapg.properties.firstVersion: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["hash"]) -> MetaOapg.properties.hash: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["timestamp"]) -> MetaOapg.properties.timestamp: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["number"]) -> MetaOapg.properties.number: ...
    
    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...
    
    def __getitem__(self, name: typing.Union[typing_extensions.Literal["lastVersion", "firstVersion", "hash", "timestamp", "number", ], str]):
        # dict_instance[name] accessor
        return super().__getitem__(name)
    
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["lastVersion"]) -> MetaOapg.properties.lastVersion: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["firstVersion"]) -> MetaOapg.properties.firstVersion: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["hash"]) -> MetaOapg.properties.hash: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["timestamp"]) -> MetaOapg.properties.timestamp: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["number"]) -> MetaOapg.properties.number: ...
    
    @typing.overload
    def get_item_oapg(self, name: str) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...
    
    def get_item_oapg(self, name: typing.Union[typing_extensions.Literal["lastVersion", "firstVersion", "hash", "timestamp", "number", ], str]):
        return super().get_item_oapg(name)
    

    def __new__(
        cls,
        *args: typing.Union[dict, frozendict.frozendict, ],
        lastVersion: typing.Union[MetaOapg.properties.lastVersion, str, ],
        number: typing.Union[MetaOapg.properties.number, str, ],
        firstVersion: typing.Union[MetaOapg.properties.firstVersion, str, ],
        hash: typing.Union[MetaOapg.properties.hash, str, ],
        timestamp: typing.Union[MetaOapg.properties.timestamp, str, ],
        _configuration: typing.Optional[schemas.Configuration] = None,
        **kwargs: typing.Union[schemas.AnyTypeSchema, dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, None, list, tuple, bytes],
    ) -> 'AptosBlock':
        return super().__new__(
            cls,
            *args,
            lastVersion=lastVersion,
            number=number,
            firstVersion=firstVersion,
            hash=hash,
            timestamp=timestamp,
            _configuration=_configuration,
            **kwargs,
        )
