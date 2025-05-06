#!/bin/bash

API_URL="http://127.0.0.1:8080/submit-job"

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
http://127.0.0.1:8080/system-monitoring-information

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "env": {
      "job.mode": "BATCH",
      "parallelism": 1
    },
    "source": [
      {
        "plugin_name": "Jdbc",
        "plugin_output_table": "raw_data",
        "url":      "jdbc:postgresql://localhost:5432/postgres",
        "driver":   "org.postgresql.Driver",
        "username": "db_cluster_viewer",
        "password": "qfxu4dUDHZlJ",
        "query":    "select account_mapper, cif_number from account_mapper"
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
          "warehouse":      "s3://demo-seatunnel/",
          "catalog-impl":   "org.apache.iceberg.aws.glue.GlueCatalog",
          "io-impl":        "org.apache.iceberg.aws.s3.S3FileIO",
          "client.region":  "ap-southeast-1"
        }
      }
    ]
  }'


curl --location 'http://localhost:8080/submit-job' \
--header 'Content-Type: application/json' \
--data '{
  "params": {
    "jobId": "1234564234234",
    "jobName": "SeaTunnel-01241"
  },
  "env": {
    "execution.parallelism": 1,
    "job.mode": "STREAMING",
    "checkpoint.interval": 5000,
    "read_limit.bytes_per_second": 7000000,
    "read_limit.rows_per_second": 400
  },
  "source": [
    {
      "plugin_name": "Postgres-CDC",
      "plugin_output": "users_cdc",
      "username": "postgres",
      "password": "postgres",
      "decoding.plugin.name": "pgoutput",
      "database-names": ["postgres"],
      "schema-names": ["datalake"],
      "table-names": ["vikki_data.datalake.person"],
      "base-url": "jdbc:postgresql://host.docker.internal:5432/postgres?loggerLevel=OFF"
    }
  ],
  "transform": [],
  "sink": [
    {
      "plugin_name": "Console",
      "plugin_input": ["users_cdc"]
    }
  ]
}'




curl --location 'http://localhost:8080/submit-job' \
--header 'Content-Type: application/json' \
--data '{
  "params": {
    "jobId": "832923873",
    "jobName": "SeaTunnel-9393"
  },
  "env": {
    "execution.parallelism": 1,
    "job.mode": "STREAMING",
    "checkpoint.interval": 5000,
    "read_limit.bytes_per_second": 7000000,
    "read_limit.rows_per_second": 400
  },
  "source": [
    {
      "plugin_name": "Postgres-CDC",
      "plugin_output": "users_cdc",
      "username": "postgres",
      "password": "postgres",
      "decoding.plugin.name": "pgoutput",
      "database-names": ["vikki_data"],
      "schema-names": ["datalake"],
      "table-names": ["vikki_data.datalake.person"],
      "base-url": "jdbc:postgresql://host.docker.internal:5432/postgres?loggerLevel=OFF"
    }
  ],
  "transform": [],
  "sink": [
    {
      "plugin_name": "Kafka",
      "source_table_name": ["users_cdc"],
      "bootstrap.servers": "kafka:9092",
      "topic": "person_cdc",
      "format": "json",
      "schema.registry.url": "http://schema-registry:8081"
    }
  ]
}'

# isStopWithSavePoint: nếu dừng kèm savepoint thì đặt true
curl -X POST 'http://localhost:8080/stop-job' \
  -H 'Content-Type: application/json' \
  -d '{
    "jobId": 733584788375666689,
    "isStopWithSavePoint": false
}'

curl --location 'http://localhost:8080/submit-job' \
--header 'Content-Type: application/json' \
--data '{
  "params": {
    "jobId": "832923873",
    "jobName": "SeaTunnel-9393"
  },
  "env": {
    "execution.parallelism": 2,
    "job.mode": "STREAMING",
    "checkpoint.interval": 5000,
    "read_limit.bytes_per_second": 7000000,
    "read_limit.rows_per_second": 400
  },
  "source": [
    {
      "plugin_name": "Postgres-CDC",
      "plugin_output": "users_cdc",
      "username": "postgres",
      "password": "postgres",
      "decoding.plugin.name": "pgoutput",
      "database-names": ["vikki_data"],
      "schema-names": ["datalake"],
      "table-names": ["vikki_data.datalake.person"],
      "base-url": "jdbc:postgresql://host.docker.internal:5432/postgres?loggerLevel=OFF"
    }
  ],
  "transform": [],
  "sink": [
        {
            "plugin_name": "Iceberg",
            "plugin_input_table": "users_cdc",
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
}'


# env { 
#     job.mode = "streaming"
#     parallelism = 1
#     checkpoint.interval = 3000
#     checkpoint.timeout = 10000000
# }

# source {
#     SftpFile {
#         host = "localhost"
#         port = 2222
#         user = "foo"
#         password = "Passw0rd"
#         path = "/the_file.jsonl"
#         file_format_type = "json"
#         plugin_output = "sftp_source"
#         schema = {
#             fields {
#                 rating             = float
#                 title              = string
#                 text               = string
#                 images             = "array<map<string,string>>"
#                 asin               = string
#                 parent_asin        = string
#                 user_id            = string
#                 timestamp          = bigint
#                 verified_purchase  = boolean
#                 helpful_vote       = int
#             }
#         }

#     }
# }

# # transform {
# #     # FieldMapper {
# #     #     plugin_input = "duck_source"
# #     #     plugin_output = "mapped"
# #     #     field_mapper = {
# #     #         "id" : "user_id"
# #     #         "creation_date" : "created_at"
# #     #     }
# #     # }

# #     # FieldRename {
# #     #     plugin_input = "mapped"
# #     #     plugin_output = "filtered"
# #     #     convert_case = "UPPER"
# #     #     prefix = "F_"
# #     #     suffix = "_S"    
# #     # }

# #     Sql {
# #         plugin_input  = "sftp_source"
# #         plugin_output = "sql_transformed"
# #         query = """
# #             SELECT rating, title, text
# #             FROM sftp_source
# #         """
# #     }

# # }

# sink {
#   Iceberg {
#     plugin_input = "sql_transformed"

#     catalog_name = "glue_cat"         
#     iceberg.catalog.config = {
#       warehouse    = "s3://cuong-seatunnel-test/warehouse/"
#       catalog-impl = "org.apache.iceberg.aws.glue.GlueCatalog"
#       io-impl      = "org.apache.iceberg.aws.s3.S3FileIO"

#       "client.region" = "ap-southeast-1"        
#     }

#     namespace = "analytics_db"
#     table     = "amazan_reviews_software_rating_helpful_votes"
#   }
# }