# llm_dynamic_load_unload
This repo contains codes for dynamic load and unload llms on localized edge device

This script provides a Flask-based system to manage LLM model tasks by continous load and unloading on localized edge device using Ollama and Raspberry Pi 4B, focusing on efficient model usage and logging. Below is a breakdown of its main components:

Install Ollama https://github.com/ollama/ollama

Alyways perform the code under virtual environment.

Then pip install -r requirements.txt

Then run llm_basic_scheduling_switch_7.py in a terminal

Then run test.py on other terminal

Check the CSV logs.

### **Key Features**
1. **Model Management**:
   - Loads and unloads models based on usage.
   - Maintains an active model to reduce loading times.
   - Automatically unloads models idle beyond a configurable `MODEL_TIMEOUT`.

2. **Task Queue**:
   - Tasks (e.g., arithmetic operations) are added to a queue and processed sequentially.
   - Ensures tasks are assigned to appropriate models.

3. **System Resource Monitoring**:
   - Tracks CPU usage, memory usage, and system load averages using `psutil`.
   - Logs these metrics for performance analysis.

4. **Logging**:
   - Logs detailed task metrics, including timestamps, task latencies, resource usage, and model states, into a CSV file (`llm_metrics.csv`).
   - Supports debugging with optional console logs.

5. **REST API**:
   - Provides an endpoint (`/perform_task`) to add tasks via HTTP POST requests.
   - Accepts JSON payloads specifying the task type, model, and prompt.

6. **Concurrency**:
   - Processes tasks and manages models concurrently using threads and thread-safe mechanisms like `Lock`.

7. **Error Handling**:
   - Handles failed model loading or task execution gracefully.
   - Logs failures and returns appropriate error messages to clients.

---

### **Important Components**
1. **Constants**:
   - `BASE_URL`: Base URL for model interactions.
   - `MODEL_TIMEOUT`: Duration (in seconds) after which idle models are unloaded.
   - `DEBUG`: Enables debug logs for troubleshooting.
   - `LOG_FILE`: Path to the CSV log file.

2. **Key Functions**:
   - `debug_log`: Logs messages if debugging is enabled.
   - `log_to_csv`: Writes task and system performance metrics to a CSV file.
   - `monitor_resources`: Captures system resource usage metrics.
   - `load_model`: Loads a specified model and tracks its state.
   - `unload_idle_models`: Unloads models that haven't been used recently.
   - `process_tasks`: Main loop to process queued tasks and log their performance.

3. **REST Endpoint**:
   - `/perform_task`: Accepts task details and adds them to the queue.

4. **Background Thread**:
   - A daemon thread (`processor_thread`) runs the `process_tasks` function continuously.

---

### **Example Use Case**
1. **Add a Task**:
   A client sends a POST request to `/perform_task` with:
   
curl -X POST http://localhost:5000/perform_task -H "Content-Type: application/json"   -d '{"task_type": "arithmetic", "model_name": "qwen2.5:0.5b-instruct", "prompt": "What is 2+2?"}'
   
2. **Process Task**:
   - The task is added to the queue.
   - The system ensures the model is loaded, executes the task, and logs the result.
3. **Resource Monitoring**:
   - During task execution, CPU, memory, and load averages are monitored.
4. **Unload Idle Models**:
   - Models unused for `MODEL_TIMEOUT` are unloaded to conserve resources.

This system is ideal for scenarios requiring efficient AI model usage, such as dynamically handling multiple models with varying tasks while monitoring and logging system performance.
