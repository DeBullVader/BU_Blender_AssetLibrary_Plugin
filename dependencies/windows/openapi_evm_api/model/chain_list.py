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


class ChainList(
    schemas.EnumBase,
    schemas.StrSchema
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """


    class MetaOapg:
        enum_value_to_name = {
            "eth": "ETH",
            "0x1": "X1",
            "goerli": "GOERLI",
            "0x5": "X5",
            "sepolia": "SEPOLIA",
            "0xaa36a7": "XAA36A7",
            "polygon": "POLYGON",
            "0x89": "X89",
            "mumbai": "MUMBAI",
            "0x13881": "X13881",
            "bsc": "BSC",
            "0x38": "X38",
            "bsc testnet": "BSC_TESTNET",
            "0x61": "X61",
            "avalanche": "AVALANCHE",
            "0xa86a": "XA86A",
            "avalanche testnet": "AVALANCHE_TESTNET",
            "0xa869": "XA869",
            "fantom": "FANTOM",
            "0xfa": "XFA",
            "palm": "PALM",
            "0x2a15c308d": "X2A15C308D",
            "cronos": "CRONOS",
            "0x19": "X19",
            "cronos testnet": "CRONOS_TESTNET",
            "0x152": "X152",
            "arbitrum": "ARBITRUM",
            "0xa4b1": "XA4B1",
        }
    
    @schemas.classproperty
    def ETH(cls):
        return cls("eth")
    
    @schemas.classproperty
    def X1(cls):
        return cls("0x1")
    
    @schemas.classproperty
    def GOERLI(cls):
        return cls("goerli")
    
    @schemas.classproperty
    def X5(cls):
        return cls("0x5")
    
    @schemas.classproperty
    def SEPOLIA(cls):
        return cls("sepolia")
    
    @schemas.classproperty
    def XAA36A7(cls):
        return cls("0xaa36a7")
    
    @schemas.classproperty
    def POLYGON(cls):
        return cls("polygon")
    
    @schemas.classproperty
    def X89(cls):
        return cls("0x89")
    
    @schemas.classproperty
    def MUMBAI(cls):
        return cls("mumbai")
    
    @schemas.classproperty
    def X13881(cls):
        return cls("0x13881")
    
    @schemas.classproperty
    def BSC(cls):
        return cls("bsc")
    
    @schemas.classproperty
    def X38(cls):
        return cls("0x38")
    
    @schemas.classproperty
    def BSC_TESTNET(cls):
        return cls("bsc testnet")
    
    @schemas.classproperty
    def X61(cls):
        return cls("0x61")
    
    @schemas.classproperty
    def AVALANCHE(cls):
        return cls("avalanche")
    
    @schemas.classproperty
    def XA86A(cls):
        return cls("0xa86a")
    
    @schemas.classproperty
    def AVALANCHE_TESTNET(cls):
        return cls("avalanche testnet")
    
    @schemas.classproperty
    def XA869(cls):
        return cls("0xa869")
    
    @schemas.classproperty
    def FANTOM(cls):
        return cls("fantom")
    
    @schemas.classproperty
    def XFA(cls):
        return cls("0xfa")
    
    @schemas.classproperty
    def PALM(cls):
        return cls("palm")
    
    @schemas.classproperty
    def X2A15C308D(cls):
        return cls("0x2a15c308d")
    
    @schemas.classproperty
    def CRONOS(cls):
        return cls("cronos")
    
    @schemas.classproperty
    def X19(cls):
        return cls("0x19")
    
    @schemas.classproperty
    def CRONOS_TESTNET(cls):
        return cls("cronos testnet")
    
    @schemas.classproperty
    def X152(cls):
        return cls("0x152")
    
    @schemas.classproperty
    def ARBITRUM(cls):
        return cls("arbitrum")
    
    @schemas.classproperty
    def XA4B1(cls):
        return cls("0xa4b1")
