

# Forked from openapi2jsonschema
https://github.com/instrumenta/openapi2jsonschema

# openapi2jsonschemasinglefile

A utility to extract [JSON Schema](http://json-schema.org/) from a
valid [OpenAPI](https://www.openapis.org/) specification.

With this forked extension you can generate to a single file instead of multiple once

## Why

openapi2jsonschema is a great tool. But I required the schema to be generated into a single schema file with the references with the single file.


## Installation

`openapi2jsonschemasinglefile` is implemented in Python. Assuming you have a
Python intepreter and pip installed you should be able to install with:

```
pip install openapi2jsonschemasinglefile
```

This has not yet been widely tested and is currently in a _works on my
machine_ state.


## Usage

The simplest usage is to point the `openapi2jsonschema` tool at a URL
containing a JSON (or YAML) OpenAPI definition like so:

```
openapi2jsonschema https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json
```

This will generate a set of schemas in a `schemas` directory. The tool
provides a number of options to modify the output:

```
$ openapi2jsonschema --help
Usage: openapi2jsonschema [OPTIONS] SCHEMA

  Converts a valid OpenAPI specification into a set of JSON Schema files

Options:
  -n, --name   NAME     Which schema in the Swagger/OpenAPI that should be selected 
  -o, --output PATH     Directory to store schema files
  -p, --prefix TEXT     Prefix for JSON references (only for OpenAPI versions
                        before 3.0)
  --stand-alone         Whether or not to de-reference JSON schemas
  --kubernetes          Enable Kubernetes specific processors
  --strict              Prohibits properties not in the schema
                        (additionalProperties: false)
  --include-references  If references should be part in the name schema
  --help                Show this message and exit.
```


## Example

My specific usecase was being able to validate a Kubernetes
configuration file without a Kubernetes client like `kubectl` and
without the server. For that I have a bash script,
[available here](https://github.com/instrumenta/kubernetes-json-schema/blob/master/build.sh).

The output from running this script can be seen in the accompanying
[instrumenta/kubernetes-json-schema](https://github.com/instrumenta/kubernetes-json-schema).

