import http.server
import socketserver
import subprocess
import threading
import urllib.parse
import time
import signal
import sys
import re

PORT = 52834
TIMEOUT = 420  # Timeout in seconds (7 minutes)
job_running = False
process = None

# Regular expression to validate Git branch names
branch_regex = re.compile(r'^(?!.*--)[a-z][a-z0-9-]*[a-z0-9]$')

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global job_running, process

        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'branch' in params:
            branch = params['branch'][0]
            if not branch_regex.match(branch):
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Bad Request: Invalid branch name.\n")
                return
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bad Request: Missing required parameters.\n")
            return

        # Check if a job is already running
        if job_running:
            self.send_response(429)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Too Many Requests: A job is already running.\n")
            return
        else:
            job_running = True

        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        
        # Launch the setup.sh script with the branch parameter and capture its output
        process = subprocess.Popen(['./setup.sh', branch], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        start_time = time.time()
        
        def stream_output(pipe):
            for line in iter(pipe.readline, ''):
                self.wfile.write(line.encode('utf-8'))
                self.wfile.flush()
            pipe.close()
        
        stdout_thread = threading.Thread(target=stream_output, args=(process.stdout,))
        stderr_thread = threading.Thread(target=stream_output, args=(process.stderr,))
        
        stdout_thread.start()
        stderr_thread.start()
        
        while stdout_thread.is_alive() or stderr_thread.is_alive():
            if time.time() - start_time > TIMEOUT:
                process.kill()
                self.wfile.write(b"\nProcess killed due to timeout.\n")
                break
            time.sleep(0.1)
        
        process.wait()

        # Mark the job as finished
        job_running = False

    def finish(self):
        global process, job_running
        if process and process.poll() is None:
            process.send_signal(signal.SIGINT)
            process.wait()
        job_running = False
        super().finish()

class ThreadingSimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def run_server():
    with ThreadingSimpleServer(("", PORT), MyHandler) as httpd:
        print(f"Serving on port {PORT}")
        
        def signal_handler(sig, frame):
            print("\nServer is shutting down.")
            httpd.server_close()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()

