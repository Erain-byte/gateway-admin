---
name: git-commit
description: 智能生成 Git 提交信息，遵循约定式提交规范
version: 1.0.0
tags: [git, commit, version-control]
---

# Git Commit Skill

## 触发条件

当用户：
- 请求生成 Git 提交信息
- 执行 `/commit` 命令
- 询问如何提交代码
- 查看 git status 后想要提交

## 执行步骤

### 1. 检查 Git 状态

首先运行：
```bash
git status
git diff --cached
```

了解哪些文件被修改、添加或删除。

### 2. 分析变更内容

根据文件变更，判断提交类型：

**类型映射**:
- `feat:` - 新功能
- `fix:` - 修复 bug
- `docs:` - 文档更新
- `style:` - 代码格式（不影响功能）
- `refactor:` - 重构
- `perf:` - 性能优化
- `test:` - 测试相关
- `chore:` - 构建过程或辅助工具变动
- `ci:` - CI/CD 配置更改

### 3. 生成提交信息

**格式**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**规则**:
- subject 不超过 50 字符
- body 每行不超过 72 字符
- 使用祈使语气（"add" 而非 "added"）
- 首字母小写
- 结尾不加句号

### 4. 提供提交建议

根据变更内容，生成 2-3 个提交信息选项供用户选择。

## 示例

### 示例 1: 新功能

**变更**: 添加了用户认证模块

**生成的提交信息**:
```
feat(auth): add JWT authentication

- Implement login endpoint
- Add JWT token generation
- Create auth middleware
- Add password hashing

Closes #123
```

### 示例 2: Bug 修复

**变更**: 修复了数据库连接超时问题

**生成的提交信息**:
```
fix(database): resolve connection timeout issue

Increase connection pool size and add retry logic
for database connections to handle high load scenarios.

Fixes #456
```

### 示例 3: 文档更新

**变更**: 更新了 README 和 API 文档

**生成的提交信息**:
```
docs: update README and API documentation

- Add installation instructions
- Update API examples
- Fix typos in configuration section
```

## 最佳实践

### ✅ 推荐

```bash
# 好的提交信息
feat(api): add user profile endpoint
fix(auth): handle expired tokens correctly
docs(readme): add quick start guide
```

### ❌ 避免

```bash
# 不好的提交信息
update files
fix bug
wip
asdf
```

## 自动化脚本

可以创建 `.git/hooks/commit-msg` hook：

```bash
#!/bin/sh

commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")

# 检查是否符合约定式提交规范
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|perf|test|chore|ci)(\(.+\))?: .+"; then
    echo "❌ 提交信息不符合约定式提交规范"
    echo "格式: <type>(<scope>): <subject>"
    echo "例如: feat(auth): add login endpoint"
    exit 1
fi

echo "✅ 提交信息格式正确"
```

## 常用命令

```bash
# 查看提交历史
git log --oneline

# 查看详细信息
git log --pretty=format:"%h - %an, %ar : %s"

# 统计提交
git shortlog -sn

# 交互式变基（整理提交历史）
git rebase -i HEAD~5
```

## 与 Agent 交互

**用户**: "帮我生成一个提交信息"

**Agent**:
1. 运行 `git status` 和 `git diff`
2. 分析变更内容
3. 生成 2-3 个提交信息选项
4. 询问用户选择哪个
5. 执行 `git commit -m "..."`

**输出示例**:
```
检测到以下变更:
- 新增: app/api/users.py (用户管理 API)
- 修改: app/models/user.py (添加邮箱字段)
- 删除: app/legacy/auth.py (旧认证模块)

建议的提交信息:

1️⃣  feat(user): add user management API
   
   - Create CRUD endpoints for users
   - Add email field to User model
   - Remove legacy authentication module

2️⃣  feat(api): implement user management with email support
   
   Comprehensive user management feature including
   email validation and legacy code cleanup.

请选择 (1/2) 或输入自定义提交信息:
```

