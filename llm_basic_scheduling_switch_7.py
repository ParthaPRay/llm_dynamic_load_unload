#v5

# unloading models which are idle for more than MODEL_TIMEOUT duration

# curl -X POST http://localhost:5000/perform_task -H "Content-Type: application/json"   -d '{"task_type": "arithmetic", "model_name": "qwen2.5:0.5b-instruct", "prompt": "What is 2+2?"}'

from flask import Flask, request, jsonify
import requests
import time
import csv
from queue import Queue
from threading import Thread, Lock
import psutil  # For system resource monitoring

app = Flask(__name__)

# Constants
BASE_URL = "http://localhost:11434/api"
MODEL_TIMEOUT = 0  # Unload models after 60 seconds of inactivity
DEBUG = True
LOG_FILE = "llm_metrics.csv"

# Task Queue and Model State
task_queue = Queue()
model_last_used = {}
current_model = None
model_lock = Lock()

# Initialize the CSV log file
with open(LOG_FILE, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "timestamp", "task_type", "model_name", "prompt", "task_latency_ns",
        "model_switching_time_ns", "result", "status", "model_load_state",
        "total_duration_ns", "load_duration_ns", "prompt_eval_count",
        "prompt_eval_duration_ns", "eval_count", "eval_duration_ns",
        "tokens_per_second", "cpu_usage_percent", "memory_usage_percent", "system_load_avg"
    ])

# Debug Logging
def debug_log(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

# Append data to the CSV log file
def log_to_csv(data):
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            data.get("timestamp"),
            data.get("task_type"),
            data.get("model_name"),
            data.get("prompt"),
            data.get("task_latency_ns"),
            data.get("model_switching_time_ns"),
            data.get("result"),
            data.get("status"),
            data.get("model_load_state"),
            data.get("total_duration_ns", 0),
            data.get("load_duration_ns", 0),
            data.get("prompt_eval_count", 0),
            data.get("prompt_eval_duration_ns", 0),
            data.get("eval_count", 0),
            data.get("eval_duration_ns", 0),
            data.get("tokens_per_second", 0),
            data.get("cpu_usage_percent", 0),
            data.get("memory_usage_percent", 0),
            data.get("system_load_avg", 0)
        ])

# Monitor System Resources
# Monitor System Resources
# Monitor System Resources
def monitor_resources():
    try:
        # Prime psutil to initialize CPU usage calculations
        psutil.cpu_percent(interval=None)  # Initialize psutil CPU tracking
        cpu_usage = psutil.cpu_percent(interval=0.1)  # Capture CPU usage over 0.1-second
        memory_usage = psutil.virtual_memory().percent
        load_avg = psutil.getloadavg()[0]  # 1-minute load average

        # Ensure CPU usage is reasonable; fallback to 0 if invalid
        if cpu_usage < 0 or cpu_usage > 100:
            debug_log("Invalid CPU usage detected. Defaulting to 0.")
            cpu_usage = 0

        return cpu_usage, memory_usage, load_avg

    except Exception as e:
        debug_log(f"Error monitoring resources: {str(e)}")
        return 0, 0, 0  # Fallback for safety


# Load a Model
def load_model(model_name):
    global current_model
    with model_lock:
        if current_model == model_name:
            debug_log(f"Model '{model_name}' is already loaded.")
            return True, 0
        start_time = time.time_ns()
        payload = {"model": model_name, "keep_alive": -1}
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        duration = time.time_ns() - start_time
        if response.status_code == 200:
            current_model = model_name
            model_last_used[model_name] = time.time()
            debug_log(f"Model '{model_name}' loaded successfully in {duration} ns.")
            return True, duration
        debug_log(f"Failed to load model '{model_name}'.")
        return False, duration

# Unload Idle Models
# Unload Idle Models
def unload_idle_models():
    global current_model
    now = time.time()
    with model_lock:
        models_to_unload = []

        # Check all models in model_last_used for unloading
        for model_name, last_used in list(model_last_used.items()):
            if now - last_used > MODEL_TIMEOUT:
                models_to_unload.append(model_name)

        # Include current_model in unloading check
        if current_model and (current_model not in models_to_unload):
            if now - model_last_used.get(current_model, 0) > MODEL_TIMEOUT:
                models_to_unload.append(current_model)

        # Perform unloading for all identified models
        for model_name in models_to_unload:
            debug_log(f"Unloading model '{model_name}' after timeout.")
            payload = {"model": model_name, "keep_alive": 0}
            response = requests.post(f"{BASE_URL}/generate", json=payload)
            if response.status_code == 200:
                if model_name in model_last_used:
                    del model_last_used[model_name]
                if model_name == current_model:
                    current_model = None
                debug_log(f"Model '{model_name}' unloaded successfully.")
            else:
                debug_log(f"Failed to unload model '{model_name}'. Error: {response.text}")

# Process Tasks
def process_tasks():
    global current_model
    while True:
        unload_idle_models()
        if task_queue.empty():
            time.sleep(1)
            continue

        task = task_queue.get()
        debug_log(f"Processing task: {task}")
        cpu_before, memory_before, load_avg_before = monitor_resources()
        success, switch_duration = load_model(task['model_name'])
        model_load_state = "Loaded" if success else "Failed"
        
        if not success:
            debug_log(f"Failed to load model '{task['model_name']}' for task.")
            log_to_csv({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "task_type": task['task_type'],
                "model_name": task['model_name'],
                "prompt": task['prompt'],
                "task_latency_ns": 0,
                "model_switching_time_ns": switch_duration,
                "result": "N/A",
                "status": "Model Load Failed",
                "model_load_state": model_load_state,
                "cpu_usage_percent": cpu_before,
                "memory_usage_percent": memory_before,
                "system_load_avg": load_avg_before
            })
            task_queue.task_done()
            continue

        prompt = f"Perform {task['task_type']} on: {task['prompt']}"
        payload = {"model": task['model_name'], "prompt": prompt, "stream": False}
        start_time = time.time_ns()
        response = requests.post(f"{BASE_URL}/generate", json=payload)
        task_latency = time.time_ns() - start_time
        cpu_after, memory_after, load_avg_after = monitor_resources()

        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get("response", "No response received.")
            total_duration = response_data.get("total_duration", 0)
            load_duration = response_data.get("load_duration", 0)
            prompt_eval_count = response_data.get("prompt_eval_count", 0)
            prompt_eval_duration = response_data.get("prompt_eval_duration", 0)
            eval_count = response_data.get("eval_count", 0)
            eval_duration = response_data.get("eval_duration", 1)  # Avoid division by zero
            tokens_per_second = eval_count / eval_duration * 1e9

            debug_log(f"Task '{task['task_type']}' completed in {task_latency} ns. Result: {result}")
            log_to_csv({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "task_type": task['task_type'],
                "model_name": task['model_name'],
                "prompt": task['prompt'],
                "task_latency_ns": task_latency,
                "model_switching_time_ns": switch_duration,
                "result": result,
                "status": "Success",
                "model_load_state": model_load_state,
                "total_duration_ns": total_duration,
                "load_duration_ns": load_duration,
                "prompt_eval_count": prompt_eval_count,
                "prompt_eval_duration_ns": prompt_eval_duration,
                "eval_count": eval_count,
                "eval_duration_ns": eval_duration,
                "tokens_per_second": tokens_per_second,
                "cpu_usage_percent": cpu_after,
                "memory_usage_percent": memory_after,
                "system_load_avg": load_avg_after
            })
        else:
            debug_log(f"Task '{task['task_type']}' failed.")
            log_to_csv({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "task_type": task['task_type'],
                "model_name": task['model_name'],
                "prompt": task['prompt'],
                "task_latency_ns": task_latency,
                "model_switching_time_ns": switch_duration,
                "result": "N/A",
                "status": "Failed",
                "model_load_state": model_load_state,
                "cpu_usage_percent": cpu_after,
                "memory_usage_percent": memory_after,
                "system_load_avg": load_avg_after
            })
        task_queue.task_done()

# Flask Endpoint for Adding Tasks
@app.route("/perform_task", methods=["POST"])
def handle_task():
    data = request.json
    task_type = data.get("task_type")
    model_name = data.get("model_name")
    prompt = data.get("prompt")

    if not all([task_type, model_name, prompt]):
        return jsonify({"error": "Missing required fields."}), 400

    task = {
        "task_type": task_type,
        "model_name": model_name,
        "prompt": prompt
    }
    task_queue.put(task)
    debug_log(f"Task '{task_type}' added for model '{model_name}'.")
    return jsonify({"message": "Task added to queue."}), 200

# Start Task Processor
processor_thread = Thread(target=process_tasks, daemon=True)
processor_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

