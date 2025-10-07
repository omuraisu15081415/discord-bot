import os
from threading import Thread

from flask import Flask
from dotenv import load_dotenv
import discord
from discord.ext import commands

# --- .env を読み込む ---
load_dotenv()

# --- Flaskによる keep-alive サーバー ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    # Render が割り当てる PORT を使う（重要）
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
# --- ここまで ---

# --- トークンを .env から取得 ---
TOKEN = os.getenv("DISCORD_TOKEN")

# --- Intents 設定 ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 👀マーク（Unicode形式）
EYE_EMOJI = "\U0001F440"

# 監視対象メッセージ / チャンネル（必要なら数値型に）
TARGET_MESSAGE_ID = 1424867146386767883
TARGET_CHANNEL_ID = 1424866996771623094


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("👀 Reaction bot is ready!")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != TARGET_MESSAGE_ID:
        return
    if str(payload.emoji) != EYE_EMOJI:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None or member.bot:
        return

    if member.id == guild.owner_id:
        print(f"{member.name} はオーナーのため、ニックネーム変更をスキップしました。")
        return

    try:
        if not member.display_name.startswith(EYE_EMOJI):
            new_name = f"{EYE_EMOJI} {member.display_name}"
            await member.edit(nick=new_name)
    except discord.Forbidden:
        print("⚠️ 権限不足：BOTにメンバーのニックネームを変更する権限がありません。")


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != TARGET_MESSAGE_ID:
        return
    if str(payload.emoji) != EYE_EMOJI:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None or member.bot:
        return

    try:
        if member.display_name.startswith(EYE_EMOJI):
            new_name = member.display_name.replace(EYE_EMOJI + " ", "")
            await member.edit(nick=new_name)
    except discord.Forbidden:
        print("⚠️ 権限不足：BOTにメンバーのニックネームを変更する権限がありません。")


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None and after.channel is None:
        print(f"{member.display_name} がVCを退出しました。")

        if member.id == member.guild.owner_id:
            print(f"{member.name} はオーナーのため、👀リアクション削除をスキップします。")
            return

        if member.display_name.startswith(EYE_EMOJI):
            try:
                new_name = member.display_name.replace(EYE_EMOJI + " ", "")
                await member.edit(nick=new_name)
            except discord.Forbidden:
                print("⚠️ 権限不足：BOTにメンバーのニックネームを変更する権限がありません。")

        print("👀リアクション削除を試行中…")
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if channel:
            try:
                message = await channel.fetch_message(TARGET_MESSAGE_ID)
                for reaction in message.reactions:
                    if str(reaction.emoji) == EYE_EMOJI:
                        async for user in reaction.users():
                            if user.id == member.id:
                                await reaction.remove(user)
                                print(f"👀リアクションを {member.display_name} から削除しました。")
            except Exception as e:
                print(f"⚠️ リアクション削除中にエラー: {e}")


# --- Bot 起動 ---
if TOKEN is None:
    print("❌ エラー: .env に DISCORD_TOKEN が設定されていません。")
else:
    keep_alive()  # Render がヘルスチェックするための Flask を起動
    bot.run(TOKEN)