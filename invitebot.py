#!/usr/bin/env python3
"""Main entry point for the Discord invite tracker bot.
Integrates all components and handles Discord events.
"""

import asyncio
import os

import discord
from discord.ext import bridge

from invite.config import TOKEN
from invite.db import get_inviter_invitees, insert_row
from invite.rawapi import get_member
from invite.utils import logger

# Bot setup
bot = bridge.Bot(
    allowed_mentions=discord.AllowedMentions(
        everyone=False, users=False, roles=False, replied_user=True
    ),
    command_prefix="!",
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


@bot.bridge_command(description="Shows who was invited.", guild_ids=[TRACKED_GUILD])
async def invited(ctx: bridge.BridgeContext) -> None:
    """View who you invited!

    Args:
        ctx: Command context

    """
    invited = get_inviter_invitees(TRACKED_GUILD).get(ctx.author.id, [])
    if invited:
        names = " ".join(f"<@{i}>" for i in invited)
        await ctx.respond(f"You invited {len(invited)} people!\n{names}")
    else:
        await ctx.respond(
            "You haven't invited anyone yet (at least since 2024..)",
        )


@bot.bridge_command(description="Shows the leaderboard.", guild_ids=[TRACKED_GUILD])
async def topinvites(ctx: bridge.BridgeContext) -> None:
    """View the leaderboard!

    Args:
        ctx: Command context

    """
    mapping = get_inviter_invitees(TRACKED_GUILD)
    pos = 0
    emojis = ["🥇", "🥈", "🥉"]
    output = []
    for user, invited in sorted(
        mapping.items(),
        key=lambda item: len(item[1]),
        reverse=True,
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
    await ctx.respond(f"## Leaderboard\n{output}")


@bot.listen("on_member_join")
async def on_member_join(member: discord.Member) -> None:
    if member.guild.id != TRACKED_GUILD:
        return

    async def post_embed(desc: str):
        embed = discord.Embed(
            title="Invite Tracker",
            description=desc,
            color=discord.Color.blue(),
        )
        await bot.get_channel(ALERT_CHANNEL).send(embed=embed)

    logger.info("%s joined %s", member.name, member.guild.name)
    await asyncio.sleep(30)  # Let the API update
    inviter = get_member(member.name, member.guild.id)["inviter_id"]
    if inviter is None:
        await post_embed(f"Welcome {member.mention}")
        logger.error("Could not find %s inviter!", member.name)
        return  # Could not look up

    try:
        status = insert_row(member.id, inviter, member.guild.id)
        if status:
            await post_embed(f"Welcome! {member.mention} was invited by <@{inviter}>")
        else:
            await post_embed(
                f"Welcome back! {member.mention} was already invited by <@{inviter}>"
            )

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
