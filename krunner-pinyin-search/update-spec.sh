#!/bin/bash
# update-spec.sh - 本地更新 spec 文件

set -euo pipefail

SPEC_FILE="${1:-krunner-pinyin-search.spec}"
UPSTREAM_REPO="AOSC-Dev/krunner-pinyin-search"
UPSTREAM_BRANCH="master"

echo "🔍 Fetching latest commit from ${UPSTREAM_REPO}..."

# 获取最新 commit 信息
LATEST=$(curl -s "https://api.github.com/repos/${UPSTREAM_REPO}/commits?sha=${UPSTREAM_BRANCH}&per_page=1" | jq -r '.[0]')
FULL_HASH=$(echo "$LATEST" | jq -r '.sha')
SHORT_HASH=$(echo "$FULL_HASH" | cut -c1-7)
COMMIT_DATE=$(echo "$LATEST" | jq -r '.commit.author.date' | cut -d'T' -f1 | tr -d '-')
COMMIT_MSG=$(echo "$LATEST" | jq -r '.commit.message' | head -1)

echo "📦 Found: ${SHORT_HASH} (${COMMIT_DATE}) - ${COMMIT_MSG:0:50}..."

# 检查当前版本
CURRENT=$(grep "^%global git_commit " "$SPEC_FILE" | awk '{print $3}')
if [[ "$CURRENT" == "$FULL_HASH" ]]; then
  echo "✅ Already up to date!"
  exit 0
fi

echo "🔄 Updating ${SPEC_FILE}..."

# 备份
cp "$SPEC_FILE" "${SPEC_FILE}.bak"

# 更新变量
sed -i "s|^%global git_commit .*|%global git_commit ${FULL_HASH}|" "$SPEC_FILE"
sed -i "s|^%global git_short .*|%global git_short ${SHORT_HASH}|" "$SPEC_FILE"
sed -i "s|^%global commit_date .*|%global commit_date ${COMMIT_DATE}|" "$SPEC_FILE"

# 更新 changelog
CHANGELOG_DATE=$(date -d "$COMMIT_DATE" '+%a %b %d %Y')
CHANGELOG_ENTRY="* ${CHANGELOG_DATE} IkunJi <ikunji@duck.com> -${COMMIT_DATE}git${SHORT_HASH}
- Auto-update to upstream ${SHORT_HASH}: ${COMMIT_MSG}"

# 插入 changelog
awk -v entry="$CHANGELOG_ENTRY" '/^%changelog/ { print entry; print ""; } { print }' "$SPEC_FILE" > "${SPEC_FILE}.tmp"
mv "${SPEC_FILE}.tmp" "$SPEC_FILE"

echo "✅ Updated! Changes:"
git diff --no-index "${SPEC_FILE}.bak" "$SPEC_FILE" || true

echo ""
echo "💡 Next steps:"
echo "  1. Review changes: git diff ${SPEC_FILE}"
echo "  2. Commit: git add ${SPEC_FILE} && git commit -m 'chore(spec): update to ${SHORT_HASH}'"
echo "  3. Push and trigger COPR rebuild"