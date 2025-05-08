#!/usr/bin/env python3
"""Main entry point for the Discord invite tracker bot.
Integrates all components and handles Discord events.
"""

import os

import discord

from config import TOKEN
from invite.db import get_inviter_invitees, insert_row
from invite.rawapi import get_member
from utils import logger

# Bot setup
bot = discord.Bot(
    allowed_mentions=discord.AllowedMentions.none(),
    intents=discord.Intents.none()
    | discord.Intents.message_content
    | discord.Intents.guilds
    | discord.Intents.guild_messages,
)

TRACKED_GUILD = os.environ["TRACKED_GUILD"]
assert TRACKED_GUILD
ALERT_CHANNEL = os.environ["ALERT_CHANNEL"]
assert ALERT_CHANNEL


@bot.event
async def on_ready() -> None:
    """Called when the bot is ready.
    Initializes database.
    """
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

    try:
        # Start random drop task
        await bot.wait_until_ready()
        logger.info("Bot is fully initialized and ready")
    except Exception as e:
        logger.error(f"Error during initialization: {e}")


@bot.listen("on_message")
async def on_text_message(message) -> None:
    """Processes incoming messages.

    Args:
        message: Discord message

    """
    # Ignore bot messages and DMs
    if message.author.bot or not isinstance(message.author, discord.member.Member):
        return

    try:
        if "!invited" in message.clean_content:
            mapping = get_inviter_invitees(TRACKED_GUILD)
            invited = mapping.get(message.author.id, [])
            if invited:
                names = " ".join(f"<@{i}>" for i in invited)
                await message.reply(f"You invited {len(invited)} people!\n{names}")
            else:
                await message.reply(
                    "You haven't invited anyone yet (at least since 2024..)",
                )
        if "!topinvites" in message.clean_content:
            mapping = get_inviter_invitees(TRACKED_GUILD)
            pos = 0
            emojis = ["🥇", "🥈", "🥉"]
            output = []
            for user, invited in sorted(
                mapping.items(), key=lambda item: len(item[1]), reverse=True,
            ):
                try:
                    prefix = emojis[pos]
                except IndexError:
                    prefix = f"**#{pos + 1}**"

                output.append(f"{prefix} <@{user}>: {len(invited)}")
                pos += 1
                if len(output) >= 10:
                    break

            output = "\n".join(output)
            await message.reply(f"## Leaderboard\n{output}")

            return

    except Exception as e:
        logger.exception(f"Error processing message: {e}")


@bot.listen("on_member_join")
async def on_member_join(member: discord.Member) -> None:
    if member.guild.id != TRACKED_GUILD:
        return

    inviter = get_member(member.name, member.guild.id)["inviter_id"]
    if inviter is None:
        return  # Could not look up

    try:
        status = insert_row(member.id, inviter, member.guild.id)
        if status:
            desc = f"Welcome! {member.mention} was invited by <@{inviter}>"
        else:
            desc = f"Welcome back! {member.mention} was already invited by <@{inviter}>"
        embed = discord.Embed(
            title="Invite Tracker",
            description=desc,
            color=discord.Color.blue(),
        )
        await bot.get_channel(ALERT_CHANNEL).send(embed=embed)
    except discord.Forbidden:
        logger.exception("Error: Forbidden")
    except discord.HTTPException as err:
        logger.exception(f"Error: {err}")


if __name__ == "__main__":
    try:
        logger.info("Starting bot")
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Fatal error starting bot: {e}")
