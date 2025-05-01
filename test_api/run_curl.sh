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
            "row.num": 10,
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
            "namespace": "seatunnel",
            "table": "test",
            "iceberg.catalog.config": {
              "warehouse": "s3://seatunnel/test/",
              "catalog-impl": "org.apache.iceberg.aws.glue.GlueCatalog",
              "io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
              "client.region": "ap-southeast-1"
            },
          }
        ]
      }
    '


# curl -X POST "$API_URL" \
#     -H "Content-Type: application/json" \
#     -d @stop_job.json


# curl --location 'http://172.16.0.2:8080/submit-job/upload' --form 'config_file=@"/temp/fake_to_console.conf"'
