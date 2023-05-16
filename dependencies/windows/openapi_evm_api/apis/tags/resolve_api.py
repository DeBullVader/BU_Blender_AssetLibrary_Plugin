# coding: utf-8

"""
    EVM API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 2.1
    Generated by: https://openapi-generator.tech
"""

from openapi_evm_api.paths.resolve_address_reverse.get import ResolveAddress
from openapi_evm_api.paths.resolve_domain.get import ResolveDomain
from openapi_evm_api.paths.resolve_ens_domain.get import ResolveEnsDomain


class ResolveApi(
    ResolveAddress,
    ResolveDomain,
    ResolveEnsDomain,
):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """
    pass