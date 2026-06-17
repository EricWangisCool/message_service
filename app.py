import os
import signal
import sys
import threading
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for message service
state = {
    "messages": [
        {"id": 1, "content": "Welcome to the system!"},
        {"id": 2, "content": "This is a simple Flask mock API."}
    ],
    "message_post_count": 0
}

# Thread function to shut down the server after a short delay
def shutdown_server():
    time.sleep(0.5)
    print("Shutting down the server as requested (POST /api/v1/message called 3 times)...")
    
    # Check if running inside Docker container or under Gunicorn (parent PID is 1 or /.dockerenv exists)
    if os.path.exists('/.dockerenv') or os.getppid() == 1:
        # Send SIGTERM to parent process (Gunicorn master) to stop the entire container
        os.kill(os.getppid(), signal.SIGTERM)
    else:
        # Send SIGINT to the current process to stop Flask development server cleanly
        os.kill(os.getpid(), signal.SIGINT)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/v1/message', methods=['POST'])
def post_message():
    data = request.get_json() or {}
    content = data.get('content')
    
    if not content:
        return jsonify({
            "status": "fail",
            "message": "Message content is required"
        }), 400
        
    state["message_post_count"] += 1
    new_id = len(state["messages"]) + 1
    state["messages"].append({"id": new_id, "content": content})
    
    response_data = {
        "status": "success",
        "message": f"Message posted successfully (Count: {state['message_post_count']}/3)",
        "posted_message": {"id": new_id, "content": content}
    }
    
    if state["message_post_count"] >= 3:
        response_data["message"] = "Message posted. Shutdown threshold reached (3 calls). Server is shutting down..."
        # Start a thread to shut down the server in 0.5s so this response can finish sending
        threading.Thread(target=shutdown_server).start()
        
    return jsonify(response_data), 200

@app.route('/api/v1/messages', methods=['GET'])
def get_messages():
    return jsonify({
        "status": "success",
        "messages": state["messages"]
    }), 200

if __name__ == '__main__':
    print("Starting Message Microservice on http://127.0.0.1:5003")
    app.run(host="127.0.0.1", port=5003, debug=False)
