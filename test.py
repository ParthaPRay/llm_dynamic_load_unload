import requests
import time

# API URL
API_URL = "http://localhost:5000/perform_task"

# Test Prompts
tasks = [
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"},
    {"task_type": "arithmetic", "model_name": "llama3.2:1b-instruct-q4_K_M", "prompt": "What is 5 + 3?"}
]

# Submit tasks
for i, task in enumerate(tasks, 1):
    print(f"Submitting task {i}/{len(tasks)}: {task}")
    response = requests.post(API_URL, json=task)
    if response.status_code == 200:
        print(f"Task {i} submitted successfully: {response.json()}")
    else:
        print(f"Task {i} failed: {response.text}")
    time.sleep(10)  # Simulate realistic delays

