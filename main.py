import discord
from discord.ext import commands
import json
import re
import os
from flask import Flask
from threading import Thread

# Create a Flask app to keep the bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is online!"  # This is a simple endpoint to keep the bot alive

def run():
    app.run(host='0.0.0.0', port=80)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Setup for the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Your bot's commands go here
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Use the keep_alive function to keep the bot alive
keep_alive()



intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
donation_file = "donations.json"

# ========== Helper Functions ==========

def load_donations():
    if not os.path.exists(donation_file):
        with open(donation_file, "w") as f:
            json.dump({}, f)
    with open(donation_file, "r") as f:
        return json.load(f)

def save_donations(donations):
    with open(donation_file, "w") as f:
        json.dump(donations, f, indent=4)

def parse_gem_value(value):
    suffixes = {
        "k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12,
        "qa": 1e15, "qn": 1e18, "sx": 1e21, "sp": 1e24,
        "oc": 1e27, "no": 1e30,
        "q": 1e15, "qi": 1e18,
        "Q": 1e15, "QN": 1e18
    }
    match = re.match(r"([\d.]+)\s*([a-zA-Z]+)?", str(value).strip())
    if match:
        num = float(match.group(1))
        suffix = match.group(2).lower() if match.group(2) else ""
        return num * suffixes.get(suffix, 1)
    return float(value)

def format_gem_value(number):
    thresholds = [
        (1e30, "no"), (1e27, "oc"), (1e24, "sp"),
        (1e21, "sx"), (1e18, "qi"), (1e15, "qa"),
        (1e12, "t"), (1e9, "b"), (1e6, "m"), (1e3, "k")
    ]
    for threshold, suffix in thresholds:
        if number >= threshold:
            return f"{number / threshold:.2f}{suffix}"
    return f"{number:.2f}"

# ========== Commands ==========

@bot.command()
async def add(ctx, username: str, amount: str):
    donations = load_donations()
    amount_num = parse_gem_value(amount)
    key = username.lower()

    prev = donations.get(key, 0)
    donations[key] = prev + amount_num
    save_donations(donations)

    await ctx.send(f"✅ Added {format_gem_value(amount_num)} gems to {username}. New total: {format_gem_value(donations[key])}")

@bot.command()
async def update(ctx, username: str, amount: str):
    donations = load_donations()
    key = username.lower()
    donations[key] = parse_gem_value(amount)
    save_donations(donations)

    await ctx.send(f"🔄 Updated {username}'s donation to {format_gem_value(donations[key])} gems.")

@bot.command()
async def delete(ctx, username: str):
    donations = load_donations()
    key = username.lower()
    if key in donations:
        del donations[key]
        save_donations(donations)
        await ctx.send(f"🗑️ Deleted {username}'s donation record.")
    else:
        await ctx.send(f"❌ User {username} not found.")

@bot.command()
async def rollback(ctx, username: str, amount: str):
    donations = load_donations()
    key = username.lower()
    if key in donations:
        rollback_amount = parse_gem_value(amount)
        donations[key] = max(0, donations[key] - rollback_amount)
        save_donations(donations)
        await ctx.send(f"↩️ Rolled back {format_gem_value(rollback_amount)} from {username}. New total: {format_gem_value(donations[key])}")
    else:
        await ctx.send(f"❌ User {username} not found.")

@bot.command()
async def total(ctx):
    donations = load_donations()
    total_gems = sum(donations.values())
    await ctx.send(f"💎 Total gems donated across all users: {format_gem_value(total_gems)}")

@bot.command()
async def user(ctx, username: str = None):
    donations = load_donations()
    if username is None:
        username = str(ctx.author.display_name)

    key = username.lower()
    value = donations.get(key)

    if value is None:
        await ctx.send(f"❌ No gem donations found for {username}.")
    else:
        await ctx.send(f"💎 {username} has donated {format_gem_value(value)} gems!")

@bot.command(name="lb")
async def leaderboard(ctx, page: int = 1):
    donations = load_donations()

    if not donations:
        await ctx.send("📭 No donations found.")
        return

    sorted_donors = sorted(donations.items(), key=lambda x: x[1], reverse=True)
    per_page = 10
    total_pages = (len(sorted_donors) + per_page - 1) // per_page

    if page < 1 or page > total_pages:
        await ctx.send(f"❌ Invalid page number. Please choose between 1 and {total_pages}.")
        return

    start = (page - 1) * per_page
    end = start + per_page
    page_donors = sorted_donors[start:end]

    embed = discord.Embed(
        title=f"🏆 Gem Donation Leaderboard",
        description=f"Page **{page}** of **{total_pages}**\n\u200b",
        color=discord.Color.gold()
    )

    rank_emojis = ["🥇", "🥈", "🥉"]
    for idx, (user, gems) in enumerate(page_donors, start=start + 1):
        emoji = rank_emojis[idx - 1] if idx <= 3 else f"`#{idx}`"
        embed.add_field(
            name=f"{emoji} **{user}**",
            value=f"> 💎 **{format_gem_value(gems)}** gems\n\u200b",
            inline=False
        )

    embed.set_footer(text="Use !lb <page> to view more")
    await ctx.send(embed=embed)




# ========== Bot Startup ==========

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

bot.run("MTM2MDQwNDAxMjg1MTAwMzU4Mw.G7enHx.TTsF-xefplL6rzxPvA5teyfkfYL6_rPZuW1f38")
