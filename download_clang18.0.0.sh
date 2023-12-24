#!/bin/bash

# -----------------------------
#   By Akari Nyan - © 2023
# ----------------------------- 

version="Clang-18.0.0git-20231224-release"
clang_gz="Clang-18.0.0git-20231224.tar.gz"
url="https://github.com/ZyCromerZ/Clang/releases/download/$version/$clang_gz"
destination_dir="$HOME/tc/clang-18.0.0"

if ! command -v curl &>/dev/null; then
  echo "The command 'curl' not installed. Please, install for continue."
  sudo apt update -y 
  sudo apt install curl -y
  exit 1
fi

curl -LO "$url"

if [ $? -ne 0 ]; then
  echo "The download of the archive has failed."
  exit 1
fi

mkdir -p "$destination_dir"
tar -xzf "$output_file" -C "$destination_dir"

if [ $? -eq 0 ]; then
  echo "Archive extracted with success in '$destination_dir'."
else
  echo "The extraction of the zip was failed!"
fi
