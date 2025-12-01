from google.cloud import scheduler_v1

project_id = "ai-assistant-backend"
location = "europe-west1"

client = scheduler_v1.CloudSchedulerClient()
parent = f"projects/{project_id}/locations/{location}"

for job in client.list_jobs(parent=parent):
    print(f"Name: {job.name}")
    print(f"Schedule: {job.schedule}")
    print(f"State: {job.state.name}")