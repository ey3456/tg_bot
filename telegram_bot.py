import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.error import TelegramError
import sqlite3

# 配置文件
class Config:
    BOT_TOKEN = "8277055162:AAHaHgp0_gqx4D1sHCtnCecUmXRlyNMfyRg"  # 替换为你的机器人 Token
    ADMIN_ID = 640311536  # 替换为你的 Telegram 用户 ID
    DB_PATH = "bot_data.db"

# 数据库管理
class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 记账表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                amount REAL,
                description TEXT,
                date TEXT
            )
        ''')
        
        # 搬运配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forward_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_chat_id INTEGER,
                target_chat_ids TEXT,
                keywords TEXT,
                enabled INTEGER DEFAULT 1
            )
        ''')
        
        # 自动回复表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                reply TEXT,
                enabled INTEGER DEFAULT 1
            )
        ''')
        
        # 用户订阅表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                plan TEXT,
                expiry_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_expense(self, user_id: int, category: str, amount: float, description: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, category, amount, description, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, category, amount, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
    
    def get_expenses(self, user_id: int, limit: int = 10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?",
            (user_id, limit)
        )
        result = cursor.fetchall()
        conn.close()
        return result
    
    def add_forward_config(self, source_id: int, target_ids: List[int], keywords: List[str] = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO forward_config (source_chat_id, target_chat_ids, keywords) VALUES (?, ?, ?)",
            (source_id, json.dumps(target_ids), json.dumps(keywords or []))
        )
        conn.commit()
        conn.close()
    
    def get_forward_configs(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM forward_config WHERE enabled = 1")
        result = cursor.fetchall()
        conn.close()
        return result
    
    def add_auto_reply(self, keyword: str, reply: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO auto_replies (keyword, reply) VALUES (?, ?)",
            (keyword, reply)
        )
        conn.commit()
        conn.close()
    
    def get_auto_replies(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT keyword, reply FROM auto_replies WHERE enabled = 1")
        result = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in result}

# 机器人类
class TelegramBot:
    def __init__(self):
        self.db = Database(Config.DB_PATH)
        self.app = Application.builder().token(Config.BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        # 命令处理器
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("menu", self.menu))
        
        # 记账功能
        self.app.add_handler(CommandHandler("addexpense", self.add_expense))
        self.app.add_handler(CommandHandler("expenses", self.view_expenses))
        self.app.add_handler(CommandHandler("stats", self.expense_stats))
        
        # 搬运功能
        self.app.add_handler(CommandHandler("addforward", self.add_forward))
        self.app.add_handler(CommandHandler("listforward", self.list_forward))
        
        # 自动回复功能
        self.app.add_handler(CommandHandler("addreply", self.add_reply))
        self.app.add_handler(CommandHandler("listreply", self.list_replies))
        
        # 群发功能
        self.app.add_handler(CommandHandler("broadcast", self.broadcast))
        
        # 赚钱功能
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("pricing", self.pricing))
        
        # 消息处理器
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        welcome_text = f"""
👋 欢迎使用多功能 Telegram 机器人！

你好 {user.first_name}！

🎯 主要功能：
• 💰 记账管理
• 🔄 频道/群组自动搬运
• 📢 群发消息
• 🤖 自动回复
• 💎 付费订阅服务

使用 /menu 查看功能菜单
使用 /help 查看详细帮助
        """
        await update.message.reply_text(welcome_text)
    
    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("💰 记账", callback_data="menu_expense")],
            [InlineKeyboardButton("🔄 搬运设置", callback_data="menu_forward")],
            [InlineKeyboardButton("🤖 自动回复", callback_data="menu_reply")],
            [InlineKeyboardButton("📢 群发消息", callback_data="menu_broadcast")],
            [InlineKeyboardButton("💎 订阅服务", callback_data="menu_subscribe")],
            [InlineKeyboardButton("❓ 帮助", callback_data="menu_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("请选择功能：", reply_markup=reply_markup)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "menu_expense":
            text = """
💰 记账功能

命令：
/addexpense <类别> <金额> <描述>
例：/addexpense 餐饮 50 午餐

/expenses - 查看最近支出
/stats - 查看统计数据
            """
            await query.edit_message_text(text)
        
        elif query.data == "menu_forward":
            text = """
🔄 自动搬运功能

命令：
/addforward <源频道ID> <目标频道ID>
例：/addforward -100123456 -100789012

/listforward - 查看搬运配置
            """
            await query.edit_message_text(text)
        
        elif query.data == "menu_reply":
            text = """
🤖 自动回复功能

命令：
/addreply <关键词> | <回复内容>
例：/addreply 你好 | 您好！有什么可以帮您的？

/listreply - 查看所有自动回复
            """
            await query.edit_message_text(text)
        
        elif query.data == "menu_broadcast":
            text = """
📢 群发消息功能

命令：
/broadcast <消息内容>

注：仅管理员可用
            """
            await query.edit_message_text(text)
        
        elif query.data == "menu_subscribe":
            await self.pricing(update, context)
        
        elif query.data == "menu_help":
            await self.help_command(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📖 详细帮助文档

【记账功能】
/addexpense <类别> <金额> <描述> - 添加支出
/expenses - 查看最近10条记录
/stats - 查看统计分析

【搬运功能】
/addforward <源ID> <目标ID> - 添加搬运规则
/listforward - 查看所有搬运配置

【自动回复】
/addreply <关键词> | <回复> - 添加自动回复
/listreply - 查看所有回复规则

【群发功能】
/broadcast <内容> - 群发消息（管理员）

【订阅服务】
/pricing - 查看价格方案
/subscribe - 订阅服务

💡 提示：
• 频道ID可通过 @userinfobot 获取
• 支持中文关键词自动回复
• 记账支持多种分类统计
        """
        if update.message:
            await update.message.reply_text(help_text)
        else:
            await update.callback_query.edit_message_text(help_text)
    
    # 记账功能
    async def add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            args = context.args
            if len(args) < 3:
                await update.message.reply_text("❌ 格式错误！\n使用: /addexpense <类别> <金额> <描述>")
                return
            
            category = args[0]
            amount = float(args[1])
            description = " ".join(args[2:])
            
            self.db.add_expense(update.effective_user.id, category, amount, description)
            
            await update.message.reply_text(
                f"✅ 记账成功！\n\n"
                f"类别: {category}\n"
                f"金额: ¥{amount:.2f}\n"
                f"描述: {description}"
            )
        except ValueError:
            await update.message.reply_text("❌ 金额格式错误！请输入数字。")
        except Exception as e:
            await update.message.reply_text(f"❌ 记账失败: {str(e)}")
    
    async def view_expenses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        expenses = self.db.get_expenses(update.effective_user.id)
        
        if not expenses:
            await update.message.reply_text("📊 暂无支出记录")
            return
        
        text = "📊 最近支出记录：\n\n"
        for exp in expenses:
            text += f"• {exp[5]} | {exp[2]} | ¥{exp[3]:.2f}\n  {exp[4]}\n\n"
        
        await update.message.reply_text(text)
    
    async def expense_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # 总支出
        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE user_id = ?",
            (update.effective_user.id,)
        )
        total = cursor.fetchone()[0] or 0
        
        # 分类统计
        cursor.execute(
            "SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category",
            (update.effective_user.id,)
        )
        categories = cursor.fetchall()
        conn.close()
        
        text = f"📈 支出统计\n\n总支出: ¥{total:.2f}\n\n分类明细:\n"
        for cat, amt in categories:
            percentage = (amt / total * 100) if total > 0 else 0
            text += f"• {cat}: ¥{amt:.2f} ({percentage:.1f}%)\n"
        
        await update.message.reply_text(text)
    
    # 搬运功能
    async def add_forward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != Config.ADMIN_ID:
            await update.message.reply_text("❌ 仅管理员可用此功能")
            return
        
        try:
            args = context.args
            if len(args) < 2:
                await update.message.reply_text("❌ 格式: /addforward <源ID> <目标ID>")
                return
            
            source_id = int(args[0])
            target_id = int(args[1])
            
            self.db.add_forward_config(source_id, [target_id])
            await update.message.reply_text(f"✅ 搬运配置已添加\n源: {source_id}\n目标: {target_id}")
        except ValueError:
            await update.message.reply_text("❌ ID格式错误！")
    
    async def list_forward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        configs = self.db.get_forward_configs()
        
        if not configs:
            await update.message.reply_text("📋 暂无搬运配置")
            return
        
        text = "📋 搬运配置列表：\n\n"
        for config in configs:
            targets = json.loads(config[2])
            text += f"源: {config[1]}\n目标: {', '.join(map(str, targets))}\n\n"
        
        await update.message.reply_text(text)
    
    # 自动回复功能
    async def add_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            text = update.message.text.replace("/addreply ", "")
            if "|" not in text:
                await update.message.reply_text("❌ 格式: /addreply 关键词 | 回复内容")
                return
            
            keyword, reply = text.split("|", 1)
            keyword = keyword.strip()
            reply = reply.strip()
            
            self.db.add_auto_reply(keyword, reply)
            await update.message.reply_text(f"✅ 自动回复已添加\n关键词: {keyword}")
        except Exception as e:
            await update.message.reply_text(f"❌ 添加失败: {str(e)}")
    
    async def list_replies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        replies = self.db.get_auto_replies()
        
        if not replies:
            await update.message.reply_text("📋 暂无自动回复规则")
            return
        
        text = "📋 自动回复列表：\n\n"
        for keyword, reply in replies.items():
            text += f"• {keyword}\n  → {reply}\n\n"
        
        await update.message.reply_text(text)
    
    # 群发功能
    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != Config.ADMIN_ID:
            await update.message.reply_text("❌ 仅管理员可用此功能")
            return
        
        message = " ".join(context.args)
        if not message:
            await update.message.reply_text("❌ 请输入要群发的消息")
            return
        
        # 这里需要实现获取所有用户的逻辑
        await update.message.reply_text(f"📢 群发消息：\n{message}\n\n（实际群发需配置用户列表）")
    
    # 订阅功能
    async def pricing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
💎 订阅服务价格

【基础版】免费
• 基础记账功能
• 最多3条自动回复

【专业版】¥29/月
• 无限记账记录
• 无限自动回复
• 最多5个搬运配置
• 优先客服支持

【企业版】¥99/月
• 所有专业版功能
• 无限搬运配置
• 群发消息功能
• API接口访问
• 专属客服

联系管理员订阅: @your_admin
        """
        
        if update.message:
            await update.message.reply_text(text)
        else:
            await update.callback_query.edit_message_text(text)
    
    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "💎 订阅服务\n\n"
            "请联系管理员完成订阅：@your_admin\n"
            "支付后发送订单号即可开通服务。"
        )
    
    # 消息处理
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 自动回复
        message_text = update.message.text.lower()
        replies = self.db.get_auto_replies()
        
        for keyword, reply in replies.items():
            if keyword.lower() in message_text:
                await update.message.reply_text(reply)
                return
        
        # 搬运功能
        if update.message.chat.type in ["group", "supergroup", "channel"]:
            await self.handle_forward(update, context)
    
    async def handle_forward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        configs = self.db.get_forward_configs()
        source_chat_id = update.message.chat.id
        
        for config in configs:
            if config[1] == source_chat_id:
                target_ids = json.loads(config[2])
                keywords = json.loads(config[3])
                
                # 如果设置了关键词过滤
                if keywords:
                    message_text = update.message.text or ""
                    if not any(kw in message_text for kw in keywords):
                        continue
                
                # 转发到目标群组
                for target_id in target_ids:
                    try:
                        await context.bot.forward_message(
                            chat_id=target_id,
                            from_chat_id=source_chat_id,
                            message_id=update.message.message_id
                        )
                    except TelegramError as e:
                        print(f"转发失败: {e}")
    
    def run(self):
        print("🤖 机器人启动中...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

# 主程序
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════╗
║   Telegram 多功能机器人               ║
║   功能：记账/搬运/群发/自动回复         ║
╚══════════════════════════════════════════╝

⚙️  配置说明：
1. 在 Config 类中设置 BOT_TOKEN
2. 设置 ADMIN_ID（你的 Telegram 用户 ID）
3. 运行程序

📝 获取 Bot Token：
   与 @BotFather 对话创建机器人

🆔 获取用户 ID：
   与 @userinfobot 对话查看
    """)
    
    bot = TelegramBot()
    bot.run()
