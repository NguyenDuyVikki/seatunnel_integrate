#!/bin/bash

API_URL="http://172.16.0.2:8080/submit-jobs"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d @create_job.json



curl -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d @stop_job.json

