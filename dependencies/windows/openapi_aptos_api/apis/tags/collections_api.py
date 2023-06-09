# coding: utf-8

"""
    aptos-api

    The aptos-api provider  # noqa: E501

    The version of the OpenAPI document: 1.0.0
    Generated by: https://openapi-generator.tech
"""

from openapi_aptos_api.paths.collections.get import GetNftCollections
from openapi_aptos_api.paths.collections_creators.get import GetNftCollectionsByCreator
from openapi_aptos_api.paths.collections_ids.get import GetNftCollectionsByIds


class CollectionsApi(
    GetNftCollections,
    GetNftCollectionsByCreator,
    GetNftCollectionsByIds,
):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """
    pass
