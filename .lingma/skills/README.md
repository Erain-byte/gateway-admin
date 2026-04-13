# Skills 使用说明

## 📋 概述

Skills 是 Lingma AI 助手的知识库，用于确保开发过程中遵循项目的架构规范和最佳实践。

---

## 🎯 当前可用的 Skills

### 1. 微服务架构开发规范 (`microservice-architecture.md`)

**用途**：确保所有微服务相关的开发遵循统一的架构规范

**适用场景**：
- ✅ 新增后端服务（Admin/User/Order 等）
- ✅ 修改 Gateway 路由或中间件
- ✅ 实现 HMAC 签名验证逻辑
- ✅ 配置服务发现和注册
- ✅ 前端集成 HMAC 签名
- ✅ 密钥管理和轮换

**核心内容**：
1. **API Gateway 模式** - 统一入口原则
2. **HMAC 签名验证机制** - 双层验证架构
3. **服务发现与注册** - 3级缓存策略
4. **零信任安全策略** - 来源验证
5. **多层防护体系** - 6层安全防护
6. **开发规范** - 代码示例和最佳实践
7. **常见错误** - 避免方法

**使用方式**：
```
当进行微服务开发时，AI 助手会自动参考此 Skill，确保：
- Gateway 使用目标服务的密钥签名
- 后端服务使用自己的密钥验证
- 前端只使用 Gateway 的密钥
- 遵循 Redis + Consul 双写策略
```

---

## 📁 Skills 目录结构

```
.lingma/
└── skills/
    └── microservice-architecture.md  # 微服务架构规范
```

---

## 🔄 如何更新 Skills

### 何时需要更新？

1. **架构变更** - 例如引入新的认证机制
2. **新增规范** - 例如添加日志规范
3. **修正错误** - 发现文档中的错误或不一致
4. **最佳实践更新** - 基于实际开发经验优化

### 更新步骤

1. **编辑 Skill 文件**
   ```bash
   # 直接编辑 markdown 文件
   code .lingma/skills/microservice-architecture.md
   ```

2. **添加版本历史**
   ```markdown
   ## 🔄 版本历史
   
   - **v1.1** (2026-04-XX) - 更新内容描述
     - 具体变更点 1
     - 具体变更点 2
   ```

3. **提交到 Git**
   ```bash
   git add .lingma/skills/microservice-architecture.md
   git commit -m "docs: 更新微服务架构规范 v1.1"
   ```

---

## 💡 最佳实践

### 1. 保持 Skills 简洁明了

- ✅ 使用清晰的标题和列表
- ✅ 提供完整的代码示例
- ✅ 标注常见错误和避免方法
- ❌ 避免冗长的理论描述

### 2. 定期审查和更新

- 📅 每次重大架构变更后更新
- 📅 每季度审查一次 Skills 的有效性
- 📅 收集团队反馈，持续改进

### 3. 与文档保持一致

- ✅ Skills 应该是对架构文档的精炼总结
- ✅ 关键规范应该在 Skills 和文档中保持一致
- ✅ Skills 侧重于"如何做"，文档侧重于"为什么"

### 4. 提供可执行的示例

```python
# ✅ 好的示例：完整、可运行
async def verify_hmac(request: Request, service_name: str):
    hmac_key = await redis.get(f"config:hmac:{service_name}")
    if not hmac_key:
        raise KeyError(f"HMAC key not found for {service_name}")
    
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    
    return verify_signature(signature, request.method, request.url.path, 
                           await request.body(), timestamp, hmac_key)

# ❌ 不好的示例：缺少上下文
def verify():
    pass
```

---

## 🎓 如何让 AI 助手使用 Skills

### 自动触发

AI 助手会在以下场景自动参考 Skills：
- 检测到关键词（如 "HMAC"、"服务注册"、"Gateway"）
- 用户明确要求遵循架构规范
- 生成代码时检查是否符合规范

### 手动引用

用户可以在对话中明确引用 Skill：
```
请根据 microservice-architecture skill 实现一个新的用户服务
```

或者：
```
按照架构规范添加 HMAC 签名验证
```

---

## 📊 Skills 效果评估

### 评估指标

1. **代码一致性** - 生成的代码是否遵循架构规范
2. **错误率** - 是否减少了常见错误
3. **开发效率** - 是否加快了开发速度
4. **团队满意度** - 团队成员是否觉得有用

### 收集反馈

- 记录 AI 助手犯的错误
- 收集团队成员的使用体验
- 定期回顾 Skills 的有效性

---

## 🔮 未来扩展

### 计划添加的 Skills

1. **数据库设计规范** (`database-design.md`)
   - MySQL 表设计规范
   - 索引优化策略
   - 迁移脚本规范

2. **API 设计规范** (`api-design.md`)
   - RESTful API 设计原则
   - 错误码规范
   - 分页和过滤规范

3. **测试规范** (`testing.md`)
   - 单元测试编写规范
   - 集成测试策略
   - Mock 数据管理

4. **日志规范** (`logging.md`)
   - 日志级别使用规范
   - 结构化日志格式
   - 敏感信息脱敏

5. **部署规范** (`deployment.md`)
   - Docker 镜像构建规范
   - Kubernetes 配置模板
   - CI/CD 流程

---

## 📞 问题与支持

如果在使用 Skills 过程中遇到问题：

1. **检查 Skill 文件** - 确认内容是否正确
2. **查看版本历史** - 了解最近的变更
3. **联系维护者** - 提出改进建议

---

**最后更新**: 2026-04-13  
**维护者**: Development Team
