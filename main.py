import discord
import asyncio
import json
import logging
from discord.ext import commands

with open("config.json") as f:
    config = json.load(f)

token = config.get("Token")
prefix = config.get("Prefix")
delay = config.get("Delay")

bot = commands.Bot(command_prefix=prefix, self_bot=True)

auto_reaction_users = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@bot.event
async def on_message(message):
    if message.author.id in auto_reaction_users:
        emoji = auto_reaction_users[message.author.id]
        try:
            await message.add_reaction(emoji)
        except discord.errors.Forbidden:
            pass
    
    await bot.process_commands(message)

async def delete_after(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
        logger.info(f"Message {message.id} deleted successfully after {delay} seconds")
    except discord.errors.NotFound:
        logger.warning(f"Message {message.id} was already deleted")
    except discord.errors.Forbidden:
        logger.error(f"No permission to delete message {message.id}")
    except Exception as e:
        logger.error(f"Failed to delete message {message.id}: {str(e)}")

@bot.command()
async def removereaction(ctx, user: discord.User):
    if user.id in auto_reaction_users:
        del auto_reaction_users[user.id]
        msg = await ctx.send(f"Removed auto reaction for {user.mention}")
        asyncio.create_task(delete_after(msg, delay))
    else:
        msg = await ctx.send(f"{user.mention} was not in the reaction list")
        asyncio.create_task(delete_after(msg, delay))
    
    await ctx.message.delete()

@bot.command()
async def ping(ctx):
    await ctx.message.delete()
    msg = await ctx.send('pong')
    asyncio.create_task(delete_after(msg, delay))

@bot.command()
async def autoreact(ctx, user: discord.User, emoji: str):
    auto_reaction_users[user.id] = emoji
    await ctx.message.delete()
    msg = await ctx.send(f"Auto reacting with {emoji} for {user.mention}")
    asyncio.create_task(delete_after(msg, delay))

@bot.command()
async def purge(ctx, number: int):
    if number <= 0:
        await ctx.send("Please provide a positive number of messages to delete.")
        return

    def is_me(m):
        return m.author == bot.user
    try:
        await ctx.message.delete()
        channel = ctx.channel
        deleted = await channel.purge(limit=number, check=is_me)
        msg = await ctx.send(f"Deleted {len(deleted)} message(s).")
        bot.loop.create_task(delete_after(msg, 1))
        logger.info(f"Purged {len(deleted)} messages in {channel.name}")
    except discord.errors.Forbidden:
        logger.error(f"No permission to delete messages in {channel.name}")
        await ctx.send("I don't have permission to delete messages in this channel.")
    except Exception as e:
        logger.error(f"Failed to purge messages: {str(e)}")
        await ctx.send("An error occurred while trying to delete messages.")

bot.run(token)