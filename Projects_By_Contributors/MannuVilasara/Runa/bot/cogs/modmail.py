from typing import Optional
import nextcord
from nextcord.ext import commands
from nextcord.ui import Select, View
from utils.mongo import mongo, servers
from main import bot
import datetime
import random
import os

options = []

id = None


class GuildControl(View):
    bot = bot

    @nextcord.ui.button(label="Close", style=nextcord.ButtonStyle.green)
    async def button_callback(self, button, interaction: nextcord.Interaction):
        db = mongo()
        db2 = servers()
        user = db.find_one({"modmail_guild": int(interaction.guild.id)})
        member = bot.get_user(int(user["_id"]))
        if not user:
            await interaction.response.send_message("Ticket Already closed")
            return
        channel = interaction.channel
        log = db2.find_one({"_id": str(interaction.guild.id)})
        # print(log)
        # # await message.channel.send(log)
        if log["log_channel"] != None:
            log_channel = bot.get_channel(int(log["log_channel"]))
            embed = nextcord.Embed(
                title="Ticket Closed",
                color=nextcord.Colour.red(),
                description=f"{channel.name}\n\n **__RESPONSIBLE USER:__**: {interaction.user.mention}",
            )
            embed.set_thumbnail(interaction.user.avatar)
            await log_channel.send(embed=embed)
        if log["transcripts"] != None:
            tsch = bot.get_channel(int(log["transcripts"]))
            history = await channel.history(limit=None, oldest_first=True).flatten()
            final = ""
            messages = []
            for msg in history:
                if msg.author == self.bot.user:
                    messages.append(msg.content)
                else:
                    messages.append(f"**{msg.author}**: {msg.content}")
            for msg in messages:
                final = final + "\n" + msg
            with open("transcript.txt", "w") as f:
                f.write(final)
            await tsch.send(file=nextcord.File("transcript.txt"))
            os.remove("transcript.txt")
        db.delete_one(user)
        user["modmail"] = False
        user["modmail_guild"] = None
        user["modmail_channel"] = None
        db.insert_one(user)
        await channel.delete()
        await member.send("Ticket Closed by Guild")
        return


class Confirm(View):
    bot = bot

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.danger)
    async def button_callback(self, button, interaction: nextcord.Interaction):
        db = mongo()
        db2 = servers()
        user = db.find_one({"_id": str(interaction.user.id)})
        if user["modmail"] == None:
            await interaction.response.send_message("No Opened Ticket")
        channel = self.bot.get_channel(int(user["modmail_channel"]))
        log = db2.find_one({"_id": str(user["modmail_guild"])})
        # print(log)
        # # await message.channel.send(log)
        if log["log_channel"] != None:
            log_channel = bot.get_channel(int(log["log_channel"]))
            embed = nextcord.Embed(
                title="Ticket Closed",
                color=nextcord.Colour.red(),
                description=f"{channel.name}\n\n **__RESPONSIBLE USER:__**: {interaction.user.mention}",
            )
            embed.set_thumbnail(interaction.user.avatar)
            await log_channel.send(embed=embed)
        if log["transcripts"] != None:
            tsch = bot.get_channel(int(log["transcripts"]))
            history = await channel.history(limit=None, oldest_first=True).flatten()
            final = ""
            messages = []
            for msg in history:
                if msg.author == self.bot.user:
                    messages.append(msg.content)
                else:
                    messages.append(f"**{msg.author}**: {msg.content}")
            for msg in messages:
                final = final + "\n" + msg
            with open("transcript.txt", "w") as f:
                f.write(final)
            await tsch.send(file=nextcord.File("transcript.txt"))
            os.remove("transcript.txt")
        db.delete_one(user)
        user["modmail"] = False
        user["modmail_guild"] = None
        user["modmail_channel"] = None
        db.insert_one(user)
        await interaction.response.send_message("`Ticket Close`")
        await channel.delete()
        return


class Control(View):
    bot = bot

    @nextcord.ui.button(label="Close", style=nextcord.ButtonStyle.red)
    async def button_callback(self, button, interaction: nextcord.Interaction):
        db = mongo()
        user = db.find_one({"_id": str(interaction.user.id)})
        if user["modmail"] == False:
            await interaction.response.send_message("No Opened Ticket", ephemeral=True)
            return
        await interaction.response.send_message(
            "Do you really want to close the ticket?",
            view=Confirm(),
            ephemeral=True,
            delete_after=10,
        )
        pass


class Guild(View):
    @nextcord.ui.select(options=options)
    async def select_callback(self, select, interaction: nextcord.Interaction):
        id = random.randint(10000, 99999)
        db = mongo()
        db2 = servers()
        user = db.find_one({"_id": str(interaction.user.id)})
        if user["modmail"] == True:
            await interaction.response.send_message(
                "`Please Close Your Previous Ticket First`", delete_after=3
            )
            return
        server = db2.find_one({"_id": str(select.values[0])})
        if not server:
            await interaction.response.send_message(
                f"`Guild Has No Modmail setup`", delete_after=3
            )
            return
        if int(interaction.user.id) in server["blocklist"]:
            await interaction.response.send_message(
                "`You are Blocked by the guild from creating any tickets`",
                delete_after=3,
            )
            return
        user = db.find_one({"_id": str(interaction.user.id)})
        db.delete_one(user)
        user["modmail"] = True
        user["modmail_guild"] = int(select.values[0])
        guild = bot.get_guild(int(user["modmail_guild"]))
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(read_messages=False)
        }
        category = None
        for cat in guild.categories:
            if cat.id == server["category"]:
                category = cat
        channel = await guild.create_text_channel(
            name=interaction.user.name, overwrites=overwrites, category=category
        )
        user["modmail_channel"] = int(channel.id)
        db.insert_one(user)
        embed = nextcord.Embed(
            title="Ticket",
            description=f"Ticket Created by **{interaction.user.name}** at **{datetime.datetime.now()}**",
            color=nextcord.Colour.green(),
        )
        embed.set_footer(text=f"temp-id: {id}", icon_url=guild.icon)
        embed.add_field(name="Name", value=interaction.user.name)
        embed.set_thumbnail(interaction.user.avatar)
        embed2 = nextcord.Embed(description=f"Temporary Ticket id: {id}")
        await interaction.response.send_message(
            "`Ticket Created`", embed=embed2, view=Control()
        )
        server = db2.find_one({"_id": str(user["modmail_guild"])})
        if server["pingrole"] != None:
            role = guild.get_role(server["pingrole"])
            await channel.send(content=role.mention, embed=embed, view=GuildControl())
        else:
            await channel.send(embed=embed, view=GuildControl())
        if server["log_channel"] == None:
            return
        log_channel = bot.get_channel(int(server["log_channel"]))
        embed = nextcord.Embed(
            title="Ticket Opened",
            color=nextcord.Colour.green(),
            description=f"{channel.mention}\n\n **__RESPONSIBLE USER:__**: {interaction.user.mention}",
        )
        embed.set_footer(text=f"temp-id: {id}", icon_url=guild.icon)
        embed.set_thumbnail(interaction.user.avatar)
        await log_channel.send(embed=embed)


class Modmail(commands.Cog):
    """DM me to create a ticket!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.message.Message):
        if message.author == self.bot.user:
            return
        if isinstance(message.channel, nextcord.DMChannel):
            db = mongo()
            db2 = servers()
            user = db.find_one({"_id": str(message.author.id)})
            if not user:
                db.insert_one(
                    {
                        "_id": str(message.author.id),
                        "name": str(message.author.name),
                        "modmail": bool(False),
                        "modmail_guild": None,
                        "modmail_channel": None,
                    }
                )
                view = Guild()
                await message.channel.send(view=view)
            if user["modmail"] == False:
                guilds = message.author.mutual_guilds
                if len(options) != len(guilds):
                    for guild in guilds:
                        options.append(
                            nextcord.SelectOption(label=guild.name, value=str(guild.id))
                        )
                view = Guild()
                await message.channel.send(view=view)
                options.clear()
                return
            else:
                channel = self.bot.get_channel(int(user["modmail_channel"]))
                if message.content == "~close":
                    if user["modmail"] == False:
                        await message.channel.send("No Ticket opened")
                        return
                    log = db2.find_one({"_id": str(user["modmail_guild"])})
                    # print(log)
                    # # await message.channel.send(log)
                    if log["log_channel"] != None:
                        log_channel = bot.get_channel(int(log["log_channel"]))
                        embed = nextcord.Embed(
                            title="Ticket Closed",
                            color=nextcord.Colour.red(),
                            description=f"{channel.mention}\n\n **__RESPONSIBLE USER:__**: {message.author.mention}",
                        )
                        embed.set_thumbnail(message.author.avatar)
                        await log_channel.send(embed=embed)
                    if log["transcripts"] != None:
                        tsch = bot.get_channel(int(log["transcripts"]))
                        history = await channel.history(
                            limit=None, oldest_first=True
                        ).flatten()
                        final = ""
                        messages = []
                        for msg in history:
                            if msg.author == self.bot.user:
                                messages.append(msg.content)
                            else:
                                messages.append(f"**{msg.author}**: {msg.content}")
                        for msg in messages:
                            final = final + "\n" + msg
                        with open("transcript.txt", "w") as f:
                            f.write(final)
                        await tsch.send(file=nextcord.File("transcript.txt"))
                        os.remove("transcript.txt")
                    db.delete_one(user)
                    user["modmail"] = False
                    user["modmail_guild"] = None
                    user["modmail_channel"] = None
                    db.insert_one(user)
                    await message.channel.send("`Ticket Close`")
                    await channel.delete()
                    return
                await channel.send(f"**{message.author}**: {message.content}")
        else:
            db2 = servers()
            db = mongo()
            user_db = db.find_one({"modmail_channel": message.channel.id})
            if not user_db:
                return
            user = await self.bot.fetch_user(user_db["_id"])
            if message.content == f"{self.bot.command_prefix}close":
                log = db2.find_one({"_id": str(user_db["modmail_guild"])})
                if log["log_channel"] != None:
                    log_channel = bot.get_channel(int(log["log_channel"]))
                    embed = nextcord.Embed(
                        title="Ticket Closed",
                        color=nextcord.Colour.red(),
                        description=f"{message.channel.mention}\n\n **__RESPONSIBLE USER:__**: {message.author.mention}",
                    )
                    embed.set_thumbnail(message.author.avatar)
                    await log_channel.send(embed=embed)
                if log["transcripts"] != None:
                    tsch = bot.get_channel(int(log["transcripts"]))
                    history = await message.channel.history(
                        limit=None, oldest_first=True
                    ).flatten()
                    final = ""
                    messages = []
                    for msg in history:
                        if msg.author == self.bot.user:
                            messages.append(msg.content)
                        else:
                            messages.append(f"**{msg.author}**: {msg.content}")
                    for msg in messages:
                        final = final + "\n" + msg
                    with open("transcript.txt", "w") as f:
                        f.write(final)
                    await tsch.send(file=nextcord.File("transcript.txt"))
                    os.remove("transcript.txt")
                db.delete_one(user_db)
                user_db["modmail"] = False
                user_db["modmail_guild"] = None
                user_db["modmail_channel"] = None
                db.insert_one(user_db)
                await user.send(f"`Ticket Closed`")
                await message.channel.delete()
                return
            embed = nextcord.Embed(
                title=message.author.name,
                description=message.content,
                color=nextcord.Colour.green(),
            )
            embed.set_thumbnail(url=message.author.guild.icon)
            await user.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Modmail(bot))
    print("Modmail Loaded")
