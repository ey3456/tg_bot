# Telegram 多功能机器人

一个功能强大的 Telegram 机器人，集成记账、自动搬运、群发、自动回复等功能。

## 主要功能

### 💰 记账管理
- 记录日常支出
- 分类统计分析
- 查看历史记录
- 生成支出报表

### 🔄 自动搬运
- 频道/群组消息自动转发
- 支持关键词过滤
- 多目标转发
- 实时同步

### 🤖 自动回复
- 智能关键词匹配
- 自定义回复内容
- 支持中文关键词
- 24小时自动响应

### 📢 群发消息
- 一键群发通知
- 管理员专属功能
- 支持文字消息

### 💎 付费订阅
- 多种订阅套餐
- 功能分级管理
- 在线支付集成

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 获取 Bot Token

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按提示设置名称和用户名
4. 获取 API Token

### 3. 获取你的用户 ID

1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息
3. 获取你的 User ID

### 4. 配置机器人

编辑 `telegram_bot.py` 文件中的 `Config` 类：

```python
class Config:
    BOT_TOKEN = "你的机器人Token"
    ADMIN_ID = 你的用户ID
    DB_PATH = "bot_data.db"
```

### 5. 运行机器人

```bash
python telegram_bot.py
```

## 使用指南

### 基础命令

- `/start` - 启动机器人
- `/help` - 查看帮助
- `/menu` - 显示功能菜单

### 记账功能

```bash
# 添加支出
/addexpense 餐饮 50 午餐

# 查看记录
/expenses

# 查看统计
/stats
```

### 搬运功能

```bash
# 添加搬运规则（需要管理员权限）
/addforward -100123456789 -100987654321

# 查看配置
/listforward
```

**获取频道/群组 ID：**
1. 将机器人添加到频道/群组
2. 转发一条消息给 `@userinfobot`
3. 获取 Chat ID

### 自动回复

```bash
# 添加自动回复
/addreply 你好 | 您好！有什么可以帮您的？

# 查看所有回复
/listreply
```

### 群发消息

```bash
# 群发消息（仅管理员）
/broadcast 大家好！这是一条群发消息
```

### 订阅服务

```bash
# 查看价格
/pricing

# 订阅
/subscribe
```

## 功能说明

### 记账系统
- 支持多种支出分类
- 自动生成时间戳
- SQLite 数据库存储
- 按用户隔离数据

### 搬运系统
- 支持频道到频道
- 支持群组到群组
- 支持关键词过滤
- 实时转发消息

### 自动回复
- 关键词模糊匹配
- 支持多条回复规则
- 可启用/禁用规则

### 数据存储
所有数据存储在 `bot_data.db` SQLite 数据库中，包括：
- 支出记录
- 搬运配置
- 自动回复规则
- 用户订阅信息

## 数据库结构

### expenses（支出表）
- id: 主键
- user_id: 用户ID
- category: 分类
- amount: 金额
- description: 描述
- date: 日期时间

### forward_config（搬运配置表）
- id: 主键
- source_chat_id: 源频道/群组ID
- target_chat_ids: 目标ID列表（JSON）
- keywords: 关键词列表（JSON）
- enabled: 是否启用

### auto_replies（自动回复表）
- id: 主键
- keyword: 关键词
- reply: 回复内容
- enabled: 是否启用

### subscriptions（订阅表）
- id: 主键
- user_id: 用户ID
- plan: 订阅套餐
- expiry_date: 到期日期

## 进阶配置

### 添加更多管理员

```python
ADMIN_IDS = [123456789, 987654321]  # 多个管理员ID

# 在权限检查中修改
if update.effective_user.id not in ADMIN_IDS:
    return
```

### 自定义数据库路径

```python
Config.DB_PATH = "/path/to/your/database.db"
```

### 添加日志记录

```python
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

## 商业应用

### 赚钱方式

1. **付费订阅**
   - 基础版：免费
   - 专业版：¥29/月
   - 企业版：¥99/月

2. **增值服务**
   - 定制开发
   - 数据分析报告
   - 专属客服支持

3. **广告推广**
   - 群发广告消息
   - 频道推广服务

### 支付集成

可以集成以下支付方式：
- 支付宝
- 微信支付
- Telegram Payment（内置支付）
- 加密货币支付

## 注意事项

⚠️ **重要提示：**

1. **Token 安全**
   - 不要公开分享 Bot Token
   - 不要将 Token 提交到 Git

2. **频率限制**
   - Telegram 有 API 调用限制
   - 群发消息不要过于频繁

3. **隐私保护**
   - 妥善保管用户数据
   - 遵守 GDPR 等隐私法规

4. **合规使用**
   - 遵守 Telegram 使用条款
   - 不发送垃圾信息
   - 不进行违法活动

## 常见问题

**Q: 如何获取频道 ID？**
A: 将机器人添加到频道，转发频道消息给 @userinfobot

**Q: 搬运功能不工作？**
A: 确保机器人在源频道和目标频道都是管理员

**Q: 如何备份数据？**
A: 定期备份 `bot_data.db` 文件

**Q: 支持多语言吗？**
A: 当前版本仅支持中文，可自行修改代码支持多语言

## 更新日志

### v1.0.0 (2025-01-23)
- ✨ 初始版本发布
- ✅ 记账功能
- ✅ 自动搬运
- ✅ 自动回复
- ✅ 群发消息
- ✅ 订阅系统

## 技术支持

如有问题或建议，欢迎联系：
- Telegram: @your_admin
- Email: support@example.com

## 开源协议

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**祝你使用愉快！💪**
