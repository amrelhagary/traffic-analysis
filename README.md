# AWS Glue Job: Search Keyword & Revenue Attribution Analysis

## Overview
This AWS Glue PySpark job processes raw web traffic event logs to analyze the performance of search keywords and domains in generating revenue. It identifies purchase events, calculates total revenue per user IP, extracts search keywords from the referrer URL, and joins these datasets to attribute revenue to specific search sources.

## Architecture & Workflow
![System Design](./docs/ACS%20System%20Design.png)
1.  **Ingestion**: Reads raw event logs (TSV) from S3.
2.  **Parsing**: Converts string-based lists (`event_list`, `product_list`) into Spark Arrays.
3.  **Transformation**:
    *   Extracts the domain name from the referrer URL.
    *   Calculates total revenue based on product data.
    *   Extracts search keywords (e.g., `q`, `p`) from the referrer query string.
4.  **Filtering & Aggregation**:
    *   Filters for `Purchase` events.
    *   Aggregates revenue by `IP` address.
5.  **Join**: Joins aggregated purchase revenue with traffic data (keywords/domains) on `IP`.
6.  **Output**: Writes a consolidated TSV file to S3 containing Domain, Keywords, and Total Revenue.

## Prerequisites

To run this job, ensure the following prerequisites are met:

*   **AWS Account**: Access to AWS Glue, S3, and IAM.
*   **IAM Role**: The Glue Job Role must have permissions to:
    *   Read from `S3_INPUT_FILE_PATH`.
    *   Write to `S3_OUTPUT_FILE_PATH`.
    *   Access CloudWatch Logs.
*   **Data Format**: The input file must be a **Tab-Separated Values (TSV)** file with a header row.

## Input Schema

The job expects a TSV file with the following columns:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `hit_time_gmt` | Long | Unix timestamp of the hit. |
| `date_time` | Timestamp | Human-readable date and time. |
| `user_agent` | String | Browser/Client User Agent. |
| `ip` | String | User IP Address. |
| `event_list` | String | Comma-separated list of event codes (e.g., `1,2,10`). |
| `geo_city` | String | User's city. |
| `geo_region` | String | User's region/state. |
| `geo_country` | String | User's country. |
| `pagename` | String | Name of the page viewed. |
| `page_url` | String | Full URL of the page. |
| `product_list` | String | Comma-separated list of products. **Format**: `ID;Name;Qty;Price` per product. |
| `referrer` | String | URL of the previous page (used for domain/keyword extraction). |

## Output Schema

The job produces a TSV file with the following columns:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `domain` | String | Extracted domain from the referrer URL (e.g., `google.com`). |
| `keywords` | String | Extracted search keywords (e.g., `red shoes, winter sale`). |
| `total_revenue` | Integer | Sum of revenue attributed to the IP for purchase events. |

## Job Parameters

The job requires the following runtime arguments:

| Parameter Name | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `JOB_NAME` | Unique name for the Glue Job run. | Yes | - |
| `S3_INPUT_FILE_PATH` | S3 URI containing the raw input TSV file. | Yes | - |
| `S3_OUTPUT_FILE_PATH` | S3 URI where the output TSV will be written. | Yes | - |

## Configuration Details

### Business Logic Rules

1.  **Purchase Status**:
    *   An event is considered a **Purchase** if the integer `1` exists within the `event_list` column.
    *   Status Enum:
        *   `1`: PURCHASE
        *   `2`: PRODUCT_VIEW
        *   `10-14`: Shopping Cart interactions
2.  **Revenue Calculation**:
    *   The `product_list` string is split by comma.
    *   Each product entry is split by semicolon (`;`).
    *   The **4th field (index 3)** is treated as the price/revenue.
    *   Total Revenue = Sum of all valid price fields for the session.
3.  **Keyword Extraction**:
    *   Searches the `referrer` URL for query parameters `q` or `p`.
    *   Values are URL-decoded and stripped of whitespace.
    *   Multiple keywords are joined by a comma (`, `).
4.  **Domain Extraction**:
    *   Extracts the `netloc` from the `referrer`.
    *   Removes the `www.` prefix if present.
    *   **Exclusion**: Traffic from `esshopzilla.com` is excluded from keyword analysis.

### Output File Naming
The output filename is dynamically generated based on the current date:
`{YYYY-MM-DD}_SearchKeywordPerformance.tab`
*Note: Running this job multiple times on the same calendar day will overwrite the previous output file.*

## Local Deployment Instructions

### 1. Create the Script
Upload the `glue.py` code to the Glue Job script location in your AWS account or S3 bucket.

### 2. Configure the Job
1.  Navigate to the **AWS Glue** console.
2.  Create a new **Job**.
3.  Set the **Job Name** (e.g., `KeywordRevenueAnalysis`).
4.  Set the **Script location** to where you uploaded `glue.py`.
5.  Under **Arguments**, add the following key-value pairs:
    *   `JOB_NAME`: `KeywordRevenueAnalysis`
    *   `S3_INPUT_FILE_PATH`: `s3://your-bucket/input/raw_traffic_logs.tsv`
    *   `S3_OUTPUT_FILE_PATH`: `s3://your-bucket/output/processed/`

### 3. Run the Job
Click **Run Job** in the Glue console or trigger it via AWS Glue Triggers, CloudWatch Events, or the AWS CLI:

```bash
aws glue start-job-run \
    --job-name "KeywordRevenueAnalysis" \
    --arguments '{"JOB_NAME": "KeywordRevenueAnalysis", "S3_INPUT_FILE_PATH": "s3://your-bucket/input/raw_traffic_logs.tsv", "S3_OUTPUT_FILE_PATH": "s3://your-bucket/output/processed/"}'
```

## Terraform Deployment Instructions

### Pre-Deployment Checklist
### Before running Terraform, you must create these AWS resources manually:

#### Resource	Dev Account	Prod Account
S3 State Bucket	my-dev-tf-state-bucket	my-prod-tf-state-bucket
DynamoDB Lock Table	terraform-locks	terraform-locks
AWS CLI Profile	dev_account	prod_account
Create state bucket:

```bash
aws s3 mb s3://my-dev-tf-state-bucket --profile dev_account
aws s3 mb s3://my-prod-tf-state-bucket --profile prod_account

```

Create DynamoDB table:
```bash
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
  --profile dev_account
```
### Deploy
### Deploy Dev
```bash
cd environments/dev
terraform init
terraform apply
```

### Deploy Prod
```bash
cd ../prod
terraform init
terraform apply
```