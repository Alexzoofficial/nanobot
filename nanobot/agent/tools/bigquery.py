"""BigQuery tool for saving and reading data."""

import json
import os
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool

class BigQueryTool(Tool):
    """Tool to interact with Google BigQuery."""

    name = "bigquery"
    description = "Execute queries, read and write data to Google BigQuery."
    parameters = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["query", "insert", "list_datasets", "list_tables"],
                "description": "The operation to perform"
            },
            "query": {
                "type": "string",
                "description": "SQL query to execute (for 'query' operation)"
            },
            "dataset_id": {
                "type": "string",
                "description": "Dataset ID (for 'insert', 'list_tables' operations)"
            },
            "table_id": {
                "type": "string",
                "description": "Table ID (for 'insert' operation)"
            },
            "rows": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of row objects to insert (for 'insert' operation)"
            }
        },
        "required": ["operation"]
    }

    def __init__(self):
        self.key_path = Path.home() / ".nanobot" / "bigquery-key.json"
        self.client = None

    def _get_client(self):
        if self.client:
            return self.client

        if not self.key_path.exists():
            raise FileNotFoundError(f"BigQuery key not found at {self.key_path}")

        from google.cloud import bigquery
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(str(self.key_path))
        self.client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        return self.client

    async def execute(self, operation: str, **kwargs: Any) -> str:
        try:
            client = self._get_client()

            if operation == "query":
                query = kwargs.get("query")
                if not query:
                    return "Error: 'query' parameter is required for query operation"
                query_job = client.query(query)
                results = query_job.result()
                rows = [dict(row) for row in results]
                return json.dumps(rows, default=str)

            elif operation == "insert":
                dataset_id = kwargs.get("dataset_id")
                table_id = kwargs.get("table_id")
                rows = kwargs.get("rows")
                if not all([dataset_id, table_id, rows]):
                    return "Error: 'dataset_id', 'table_id', and 'rows' are required for insert operation"

                table_ref = client.dataset(dataset_id).table(table_id)
                errors = client.insert_rows_json(table_ref, rows)
                if errors == []:
                    return "Success: Rows inserted"
                else:
                    return f"Error inserting rows: {errors}"

            elif operation == "list_datasets":
                datasets = list(client.list_datasets())
                return json.dumps([d.dataset_id for d in datasets])

            elif operation == "list_tables":
                dataset_id = kwargs.get("dataset_id")
                if not dataset_id:
                    return "Error: 'dataset_id' is required for list_tables operation"
                tables = list(client.list_tables(dataset_id))
                return json.dumps([t.table_id for t in tables])

            else:
                return f"Error: Unknown operation '{operation}'"

        except Exception as e:
            return f"Error: {str(e)}"
