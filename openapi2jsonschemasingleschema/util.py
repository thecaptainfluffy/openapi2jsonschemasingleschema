#!/usr/bin/env python
import os

from jsonref import JsonRef  # type: ignore
from openapi2jsonschemasingleschema.errors import UnsupportedError


def iteritems(d):
    if hasattr(dict, "iteritems"):
        return d.iteritems()
    else:
        return iter(d.items())


def additional_properties(data):
    "This recreates the behaviour of kubectl at https://github.com/kubernetes/kubernetes/blob/225b9119d6a8f03fcbe3cc3d590c261965d928d0/pkg/kubectl/validation/schema.go#L312"
    new = {}
    try:
        for k, v in iteritems(data):
            new_v = v
            if isinstance(v, dict):
                if "properties" in v:
                    if "additionalProperties" not in v:
                        v["additionalProperties"] = False
                new_v = additional_properties(v)
            else:
                new_v = v
            new[k] = new_v
        return new
    except AttributeError:
        return data


def replace_int_or_string(data):
    new = {}
    try:
        for k, v in iteritems(data):
            new_v = v
            if isinstance(v, dict):
                if "format" in v and v["format"] == "int-or-string":
                    new_v = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
                else:
                    new_v = replace_int_or_string(v)
            elif isinstance(v, list):
                new_v = list()
                for x in v:
                    new_v.append(replace_int_or_string(x))
            else:
                new_v = v
            new[k] = new_v
        return new
    except AttributeError:
        return data


def allow_null_optional_fields(data, parent=None, grand_parent=None, key=None):
    new = {}
    try:
        for k, v in iteritems(data):
            new_v = v
            if isinstance(v, dict):
                new_v = allow_null_optional_fields(v, data, parent, k)
            elif isinstance(v, list):
                new_v = list()
                for x in v:
                    new_v.append(allow_null_optional_fields(x, v, parent, k))
            elif isinstance(v, str):
                is_non_null_type = k == "type" and v != "null"
                has_required_fields = grand_parent and "required" in grand_parent
                is_required_field = (
                    has_required_fields and key in grand_parent["required"]
                )
                if is_non_null_type and not is_required_field:
                    new_v = [v, "null"]
            new[k] = new_v
        return new
    except AttributeError:
        return data

def retrieve_all_references(references, d, definitions, version):
    for reference in retrieve_references([], d, version):
        if not reference in references:
            references.append(reference)
            retrieve_all_references(references, definitions[reference], definitions, version)
    
    return references

def retrieve_references(references, d, version):
    for k, v in iteritems(d):
        if isinstance(v, dict):
            retrieve_references(references, v, version)
        elif isinstance(v, str):
            if k == "$ref":
                if version < "3":
                    v = v.replace("#/definitions/", "")
                else:
                    v = v.replace("#/components/schemas/", "")
                if not v in references:
                    references.append(v)
                
    return references

def change_dict_values(d, prefix, version, singlefile):
    new = {}
    try:
        for k, v in iteritems(d):
            new_v = v
            if isinstance(v, dict):
                new_v = change_dict_values(v, prefix, version, singlefile)
            elif isinstance(v, list):
                new_v = list()
                for x in v:
                    new_v.append(change_dict_values(x, prefix, version, singlefile))
            elif isinstance(v, str):
                if k == "$ref":
                    if version < "3":
                        if (singlefile):
                            new_v = "%s%s" % (prefix, v.replace("#/definitions", "#"))
                        else:
                            new_v = "%s%s" % (prefix, v.replace("#/definitions", "#")) + ".json"   
                    else:
                        if (singlefile):
                            new_v = v.replace("#/components/schemas", "#")
                        else:
                            new_v = v.replace("#/components/schemas/", "") + ".json"                        
            else:
                new_v = v
            new[k] = new_v
        return new
    except AttributeError:
        return d


def append_no_duplicates(obj, key, value):
    """
    Given a dictionary, lookup the given key, if it doesn't exist create a new array.
    Then check if the given value already exists in the array, if it doesn't add it.
    """
    if key not in obj:
        obj[key] = []
    if value not in obj[key]:
        obj[key].append(value)

def process_specification(kubernetes, title, components, stand_alone, prefix, version, nameExist, output, strict):
    specification = components[title]
    if not nameExist:
        specification["$schema"] = "http://json-schema.org/schema#"
        
    specification.setdefault("type", "object")

    if strict:
        specification["additionalProperties"] = False
    
    # These APIs are all deprecated
    if kubernetes:
        if title.split(".")[3] == "pkg" and title.split(".")[2] == "kubernetes":
            raise UnsupportedError(
                "%s not currently supported, due to use of pkg namespace"
                % title
            )

    updated = change_dict_values(specification, prefix, version, nameExist)
    specification = updated

    if stand_alone:
        base = "file://%s/%s/" % (os.getcwd(), output)
        specification = JsonRef.replace_refs(
            specification, base_uri=base)

    if "additionalProperties" in specification:
        if specification["additionalProperties"]:
            updated = change_dict_values(
                specification["additionalProperties"], prefix, version, nameExist
            )
            specification["additionalProperties"] = updated

    if strict and "properties" in specification:
        updated = additional_properties(specification["properties"])
        specification["properties"] = updated

    if kubernetes and "properties" in specification:
        updated = replace_int_or_string(specification["properties"])
        updated = allow_null_optional_fields(updated)
        specification["properties"] = updated
    
    return specification

def get_full_name(title, kubernetes, stand_alone, expanded):
    kind = title.split(".")[-1]
    if kubernetes:
        group = title.split(".")[-3]
        api_version = title.split(".")[-2]
    
        # This list of Kubernetes types carry around jsonschema for Kubernetes and don't
    # currently work with openapi2jsonschema
    if (
        kubernetes
        and stand_alone
        and kind
        in [
            "jsonschemaprops",
            "jsonschemapropsorarray",
            "customresourcevalidation",
            "customresourcedefinition",
            "customresourcedefinitionspec",
            "customresourcedefinitionlist",
            "customresourcedefinitionspec",
            "jsonschemapropsorstringarray",
            "jsonschemapropsorbool",
        ]
    ):
        raise UnsupportedError("%s not currently supported" % kind)

    if kubernetes and expanded:
        if group in ["core", "api"]:
            full_name = "%s-%s" % (kind, api_version)
        else:
            full_name = "%s-%s-%s" % (kind, group, api_version)
    else:
        full_name = kind  
    
    return full_name
