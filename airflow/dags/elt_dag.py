from datetime import datetime
from airflow import DAG
from docker.types import Mount
from airflow.utils.dates import days_ago
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator

from airflow.providers.docker.operators.docker import DockerOperator
import subprocess



CONN_ID = ''

# Define some parameters that Airflow needs
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
}

# Function to run the ELT script
# def run_elt_script(): 
#     # Path to elt_script in the Docker volume
#     script_path = "/opt/airflow/elt/elt_script.py"
#     result = subprocess.run(["python", script_path], capture_output=True, text=True)

#     if result.returncode != 0:
#         raise Exception(f"Script failed with error: {result.stderr}")
#     else:
#         print(result.stdout)

# Build the actual DAG itself
dag = DAG(
    'elt_and_dbt',
    default_args=default_args,
    description='An ELT workflow with dbt',
    start_date=datetime(2024,9,11),
    catchup=False,
)

# First task in Airflow
t1 = AirbyteTriggerSyncOperator(
    task_id="airbyte_postgres_postgres",
    airbyte_conn_id=CONN_ID,
    asynchronous=False,
    Timeout= 3600,
    wait_seconds=3,
    dag=dag
)

# Second task in Airflow
t2 = DockerOperator(
    task_id="dbt_run",
    image='ghcr.io/dbt-labs/dbt-postgres:1.4.7',
    command=[
        "run",
        "--profiles-dir",
        "/root",
        "--project-dir",
        "/opt/dbt"
    ],
    auto_remove=True,
    docker_url="unix://var/run/docker.sock",
    network_mode="bridge",
    mounts=[
        Mount(source='/Users/DEll/getting-started-with-Pipelines/custom_postgres',
              target='/opt/dbt', type='bind'),
        Mount(source='/Users/DEll/.dbt',
              target='/root', type='bind'),
    ],
    dag=dag,
)

# First task should have priority over the second
t1 >> t2
