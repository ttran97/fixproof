import os
import subprocess

# Vulnerability 1: Hardcoded Secret / API Key
API_SECRET_KEY = "sk_live_99887766554433221100aabbccdd"

# Vulnerability 2: Command Injection (Unsanitized User Input in System Call)
def run_user_command():
    user_input = input("Enter a directory to list: ")
    # Dangerous: Concatenating unescaped user input directly into shell command
    os.system("ls -la " + user_input)

# Vulnerability 3: Subprocess with shell=True
def check_ping():
    host = input("Enter host IP: ")
    # Dangerous: Passing raw strings to shell=True
    subprocess.call(f"ping -c 1 {host}", shell=True)

if __name__ == "__main__":
    run_user_command()