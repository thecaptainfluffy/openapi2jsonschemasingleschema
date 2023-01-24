#!/usr/bin/env python

import json
import yaml
import urllib
import os
import sys

from jsonref import JsonRef  # type: ignore
import click

from openapi2jsonschemasingleschema.log import info, debug, error
from openapi2jsonschemasingleschema.util import (
    additional_properties,
    get_full_name,
    process_specification,
    change_dict_values,
    append_no_duplicates,
    retrieve_all_references
)
from openapi2jsonschemasingleschema.errors import UnsupportedError


@click.command()
@click.option(
    "-o",
    "--output",
    default="schemas",
    metavar="PATH",
    help="Directory to store schema files",
)
@click.option(
    "-n",
    "--name",
    default="",
    help="What is the name of the primary schema that should be used",
)
@click.option(
    "-p",
    "--prefix",
    default="",
    help="Prefix for JSON references (only for OpenAPI versions before 3.0)",
)
@click.option(
    "--stand-alone", is_flag=True, help="Whether or not to de-reference JSON schemas"
)
@click.option(
    "--include-references", is_flag=True, help="Whether or not to include references from main schema to JSON schemas"
)
@click.option(
    "--expanded", is_flag=True, help="Expand Kubernetes schemas by API version"
)
@click.option(
    "--kubernetes", is_flag=True, help="Enable Kubernetes specific processors"
)
@click.option(
    "--strict",
    is_flag=True,
    help="Prohibits properties not in the schema (additionalProperties: false)",
)
@click.argument("schema", metavar="SCHEMA_URL")
def default(output, schema, name, prefix, stand_alone, include_references, expanded, kubernetes, strict):
    """
    Converts a valid OpenAPI specification into a set of JSON Schema files
    """
    info("Downloading schema")
    if sys.version_info < (3, 0):
        response = urllib.urlopen(schema)
    else:
        if os.path.isfile(schema):
            schema = "file://" + os.path.realpath(schema)
        req = urllib.request.Request(schema)
        response = urllib.request.urlopen(req)

    nameExist = name != ""

    info("Parsing schema")
    # Note that JSON is valid YAML, so we can use the YAML parser whether
    # the schema is stored in JSON or YAML
    data = yaml.load(response.read(), Loader=yaml.SafeLoader)

    if "swagger" in data:
        version = data["swagger"]
    elif "openapi" in data:
        version = data["openapi"]

    if not os.path.exists(output):
        os.makedirs(output)

    if version < "3":
        with open("%s/_definitions.json" % output, "w") as definitions_file:
            info("Generating shared definitions")
            definitions = data["definitions"]
            if kubernetes:
                definitions["io.k8s.apimachinery.pkg.util.intstr.IntOrString"] = {
                    "oneOf": [{"type": "string"}, {"type": "integer"}]
                }
                # Although the kubernetes api does not allow `number`  as valid
                # Quantity type - almost all kubenetes tooling
                # recognizes it is valid. For this reason, we extend the API definition to
                # allow `number` values.
                definitions["io.k8s.apimachinery.pkg.api.resource.Quantity"] = {
                    "oneOf": [{"type": "string"}, {"type": "number"}]
                }

                # For Kubernetes, populate `apiVersion` and `kind` properties from `x-kubernetes-group-version-kind`
                for type_name in definitions:
                    type_def = definitions[type_name]
                    if "x-kubernetes-group-version-kind" in type_def:
                        for kube_ext in type_def["x-kubernetes-group-version-kind"]:
                            if expanded and "apiVersion" in type_def["properties"]:
                                api_version = (
                                    kube_ext["group"] + "/" +
                                    kube_ext["version"]
                                    if kube_ext["group"]
                                    else kube_ext["version"]
                                )
                                append_no_duplicates(
                                    type_def["properties"]["apiVersion"],
                                    "enum",
                                    api_version,
                                )
                            if "kind" in type_def["properties"]:
                                kind = kube_ext["kind"]
                                append_no_duplicates(
                                    type_def["properties"]["kind"], "enum", kind
                                )
            if strict:
                definitions = additional_properties(definitions)
            definitions_file.write(json.dumps(
                {"definitions": definitions}, indent=2))

    types = []

    # Store a specific schema into a file 
    if version < "3":
        components = data["definitions"]
    else:
        components = data["components"]["schemas"]

    if nameExist: # components[name]
        specification = components[name]
        specification.setdefault("type", "object")

        # If references should be populated into the file
        if include_references:
            references = [name]
            references = retrieve_all_references(references, specification, components, version)
            for reference in references:
                if not name is reference:
                    specification[reference] = process_specification(kubernetes, reference, components, stand_alone, prefix, version, nameExist, output, strict)
        
        specification = process_specification(kubernetes, name, components, stand_alone, prefix, version, nameExist, output, strict)
        specification["$schema"] = "http://json-schema.org/schema#"

        full_name = get_full_name(name, kubernetes, stand_alone, expanded)

        with open("%s/%s.json" % (output, full_name), "w") as schema_file:
            debug("Generating %s.json" % full_name)
            schema_file.write(json.dumps(specification, indent=2))
    # Store all schemas into individual files 
    else:
        info("Generating individual schemas")
        
        for title in components:
            types.append(title)

            full_name = get_full_name(title, kubernetes, stand_alone, expanded)       

            try:
                debug("Processing %s" % full_name)
                specification = process_specification(kubernetes, title, components, stand_alone, prefix, version, nameExist, output, strict)

                with open("%s/%s.json" % (output, full_name), "w") as schema_file:
                    debug("Generating %s.json" % full_name)
                    schema_file.write(json.dumps(specification, indent=2))
            except Exception as e:
                error("An error occured processing %s: %s" % (full_name, e))

        with open("%s/all.json" % output, "w") as all_file:
            info("Generating schema for all types")
            contents = {"oneOf": []}
            for title in types:
                if version < "3":
                    contents["oneOf"].append(
                        {"$ref": "%s#/definitions/%s" % (prefix, title)}
                    )
                else:
                    contents["oneOf"].append(
                        {"$ref": (title.replace("#/components/schemas/", "") + ".json")}
                    )
            all_file.write(json.dumps(contents, indent=2))


if __name__ == "__main__":
    default()
