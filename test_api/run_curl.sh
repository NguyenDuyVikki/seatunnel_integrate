#!/bin/bash

API_URL="http://172.16.0.2:8080/submit-job"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '
     {
    "env": {
        "job.mode": "BATCH",
        "parallelism": 1
    },
    "source": [
        {
            "plugin_name": "FakeSource",
            "plugin_output_table": "raw_data",
            "row_num": null,
            "schema": {
                "fields": {
                    "name": "string",
                    "age": "int"
                }
            }
        }
    ],
    "sink": [
        {
            "plugin_name": "Iceberg",
            "plugin_input_table": "raw_data",
            "catalog_name": "glue_catalog",
            "catalog_type": "glue",
            "namespace": "demo_glue_duy",
            "table": "seatunnel",
            "create_table_if_not_exists": "true",
            "iceberg.catalog.config": {
                "warehouse": "s3://demo-seatunnel/",
                "catalog-impl": "org.apache.iceberg.aws.glue.GlueCatalog",
                "io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
                "client.region": "ap-southeast-1"
            }
        }
    ]
}
    '
