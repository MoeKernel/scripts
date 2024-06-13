import subprocess
import requests
import os

OPENELA_API_URL = "https://api.github.com/repos/openela/kernel-lts/commits?sha=linux-4.14.y"
KERNEL_REPO_URL = "https://github.com/MoeKernel/android_kernel_xiaomi_ginkgo.git"
KERNEL_BRANCH = "linux-4.14.y"
KERNEL_REPO_DIR = "kernel_repo"
VERSION_FILE = "kernelversion.txt"

def get_latest_openela_commit():
    response = requests.get(OPENELA_API_URL)
    if response.status_code == 200:
        commits = response.json()
        if commits:
            latest_commit = commits[0]
            return latest_commit['sha']
    return None

def clone_kernel_repo():
    if os.path.exists(KERNEL_REPO_DIR):
        run_git_command("git fetch origin", KERNEL_REPO_DIR)
    else:
        run_git_command(f"git clone --depth=1 {KERNEL_REPO_URL} {KERNEL_REPO_DIR}", ".")

def run_git_command(command, repo_dir):
    result = subprocess.run(command, shell=True, cwd=repo_dir, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stdout, result.stderr
    return True, result.stdout, result.stderr

def fetch_openela_commits():
    latest_commit = get_latest_openela_commit()
    if latest_commit:
        return run_git_command(f"git fetch https://github.com/openela/kernel-lts.git {KERNEL_BRANCH}:refs/remotes/origin/{KERNEL_BRANCH}", KERNEL_REPO_DIR)
    else:
        print("Failed to fetch latest OpenELA commit.")
        return False, None, None

def cherry_pick_openela_commits():
    success, stdout, stderr = run_git_command(f"git log origin/{KERNEL_BRANCH}..HEAD --pretty=format:%H", KERNEL_REPO_DIR)
    if success:
        commits = stdout.strip().split('\n')
        for commit in commits:
            success, _, stderr = run_git_command(f"git cherry-pick {commit}", KERNEL_REPO_DIR)
            if not success:
                print(f"Conflict with commit {commit}, skipping...")
                run_git_command("git cherry-pick --skip", KERNEL_REPO_DIR)
    else:
        print(f"Error: {stderr}")

def get_latest_commit_message():
    response = requests.get(OPENELA_API_URL)
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

if __name__ == "__main__":
    if check_for_new_version():
        clone_kernel_repo()
        success, _, _ = fetch_openela_commits()
        if success:
            cherry_pick_openela_commits()
        else:
            print("Failed to fetch OpenELA commits.")

