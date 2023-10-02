import os
import sqlite3
import aiosqlite
import nextcord

from config import TOKEN
from nextcord import SlashOption
from nextcord.ext import commands, application_checks


class Runa(commands.Bot):
    async def startup(self) -> None:
        print(f"Bot Ready | Guilds: {len(self.guilds)} | Users: {len(self.users)}")


bot = Runa(command_prefix="~", case_insensitive=True, intents=nextcord.Intents.all())
bot.remove_command("help")

for fn in os.listdir("bot/cogs"):
    if fn.endswith(".py"):
        bot.load_extension(f"cogs.{fn[:-3]}")


@bot.event
async def on_ready():
    db = sqlite3.connect("main.sqlite")
    cursor = db.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS main(guild_id TEXT,msg TEXT,channel_id TEXT)"""
    )

    bot.db1 = await aiosqlite.connect("level.db")
    bot.db2 = await aiosqlite.connect("bank.db")
    bot.db4 = await aiosqlite.connect("welcome.db")
    bot.dblog = await aiosqlite.connect("log.db")

    await bot.change_presence(
        activity=nextcord.Streaming(
            type=3,
            name=" for /help | DM me to create a ticket!",
            url="https://www.twitch.tv/secretsocietyserver",
        )
    )


@bot.slash_command(description="Creates an invite to the server")
async def invite(interaction: nextcord.Interaction, channel: nextcord.TextChannel):
    invite = await channel.create_invite()
    await interaction.send(invite)


@bot.slash_command(description="Kills the bot")
@application_checks.is_owner()
async def shutdown(interaction: nextcord.Interaction):
    try:
        await interaction.response.send_message("I have been brutally murdered :(")
        await bot.close()
    except Exception as e:
        await interaction.response.send_message(
            f"Your assassination attempt has been blocked! Maybe ask Fawn for some help... \nError: ```{e}```"
        )


@bot.slash_command(description="Loads a cog")
@application_checks.is_owner()
async def load(
    interaction: nextcord.Interaction,
    extension: str = SlashOption(description="Cog you would like to load"),
):
    try:
        bot.load_extension(f"cogs.{extension}")
    except commands.ExtensionAlreadyLoaded:
        return await interaction.response.send_message("Cog is already loaded")
    except commands.ExtensionNotFound:
        return await interaction.response.send_message("Cog is not found")
    await interaction.response.send_message("Cog loaded")


@bot.slash_command(description="Reloads a cog")
@application_checks.is_owner()
async def reload(
    interaction: nextcord.Interaction,
    extension: str = SlashOption(description="Cog you would like to reload"),
):
    try:
        bot.reload_extension(f"cogs.{extension}")
    except commands.ExtensionNotFound:
        return await interaction.response.send_message("Cog is not found")
    await interaction.response.send_message("Cog reloaded")


@bot.slash_command(description="Unloads a cog")
@application_checks.is_owner()
async def unload(
    interaction: nextcord.Interaction,
    extension: str = SlashOption(description="Cog you would like to unload"),
):
    try:
        bot.unload_extension(f"cogs.{extension}")
    except commands.ExtensionNotFound:
        return await interaction.response.send_message("Cog is not found")
    await interaction.response.send_message("Cog unloaded")


@bot.slash_command(description="Gets the bot's ping")
async def ping(interaction: nextcord.Interaction):
    await interaction.send(f"Pong! {round(bot.latency*1000)}ms")


bot.run(TOKEN)
