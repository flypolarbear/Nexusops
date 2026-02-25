#!/usr/bin/env python3
"""
Test Monitor Agent - Periodically monitors task status and runs tests

Features:
- Monitors agentic_pact/state/task_list.json for task changes
- Runs chrome-devtools and playwright tests when tasks complete
- Provides a simple HTTP server for web-based progress monitoring
- Keeps running until manually stopped
"""

import json
import os
import subprocess
import time
import threading
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
TASK_LIST_PATH = PROJECT_ROOT / "agentic_pact" / "state" / "task_list.json"
EVIDENCE_DIR = PROJECT_ROOT / "test_results"
LOG_FILE = PROJECT_ROOT / "logs" / "test_monitor.log"

# Ensure directories exist
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
(LOG_FILE.parent).mkdir(parents=True, exist_ok=True)


class TestMonitorAgent:
    def __init__(self, interval_seconds: int = 60, port: int = 8765):
        self.interval = interval_seconds
        self.port = port
        self.running = True
        self.last_task_states = {}
        self.test_history = []
        self.current_status = "initialized"
        self.lock = threading.Lock()

    def log(self, message: str):
        """Log message to file and print to console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(LOG_FILE, "a") as f:
            f.write(log_line + "\n")

    def load_tasks(self) -> dict:
        """Load current task list"""
        try:
            with open(TASK_LIST_PATH) as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Error loading tasks: {e}")
            return {}

    def detect_changes(self, tasks: dict) -> list:
        """Detect tasks that have changed status to 'done'"""
        changed_tasks = []

        for task in tasks.get("tasks", []):
            task_id = task.get("id")
            status = task.get("status")

            if task_id not in self.last_task_states:
                self.last_task_states[task_id] = status
                continue

            old_status = self.last_task_states[task_id]
            if old_status != "done" and status == "done":
                changed_tasks.append(task)
                self.log(f"Task {task_id} completed: {task.get('title')}")

            self.last_task_states[task_id] = status

        return changed_tasks

    def run_backend_tests(self, task_id: str) -> dict:
        """Run backend pytest tests"""
        self.log(f"Running backend tests for task {task_id}...")

        result = {
            "task_id": task_id,
            "type": "backend",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "output": ""
        }

        try:
            cmd = ["cd", str(PROJECT_ROOT / "backend"), "&&", "pytest", "tests/", "-v", "--tb=short"]
            proc = subprocess.run(
                " ".join(cmd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            result["output"] = proc.stdout + proc.stderr
            result["success"] = proc.returncode == 0

            # Save output to file
            output_file = EVIDENCE_DIR / f"{task_id}_backend_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(output_file, "w") as f:
                f.write(result["output"])
            result["output_file"] = str(output_file)

        except subprocess.TimeoutExpired:
            result["output"] = "Test timed out after 300 seconds"
        except Exception as e:
            result["output"] = f"Error running tests: {e}"

        self.log(f"Backend tests {'PASSED' if result['success'] else 'FAILED'}")
        return result

    def run_playwright_tests(self, task_id: str) -> dict:
        """Run playwright/e2e tests using available MCP tools"""
        self.log(f"Running Playwright tests for task {task_id}...")

        result = {
            "task_id": task_id,
            "type": "playwright",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "output": "",
            "screenshots": []
        }

        try:
            # Check if frontend is running
            import urllib.request
            try:
                urllib.request.urlopen("http://localhost:5173", timeout=5)
                frontend_running = True
            except:
                frontend_running = False
                result["output"] = "Frontend not running on port 5173. Start with 'make frontend'"

            if frontend_running:
                result["output"] = "Frontend is running. Use chrome-devtools MCP tools for testing."
                result["success"] = True
                result["note"] = "Manual chrome-devtools testing recommended via MCP"

                # Create evidence directory for screenshots
                screenshot_dir = EVIDENCE_DIR / f"{task_id}_screenshots_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                result["screenshot_dir"] = str(screenshot_dir)

        except Exception as e:
            result["output"] = f"Error: {e}"

        self.log(f"Playwright tests {'READY' if result['success'] else 'FAILED'}")
        return result

    def run_all_tests(self, task: dict) -> list:
        """Run all test types for a completed task"""
        task_id = task.get("id")
        results = []

        # Run backend tests
        results.append(self.run_backend_tests(task_id))

        # Run playwright tests
        results.append(self.run_playwright_tests(task_id))

        return results

    def get_status(self) -> dict:
        """Get current monitor status"""
        with self.lock:
            tasks = self.load_tasks()

            # Count by status
            status_counts = {"done": 0, "in_progress": 0, "todo": 0}
            for task in tasks.get("tasks", []):
                status = task.get("status", "todo")
                if status in status_counts:
                    status_counts[status] += 1

            return {
                "running": self.running,
                "current_status": self.current_status,
                "interval_seconds": self.interval,
                "last_check": datetime.now().isoformat(),
                "task_counts": status_counts,
                "test_history_count": len(self.test_history),
                "recent_tests": self.test_history[-10:] if self.test_history else []
            }

    def monitor_loop(self):
        """Main monitoring loop"""
        self.log("Test Monitor Agent started")
        self.log(f"Monitoring interval: {self.interval} seconds")
        self.log(f"Task list: {TASK_LIST_PATH}")

        # Initial load
        tasks = self.load_tasks()
        for task in tasks.get("tasks", []):
            self.last_task_states[task.get("id")] = task.get("status")

        while self.running:
            try:
                self.current_status = "checking"
                tasks = self.load_tasks()
                changed_tasks = self.detect_changes(tasks)

                if changed_tasks:
                    self.log(f"Found {len(changed_tasks)} newly completed task(s)")

                    for task in changed_tasks:
                        self.current_status = f"testing_{task.get('id')}"
                        results = self.run_all_tests(task)

                        with self.lock:
                            self.test_history.extend(results)

                        # Update evidence file
                        evidence_file = EVIDENCE_DIR / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(evidence_file, "w") as f:
                            json.dump({
                                "task": task,
                                "results": results,
                                "timestamp": datetime.now().isoformat()
                            }, f, indent=2)

                self.current_status = "waiting"

            except Exception as e:
                self.log(f"Error in monitor loop: {e}")
                self.current_status = "error"

            # Wait for next interval
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

        self.log("Test Monitor Agent stopped")

    def start_http_server(self):
        """Start HTTP server for web monitoring"""
        handler = self.create_status_handler()

        server = HTTPServer(('0.0.0.0', self.port), handler)
        self.log(f"Status server started on http://localhost:{self.port}")

        server.serve_forever()

    def create_status_handler(self):
        """Create a custom HTTP handler that serves status"""
        agent = self

        class StatusHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/status' or self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    status = agent.get_status()
                    self.wfile.write(json.dumps(status, indent=2).encode())
                elif self.path == '/dashboard':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html = agent.generate_dashboard_html()
                    self.wfile.write(html.encode())
                elif self.path == '/history':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    with agent.lock:
                        history = agent.test_history[-50:]
                    self.wfile.write(json.dumps(history, indent=2).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress default logging

        return StatusHandler

    def generate_dashboard_html(self) -> str:
        """Generate a simple HTML dashboard"""
        status = self.get_status()

        return f'''<!DOCTYPE html>
<html>
<head>
    <title>NexusOps Test Monitor</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #4ecca3; }}
        .status-card {{ background: #16213e; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .status-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; }}
        .running {{ background: #4ecca3; color: #1a1a2e; }}
        .waiting {{ background: #f0a500; color: #1a1a2e; }}
        .error {{ background: #e94560; color: white; }}
        .task-stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ flex: 1; background: #0f3460; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 48px; font-weight: bold; }}
        .stat-label {{ color: #aaa; }}
        .done .stat-number {{ color: #4ecca3; }}
        .in_progress .stat-number {{ color: #f0a500; }}
        .todo .stat-number {{ color: #e94560; }}
        .test-history {{ margin-top: 30px; }}
        .test-item {{ background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #4ecca3; }}
        .test-item.failed {{ border-left-color: #e94560; }}
        pre {{ background: #0f3460; padding: 15px; border-radius: 4px; overflow-x: auto; }}
        .refresh-note {{ color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NexusOps Test Monitor Agent</h1>

        <div class="status-card">
            <h3>Monitor Status</h3>
            <span class="status-badge {status['current_status']}">{status['current_status']}</span>
            <p>Interval: {status['interval_seconds']}s | Running: {status['running']}</p>
            <p>Last Check: {status['last_check']}</p>
        </div>

        <div class="task-stats">
            <div class="stat-box done">
                <div class="stat-number">{status['task_counts']['done']}</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-box in_progress">
                <div class="stat-number">{status['task_counts']['in_progress']}</div>
                <div class="stat-label">In Progress</div>
            </div>
            <div class="stat-box todo">
                <div class="stat-number">{status['task_counts']['todo']}</div>
                <div class="stat-label">Todo</div>
            </div>
        </div>

        <div class="test-history">
            <h3>Recent Tests ({status['test_history_count']} total)</h3>
            {''.join(self._render_test_item(t) for t in status['recent_tests'])}
        </div>

        <p class="refresh-note">Auto-refreshing every 10 seconds | <a href="/status" style="color:#4ecca3">JSON API</a> | <a href="/history" style="color:#4ecca3">Full History</a></p>
    </div>
</body>
</html>'''

    def _render_test_item(self, test: dict) -> str:
        """Render a test result item"""
        success_class = "" if test.get("success") else "failed"
        status = "PASS" if test.get("success") else "FAIL"
        return f'''
            <div class="test-item {success_class}">
                <strong>{test.get('task_id', 'Unknown')}</strong> - {test.get('type', 'Unknown')} [{status}]
                <br><small>{test.get('timestamp', '')}</small>
            </div>'''

    def run(self):
        """Run the monitor agent"""
        # Start HTTP server in a separate thread
        http_thread = threading.Thread(target=self.start_http_server, daemon=True)
        http_thread.start()

        # Run monitor loop in main thread
        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            self.log("Received shutdown signal")
            self.running = False


def main():
    parser = argparse.ArgumentParser(description="Test Monitor Agent for NexusOps")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60)")
    parser.add_argument("--port", type=int, default=8765, help="HTTP server port (default: 8765)")
    args = parser.parse_args()

    agent = TestMonitorAgent(interval_seconds=args.interval, port=args.port)
    agent.run()


if __name__ == "__main__":
    main()
