#!/bin/bash

export CHAT_ID="${CHAT_ID:-}"
export API_ID="${API_ID:-}"
export API_HASH="${API_HASH:-}"
export BOT_TOKEN="${BOT_TOKEN:-}"

if [[ -z "$CHAT_ID" || -z "$API_ID" || -z "$API_HASH" || -z "$BOT_TOKEN" ]]; then
    echo "Erro: Variáveis de ambiente não foram definidas corretamente."
    exit 1
fi

if [[ -f "build_count.txt" ]]; then
    build_count=$(cat build_count.txt)
else
    build_count=0
fi
build_count=$((build_count + 1))
echo $build_count > build_count.txt

commit_head=$(git log --oneline -1 --pretty=format:'%h - %an')
commit_id=$(git log --oneline -1 --pretty=format:'%h')
author_name=$(echo $commit_head | cut -d ' ' -f 3-)
commit_hash=$(echo $commit_head | cut -d ' ' -f 1)
kernel_version=$(make kernelversion 2>/dev/null)
build_type="release"
tag="ginkgo_${commit_hash:0:7}_$(date +%Y%m%d)"

start_message=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    -d chat_id=$CHAT_ID \
    -d text="Compilation started... please wait." \
    -d parse_mode="Markdown")

start_time=$(date +%s)

./ksu_update.sh -t stable
./moe.sh

if [[ $? -eq 0 ]]; then
    commit_head=$(git log --oneline -1 --pretty=format:'%h - %an')
    commit_id=$(git log --oneline -1 --pretty=format:'%h')
    author_name=$(echo $commit_head | cut -d ' ' -f 3-)
    commit_hash=$(echo $commit_head | cut -d ' ' -f 1)
    
    message_commit=$(git log --oneline -1 | cut -d ' ' -f 2-)
    commit_text=$message_commit
    commit_link="<a href=\"https://github.com/MoeKernel/android_kernel_xiaomi_ginkgo/commit/$commit_hash\">$commit_head</a>"

    end_time=$(date +%s)
    elapsed_time=$((end_time - start_time))
    elapsed_minutes=$((elapsed_time / 60))
    elapsed_seconds=$((elapsed_time % 60))
    elapsed_minutes_formatted=$(printf "%.2f" $(echo "$elapsed_minutes + $elapsed_seconds / 60" | bc -l))

    completion_message="\nCompleted in $elapsed_minutes_formatted minute(s) and $elapsed_seconds second(s)!"
    completed_compile_text="**Compilation completed!**\n\nCommit: $commit_link\n$completion_message"

    build_info="**ginkgo build (#$build_count) has succeeded**\n" \
               "**Kernel Version**: $kernel_version\n" \
               "**Build Type**: $build_type **(KSU/Fourteen)**\n" \
               "**Tag**: $tag\n" \
               "\n" \
               "**Duration**: $elapsed_minutes Minutes $elapsed_seconds Seconds\n" \
               "\n@MoeKernel #ginkgo #ksu"

    message_id=$(echo $start_message | jq .result.message_id)
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/editMessageText" \
        -d chat_id=$CHAT_ID \
        -d message_id=$message_id \
        -d text="$completed_compile_text" \
        -d parse_mode="Markdown"

    zip_file=$(ls *.zip | head -n 1)
    if [[ -n "$zip_file" ]]; then
        caption="**Build Information**\n • **Commit**: \`$commit_id\`\n • **Message**: \`$commit_text\`\n • **Author**: \`$author_name\`"

        curl -s -F chat_id=$CHAT_ID \
            -F document=@"$zip_file" \
            -F caption="$caption" \
            -F parse_mode="Markdown" \
            "https://api.telegram.org/bot$BOT_TOKEN/sendDocument"
    fi

    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d chat_id="@MoeNyanCI" \
        -d text="$build_info" \
        -d parse_mode="Markdown"

    exit 0
else
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d chat_id=$CHAT_ID \
        -d text="No zip files found in the current directory." \
        -d parse_mode="Markdown"
    exit 1
fi

echo "bot is running..."
