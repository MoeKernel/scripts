#!/bin/bash

# -----------------------------
#   By Akari Nyan - © 2023
# ----------------------------- 

tag="stable"
remove_kprobes_warning="y"

while getopts "t:k:h" opt; do
  case $opt in
    t)
      tag="$OPTARG"
      ;;
    k)
      remove_kprobes_warning="$OPTARG"
      ;;
    h)
      echo "Use: ./ksu_update.sh [-t <tag>] [-k <remove warning KPROBES>] [-h]"
      echo ""
      echo "Options:"
      echo "  -t <tag> Selects the KernelSU tag. Options: stable (default), dev (unstable)"
      
      echo "  -k <remove warning KPROBES> Whether to remove. Options: y, n (y: default)"

      echo "  -h, --help Display this help message"
      exit 0
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

if [ "$tag" = "stable" ]; then
  rm -rf KernelSU
  cmd="bash -"
elif [ "$tag" = "dev" ]; then
  rm -rf KernelSU
  cmd="bash -s main"
else
  echo "Tag inválida: $tag" >&2
  exit 1
fi

curl -LSs "https://raw.githubusercontent.com/tiann/KernelSU/main/kernel/setup.sh" | $cmd

if [ "$remove_kprobes_warning" = "y" ]; then
  sed -i '59,60d' KernelSU/kernel/ksu.c
fi
