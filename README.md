

# Forked from openapi2jsonschema project
https://github.com/instrumenta/openapi2jsonschema

# openapi2jsonschemasingleschema

A utility to extract [JSON Schema](http://json-schema.org/) from a
valid [OpenAPI](https://www.openapis.org/) specification.

With this forked extension you can generate to a single file instead of multiple once

## Why the fork

openapi2jsonschema is a great tool, but have not been updated in a long time. I also required the schema to be generated into a single schema file with the references included into the file.


## Requirements

Install pip if you don't have it. Follow the guide below:
https://pip.pypa.io/en/stable/installation/

## Installation

1. Clone down the project to your local directory.
2. In the terminal go to the directory where the folder `openapi2jsonschemasingleschema` exist 
3. Run the command
```
pip install -e openapi2jsonschemasingleschema
```

*Since we use the `-e option` when we install it locally, it becomes important that you don't more the folder after installation.* *If you move it you need to reinstall it again. I might deploy it into PIP so you don't need to install it locally in* *the future. *

## Usage

**TMF621 - Trouble Ticket example**

```
openapi2jsonschemasingleschema -o schemas/tmf621 -n "TroubleTicket" --include-references https://tmf-open-api-table-documents.s3.eu-west-1.amazonaws.com/OpenApiTable/4.0.0/swagger/TMF621-TroubleTicket-v4.0.0.swagger.json
```

This will generate the TroubleTicket schema and all it's references into a single file


**TMF622 - Product Order example**

```
openapi2jsonschemasingleschema -o schemas/tmf622 -n "ProductOrder" https://tmf-open-api-table-documents.s3.eu-west-1.amazonaws.com/OpenApiTable/4.0.0/swagger/TMF622-ProductOrder-v4.0.0.swagger.json
```

This will generate the ProductOrder schema but with no references into a single file

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


