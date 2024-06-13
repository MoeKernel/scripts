import os
import requests
import subprocess
from dotenv import load_dotenv

OPENELA_API_URL = "https://api.github.com/repos/whyakari/kernel-lts/commits?sha=linux-4.14.y"
KERNEL_REPO_URL = "https://github.com/MoeKernel/android_kernel_xiaomi_ginkgo.git"
KERNEL_BRANCH = "linux-4.14.y"
KERNEL_REPO_DIR = "kernel_repo"
VERSION_FILE_PATH = "kernelversion.txt"
SCRIPTS_REPO_URL = "https://github.com/MoeKernel/scripts.git"

load_dotenv()

TOKEN_GITHUB = os.getenv('TOKEN_GITHUB', '')
USER = "MoeKernel"
REPO = "scripts"

def get_latest_openela_commits():
    response = requests.get(OPENELA_API_URL)
    if response.status_code == 200:
        commits = response.json()
        if commits:
            return commits
    return []

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
    return run_git_command(f"git fetch https://github.com/openela/kernel-lts.git {KERNEL_BRANCH}:refs/remotes/origin/{KERNEL_BRANCH}", KERNEL_REPO_DIR)

def cherry_pick_openela_commits(new_commits):
    for commit in new_commits:
        success, _, stderr = run_git_command(f"git cherry-pick {commit['sha']}", KERNEL_REPO_DIR)
        if not success:
            print(f"Conflict with commit {commit['sha']}, skipping...")
            run_git_command("git cherry-pick --skip", KERNEL_REPO_DIR)

def get_latest_commit_message():
    commits = get_latest_openela_commits()
    if commits:
        latest_commit = commits[0]
        return latest_commit['commit']['message']
    return None

def extract_version_from_commit_message(message):
    if "LTS: Update to" in message:
        return message.split("LTS: Update to")[1].strip()
    return None

def read_stored_version():
    if os.path.exists(VERSION_FILE_PATH):
        with open(VERSION_FILE_PATH, 'r') as file:
            return file.read().strip()
    return None

def write_stored_version(version):
    with open(VERSION_FILE_PATH, 'w') as file:
        file.write(version)

    run_git_command("git add kernelversion.txt", ".")
    run_git_command(f"git commit -m 'Update kernel version to {version}'", ".")
    run_git_command("git push origin", REPO)

def commit_and_push_version(version):
    url_remoto = f'https://{USER}:{TOKEN_GITHUB}@github.com/{USER}/{REPO}.git'
    subprocess.run(["git", "remote", "set-url", "origin", url_remoto])
    subprocess.run(["git", "config", "--global", "user.email", "akariondev@gmail.com"])
    subprocess.run(["git", "config", "--global", "user.name", "ginkgo"])

    # Adicionar, commitar e enviar o arquivo de versão
    subprocess.run(["git", "add", VERSION_FILE_PATH])
    subprocess.run(["git", "commit", "-m", f"Update kernel version to {version}"])
    subprocess.run(["git", "push"])

def check_for_new_version():
    latest_commit_message = get_latest_commit_message()
    if latest_commit_message:
        latest_version = extract_version_from_commit_message(latest_commit_message)
        if latest_version:
            stored_version = read_stored_version()
            if stored_version != latest_version:
                print(f"New version available: {latest_version}")
                write_stored_version(latest_version)
                commit_and_push_version(latest_version)
                return latest_version
            else:
                print("No new version available.")
        else:
            print("Failed to extract version from commit message.")
    else:
        print("Failed to fetch the latest commit message.")
    return None

def filter_new_commits(commits, stored_version):
    new_commits = []
    for commit in commits:
        commit_message = commit['commit']['message']
        print(f"Checking commit: {commit_message}")  # Log commit messages
        if stored_version not in commit_message:
            new_commits.append(commit)
        else:
            print(f"Stopping at commit: {commit_message}")  # Log the commit where we stop
            break
    return new_commits

if __name__ == "__main__":
    latest_version = check_for_new_version()
    if latest_version:
        clone_kernel_repo()
        success, _, _ = fetch_openela_commits()
        if success:
            openela_commits = get_latest_openela_commits()
            stored_version = read_stored_version()
            new_commits = filter_new_commits(openela_commits, stored_version)
            print(f"New commits to cherry-pick: {[commit['sha'] for commit in new_commits]}")  # Log new commits
            if new_commits:
                cherry_pick_openela_commits(new_commits)
            else:
                print("No new commits to cherry-pick.")
        else:
            print("Failed to fetch OpenELA commits.")
    else:
        # If there's no new version, ensure the VERSION_FILE is created if it doesn't exist
        if not os.path.exists(os.path.join(KERNEL_REPO_DIR, VERSION_FILE_PATH)):
            clone_kernel_repo()
            write_stored_version(read_stored_version())
