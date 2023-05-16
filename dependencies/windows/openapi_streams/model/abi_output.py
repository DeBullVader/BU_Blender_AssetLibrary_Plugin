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


class AbiOutput(
    schemas.DictSchema
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """


    class MetaOapg:
        required = {
            "name",
            "type",
        }
        
        class properties:
            name = schemas.StrSchema
            type = schemas.StrSchema
            
            
            class components(
                schemas.ListSchema
            ):
            
            
                class MetaOapg:
                    
                    @staticmethod
                    def items() -> typing.Type['AbiOutput']:
                        return AbiOutput
            
                def __new__(
                    cls,
                    arg: typing.Union[typing.Tuple['AbiOutput'], typing.List['AbiOutput']],
                    _configuration: typing.Optional[schemas.Configuration] = None,
                ) -> 'components':
                    return super().__new__(
                        cls,
                        arg,
                        _configuration=_configuration,
                    )
            
                def __getitem__(self, i: int) -> 'AbiOutput':
                    return super().__getitem__(i)
            internalType = schemas.StrSchema
            __annotations__ = {
                "name": name,
                "type": type,
                "components": components,
                "internalType": internalType,
            }
        additional_properties = schemas.NotAnyTypeSchema
    
    name: MetaOapg.properties.name
    type: MetaOapg.properties.type
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["name"]) -> MetaOapg.properties.name: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["type"]) -> MetaOapg.properties.type: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["components"]) -> MetaOapg.properties.components: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["internalType"]) -> MetaOapg.properties.internalType: ...
    
    def __getitem__(self, name: typing.Union[typing_extensions.Literal["name"], typing_extensions.Literal["type"], typing_extensions.Literal["components"], typing_extensions.Literal["internalType"], ]):
        # dict_instance[name] accessor
        return super().__getitem__(name)
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["name"]) -> MetaOapg.properties.name: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["type"]) -> MetaOapg.properties.type: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["components"]) -> typing.Union[MetaOapg.properties.components, schemas.Unset]: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["internalType"]) -> typing.Union[MetaOapg.properties.internalType, schemas.Unset]: ...
    
    def get_item_oapg(self, name: typing.Union[typing_extensions.Literal["name"], typing_extensions.Literal["type"], typing_extensions.Literal["components"], typing_extensions.Literal["internalType"], ]):
        return super().get_item_oapg(name)

    def __new__(
        cls,
        *args: typing.Union[dict, frozendict.frozendict, ],
        name: typing.Union[MetaOapg.properties.name, str, ],
        type: typing.Union[MetaOapg.properties.type, str, ],
        components: typing.Union[MetaOapg.properties.components, list, tuple, schemas.Unset] = schemas.unset,
        internalType: typing.Union[MetaOapg.properties.internalType, str, schemas.Unset] = schemas.unset,
        _configuration: typing.Optional[schemas.Configuration] = None,
    ) -> 'AbiOutput':
        return super().__new__(
            cls,
            *args,
            name=name,
            type=type,
            components=components,
            internalType=internalType,
            _configuration=_configuration,
        )
