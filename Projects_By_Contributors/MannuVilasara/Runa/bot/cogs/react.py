import nextcord
import re
import sqlite3

from nextcord.ext import commands, application_checks


class ReactCog(commands.Cog, name="Reactions"):
    """roleadd, roleremove"""

    def __init__(self, bot):
        self.bot = bot
        db = sqlite3.connect("main.sqlite")
        cursor = db.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS reaction(emoji TEXT, role TEXT, message_id TEXT, channel_id TEXT, guild_id TEXT)"""
        )

    # add role on reaction
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        main = sqlite3.connect("main.sqlite")
        cursor = main.cursor()
        if "<:" in str(reaction.emoji):
            cursor.execute(
                f"SELECT emoji, role, message_id, channel_id  FROM reaction WHERE guild_id= '{reaction.guild_id}' and message_id='{reaction.message_id}' and emoji='{reaction.emoji.id}'"
            )
            result = cursor.fetchone()
            guild = self.bot.get_guild(reaction.guild_id)
            if result is None:
                return
            elif str(reaction.emoji.id) in str(result[0]):
                on = nextcord.utils.get(guild.roles, id=int(result[1]))
                user = guild.get_member(reaction.user_id)
                await user.add_roles(on)
            else:
                return
        elif "<:" not in str(reaction.emoji):
            cursor.execute(
                f"SELECT emoji, role, message_id, channel_id  FROM reaction WHERE guild_id= '{reaction.guild_id}' and message_id='{reaction.message_id}' and emoji='{reaction.emoji}'"
            )
            result = cursor.fetchone()
            guild = self.bot.get_guild(reaction.guild_id)
            if result is None:
                return
            elif result is not None:
                on = nextcord.utils.get(guild.roles, id=int(result[1]))
                user = guild.get_member(reaction.user_id)
                await user.add_roles(on)
        else:
            return

    # remove role after user removes reaction
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        main = sqlite3.connect("main.sqlite")
        cursor = main.cursor()
        if "<:" in str(reaction.emoji):
            cursor.execute(
                f"SELECT emoji, role, message_id, channel_id  FROM reaction WHERE guild_id= '{reaction.guild_id}' and message_id='{reaction.message_id}' and emoji='{reaction.emoji.id}'"
            )
            result = cursor.fetchone()
            guild = self.bot.get_guild(reaction.guild_id)
            if result is None:
                return
            elif str(reaction.emoji.id) in str(result[0]):
                on = nextcord.utils.get(guild.roles, id=int(result[1]))
                user = guild.get_member(reaction.user_id)
                await user.remove_roles(on)
            else:
                return
        elif "<:" not in str(reaction.emoji):
            cursor.execute(
                f"SELECT emoji, role, message_id, channel_id  FROM reaction WHERE guild_id= '{reaction.guild_id}' and message_id='{reaction.message_id}' and emoji='{reaction.emoji}'"
            )
            result = cursor.fetchone()
            guild = self.bot.get_guild(reaction.guild_id)
            if result is None:
                return
            elif result is not None:
                on = nextcord.utils.get(guild.roles, id=int(result[1]))
                user = guild.get_member(reaction.user_id)
                await user.remove_roles(on)
        else:
            return

    # roleadd
    @nextcord.slash_command(description="Add a reaction role")
    @application_checks.has_permissions(manage_channels=True)
    async def roleadd(
        self,
        interaction,
        channel: nextcord.TextChannel,
        messageid,
        emoji,
        role: nextcord.Role,
    ):
        main = sqlite3.connect("main.sqlite")
        cursor = main.cursor()
        cursor.execute(
            f"SELECT emoji, role, message_id, channel_id FROM reaction WHERE guild_id='{interaction.guild.id}' and message_id='{messageid}'"
        )
        result = cursor.fetchone()
        if "<:" in emoji:
            enm = re.sub(":.*?:", "", emoji).strip("<>")
            if result is None:
                sql = "INSERT INTO reaction(emoji, role, message_id, channel_id, guild_id) VALUES(?,?,?,?,?) "
                val = (enm, role.id, messageid, channel.id, interaction.guild.id)
                msg = await channel.fetch_message(messageid)
                em = self.bot.get_emoji(int(enm))
                await msg.add_reaction(em)
                await interaction.send("Done.")
            elif str(messageid) not in str(result[3]):
                sql = "INSERT INTO reaction(emoji, role, message_id, channel_id, guild_id) VALUES(?,?,?,?,?)"
                val = (enm, role.id, messageid, channel.id, interaction.guild.id)
                msg = await channel.fetch_message(messageid)
                em = self.bot.get_emoji(int(enm))
                await msg.add_reaction(em)
                await interaction.send("Done.")
        elif "<:" not in emoji:
            if result is None:
                sql = "INSERT INTO reaction(emoji, role, message_id, channel_id, guild_id) VALUES(?,?,?,?,?)"
                val = (emoji, role.id, messageid, channel.id, interaction.guild.id)
                msg = await channel.fetch_message(messageid)
                await msg.add_reaction(emoji)
                await interaction.send("Done.")
            elif str(messageid) not in str(result[3]):
                sql = "INSERT INTO reaction(emoji, role, message_id, channel_id, guild_id) VALUES(?,?,?,?,?)"
                val = (emoji, role.id, messageid, channel.id, interaction.guild.id)
                msg = await channel.fetch_message(messageid)
                await msg.add_reaction(emoji)
                await interaction.send("Done.")
        cursor.execute(sql, val)
        main.commit()
        cursor.close()
        main.close()

    # roleremove
    @nextcord.slash_command(description="Remove a reaction role")
    @application_checks.has_permissions(manage_channels=True)
    async def roleremove(self, interaction, messageid=None, emoji=None):
        main = sqlite3.connect("main.sqlite")
        cursor = main.cursor()
        cursor.execute(
            f"SELECT emoji, role, message_id, channel_id FROM reaction WHERE guild_id ='{interaction.guild.id}'and message_id='{messageid}'"
        )
        result = cursor.fetchone()
        if "<:" in emoji:
            enm = re.sub(":.*?:", "", emoji).strip("<>")
            if result is None:
                await interaction.send("I couldn't find that reaction on that message!")
            elif str(messageid) in str(result[2]):
                cursor.execute(
                    f"DELETE FROM reaction WHERE guild_id='{interaction.guild.id}' and message_id='{messageid}'and emoji='{enm}'"
                )
                await interaction.send("I removed the reaction :)")
            else:
                await interaction.send("I couldn't find that reaction on that message!")
        elif "<:" not in emoji:
            if result is None:
                await interaction.send("I couldn't find that reaction on that message!")
            elif str(messageid) in str(result[2]):
                cursor.execute(
                    f"DELETE FROM reaction WHERE guild_id='{interaction.guild.id}' and message_id='{messageid}'and emoji='{emoji}'"
                )
                await interaction.send("I removed the reaction :)")
            else:
                await interaction.send("I couldn't find that reaction on that message!")
        main.commit()
        cursor.close()
        main.close()


def setup(bot):
    bot.add_cog(ReactCog(bot))
    print("React is loaded")
