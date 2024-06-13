import subprocess
import requests
import os

GITHUB_API_URL = "https://api.github.com/repos/openela/kernel-lts/commits?sha=linux-4.14.y"
VERSION_FILE = "kernelversion.txt"
KERNEL_REPO_URL = "https://github.com/openela/kernel-lts.git"
KERNEL_BRANCH = "linux-4.14.y"
KERNEL_REPO_DIR = "kernel_repo"

def get_latest_commit_message():
    response = requests.get(GITHUB_API_URL)
    if response.status_code == 200:
        commits = response.json()
        if commits:
            latest_commit = commits[0]
            return latest_commit['commit']['message']
    return None

def extract_version_from_commit_message(message):
    if "LTS: Update to" in message:
        return message.split("LTS: Update to")[1].strip()
    return None

def read_stored_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as file:
            return file.read().strip()
    return None

def write_stored_version(version):
    with open(VERSION_FILE, 'w') as file:
        file.write(version)

def check_for_new_version():
    latest_commit_message = get_latest_commit_message()
    if latest_commit_message:
        latest_version = extract_version_from_commit_message(latest_commit_message)
        if latest_version:
            stored_version = read_stored_version()
            if stored_version != latest_version:
                print(f"New version available: {latest_version}")
                write_stored_version(latest_version)
                return True
            else:
                print("No new version available.")
    else:
        print("Failed to fetch the latest commit message.")
    return False

def run_git_command(command, repo_dir):
    result = subprocess.run(command, shell=True, cwd=repo_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def clone_kernel_repo():
    if os.path.exists(KERNEL_REPO_DIR):
        run_git_command("git fetch", KERNEL_REPO_DIR)
    else:
        run_git_command(f"git clone {KERNEL_REPO_URL} {KERNEL_REPO_DIR}", ".")

def fetch_commits():
    return run_git_command(f"git fetch origin {KERNEL_BRANCH}", KERNEL_REPO_DIR)

def get_commit_hashes():
    result = subprocess.run(f"git rev-list FETCH_HEAD", shell=True, cwd=KERNEL_REPO_DIR, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().split("\n")
    else:
        print(f"Error: {result.stderr}")
        return []

def cherry_pick_commits(commits):
    for commit in commits:
        if not run_git_command(f"git cherry-pick {commit}", KERNEL_REPO_DIR):
            print(f"Conflict with commit {commit}, skipping...")
            run_git_command("git cherry-pick --skip", KERNEL_REPO_DIR)

if __name__ == "__main__":
    if check_for_new_version():
        clone_kernel_repo()
        if fetch_commits():
            commits = get_commit_hashes()
            cherry_pick_commits(commits)
        else:
            print("Failed to fetch commits.")

