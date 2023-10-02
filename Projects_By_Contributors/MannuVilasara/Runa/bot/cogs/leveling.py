import asyncio
import random
import cooldowns
from easy_pil import *

import nextcord
from nextcord.ext import application_checks, commands
from nextcord.abc import GuildChannel
from nextcord import SlashOption, ChannelType


class LevelCog(commands.Cog, name="Leveling"):
    """setlevel, rank, slvl enable, slvl disable, leaderboard, add_level, add_xp, subtract_level, subtract_xp"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(3)
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS levels (level INTEGER, xp INTEGER, user INTEGER, guild INTEGER)"
            )
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS levelSettings (levelsys BOOL, role INTEGER, levelreq INTEGER, guild INTEGER)"
            )
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS levelchannel (guild INTEGER, levelChannel INTEGER)"
            )

    # setlevel
    @nextcord.slash_command(description=".")
    @application_checks.has_permissions(manage_channels=True)
    @cooldowns.cooldown(1, 20, bucket=cooldowns.SlashBucket.author)
    async def setlevel(
        self,
        interaction: nextcord.Interaction,
        channel: GuildChannel = SlashOption(channel_types=[ChannelType.text]),
    ):
        if channel is None:
            channel = 0
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelChannel FROM levelchannel WHERE guild = ?",
                (interaction.guild.id,),
            )
            data = await cursor.fetchone()
            if data:
                if channel == 0:
                    await cursor.execute(
                        "UPDATE levelchannel SET levelChannel = ? WHERE guild = ?",
                        (
                            0,
                            interaction.guild.id,
                        ),
                    )
                    await interaction.send("Removed level channel")
                else:
                    if not channel:
                        return await interaction.send("Cannot find mentioned channel")
                    channel = interaction.guild.get_channel(channel.id)
                    await cursor.execute(
                        "UPDATE levelchannel SET levelChannel = ? WHERE guild = ?",
                        (
                            channel.id,
                            interaction.guild.id,
                        ),
                    )
                    await interaction.send(
                        f"The level channel has been set to {channel.mention}"
                    )
            else:
                channel = interaction.guild.get_channel(channel.id)
                if not channel:
                    return await interaction.send("Cannot find mentioned channel")
                await cursor.execute(
                    f"INSERT INTO levelchannel (guild, levelChannel) VALUES (?,?)",
                    (interaction.guild.id, channel.id),
                )
                await interaction.send(
                    f"The level channel has been set to {channel.mention}"
                )
        await self.bot.db1.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return
        author = message.author
        guild = message.guild
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?", (guild.id,)
            )
            levelsys = await cursor.fetchone()
            if levelsys and not levelsys[0]:
                return
            await cursor.execute(
                "SELECT xp FROM levels WHERE user = ? AND guild = ?",
                (author.id, guild.id),
            )
            xp = await cursor.fetchone()
            await cursor.execute(
                "SELECT level FROM levels WHERE user = ? AND guild = ?",
                (author.id, guild.id),
            )
            level = await cursor.fetchone()
            if not xp or not level:
                await cursor.execute(
                    "INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)",
                    (0, 0, author.id, guild.id),
                )
            try:
                xp = xp[0]
                level = level[0]
            except TypeError:
                xp = 0
                level = 0
            if level < 5:
                xp += random.randint(1, 3)
                await cursor.execute(
                    "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?",
                    (xp, author.id, guild.id),
                )
            else:
                rand = random.randint(1, (level // 4))
                if rand == 1:
                    xp += random.randint(1, 3)
                    await cursor.execute(
                        "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?",
                        (xp, author.id, guild.id),
                    )
            if xp >= 100:
                level += 1
                await cursor.execute(
                    "UPDATE levels SET level = ? WHERE user = ? AND guild = ?",
                    (level, author.id, guild.id),
                )
                await cursor.execute(
                    "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?",
                    (0, author.id, guild.id),
                )
                async with self.bot.db1.cursor() as cursor:
                    await cursor.execute(
                        "SELECT levelChannel FROM levelchannel WHERE guild = ?",
                        (guild.id,),
                    )
                    channelID = await cursor.fetchone()
                    if not channelID:
                        return
                    channelID = channelID[0]
                    channel = guild.get_channel(channelID)
                    if not channel:
                        return await message.channel.send(
                            f"{author.name} has leveled up to level {level}!"
                        )
                    await channel.send(
                        f"{author.name} has leveled up to level {level}!"
                    )
                await self.bot.db1.commit()

    @nextcord.slash_command(description="See what level you are!")
    async def rank(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="The member whos rank you want to see!"
        ),
    ):
        if member is None:
            member = interaction.user

        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?",
                (interaction.guild.id,),
            )
            levelsys = await cursor.fetchone()

            if levelsys and not levelsys[0]:
                await interaction.response.send_message("Leveling system is disabled!")
                return

            await cursor.execute(
                "SELECT level FROM levels WHERE user = ? AND guild = ?",
                (member.id, interaction.guild.id),
            )
            level = await cursor.fetchone()
            await cursor.execute(
                "SELECT xp FROM levels WHERE user = ? AND guild = ?",
                (member.id, interaction.guild.id),
            )
            xp = await cursor.fetchone()

            if not xp or not level:
                await cursor.execute(
                    "INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)",
                    (0, 0, member.id, interaction.guild.id),
                )
                await self.bot.db1.commit()
            try:
                xp = xp[0]
                level = level[0]
            except TypeError:
                xp = 0
                level = 0
            user_data = {
                "name": f"{member.name}",
                "xp": xp,
                "level": level,
                "next_level_xp": 100,
                "percentage": xp,
            }

        background = Editor(Canvas((900, 300), color="#ff6365"))
        profile_picture = await load_image_async(str(member.avatar.url))
        profile = Editor(profile_picture).resize((150, 150)).circle_image()
        poppins = Font.poppins(size=40)
        poppins_small = Font.poppins(size=30)
        card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]
        background.polygon(card_right_shape, color="#ffdada")
        background.paste(profile, (30, 30))
        background.rectangle((30, 220), width=650, height=40, color="#ffdada")
        background.bar(
            (30, 220),
            max_width=650,
            height=40,
            color="#ffb4e7",
            percentage=user_data["percentage"],
            radius=20,
        )
        background.text((200, 40), user_data["name"], font=poppins, color="#ffdada")
        background.rectangle((200, 100), width=350, height=2, fill="#ffdada")
        background.text(
            (200, 130),
            f"Level: {user_data['level']} | XP: {user_data['xp']}/{user_data['next_level_xp']}",
            font=poppins_small,
            color="#ffdada",
        )

        file = nextcord.File(fp=background.image_bytes, filename="levelcard.png")
        await interaction.response.send_message(file=file)

    @nextcord.slash_command(description="Blank Command for level settings")
    async def slvl(self, interaction: nextcord.Interaction):
        pass

    # toggle leveling system on
    @slvl.subcommand(description="Enable the leveling system!")
    @application_checks.has_permissions(manage_guild=True)
    async def enable(self, interaction: nextcord.Interaction):
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?",
                (interaction.guild.id,),
            )
            levelsys = await cursor.fetchone()
            if levelsys:
                if levelsys[0]:
                    await interaction.response.send_message(
                        "The leveling system is already enabled.", ephemeral=True
                    )
                    return
                await cursor.execute(
                    "UPDATE levelSettings SET levelsys = ? WHERE guild = ?",
                    (True, interaction.guild.id),
                )
            else:
                await cursor.execute(
                    "INSERT INTO levelSettings VALUES (?,?,?,?)",
                    (True, 0, 0, interaction.guild.id),
                )
            await interaction.response.send_message(
                "Enabled the leveling system!", ephemeral=True
            )
        await self.bot.db1.commit()

    # toggle leveling system off
    @slvl.subcommand(description="Disable the leveling system!")
    @application_checks.has_permissions(manage_guild=True)
    async def disable(self, interaction: nextcord.Interaction):
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?",
                (interaction.guild.id,),
            )
            levelsys = await cursor.fetchone()
            if levelsys:
                if not levelsys[0]:
                    await interaction.response.send_message(
                        "The leveling system is already disabled.", ephemeral=True
                    )
                    return
                await cursor.execute(
                    "UPDATE levelSettings SET levelsys = ? WHERE guild = ?",
                    (False, interaction.guild.id),
                )
            else:
                await cursor.execute(
                    "INSERT INTO levelSettings VALUES (?,?,?,?)",
                    (False, 0, 0, interaction.guild.id),
                )
            await interaction.response.send_message(
                "Disabled the leveling system!", ephemeral=True
            )
        await self.bot.db1.commit()

    # leaderboard
    @nextcord.slash_command(description="View the server leaderboard")
    async def leaderboard(self, interaction: nextcord.Interaction):
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?",
                (interaction.guild.id,),
            )
            levelsys = await cursor.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    await interaction.response.send_message(
                        "Level system is disabled in this server.", ephemeral=True
                    )
                    return
            await cursor.execute(
                "SELECT level, xp, user FROM levels WHERE guild = ? ORDER BY level DESC, xp DESC LIMIT 10",
                (interaction.guild.id,),
            )
            data = await cursor.fetchall()
            if data:
                em = nextcord.Embed(title="Server Leaderboard", color=0xFD9FA1)
                count = 1
                for table in data:
                    member = interaction.guild.get_member(table[2])
                    em.add_field(
                        name=f"{count}. {member}",
                        value=f"Level-**{table[0]}** | XP-**{table[1]}**",
                        inline=False,
                    )
                    count += 1
                await interaction.response.send_message(embed=em, ephemeral=True)
                return
            await interaction.response.send_message(
                "There are no users stored in the database.", ephemeral=True
            )
            return

    @nextcord.slash_command(description="Add levels to a user [admin only]")
    @application_checks.has_permissions(administrator=True)
    async def add_level(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="The member whos level you want to add!"
        ),
        amount: int = None,
    ):
        if not amount:
            return await interaction.response.send_message(
                "Please provide an amount of levels to add!", ephemeral=True
            )
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?",
                (interaction.guild.id,),
            )
            levelsys = await cursor.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    await interaction.response.send_message(
                        "Level system is disabled in this server.", ephemeral=True
                    )
                    return
            await cursor.execute(
                "SELECT level FROM levels WHERE user = ? AND guild = ?",
                (member.id, interaction.guild.id),
            )
            level = await cursor.fetchone()
            level = level[0]
            level += amount
            await cursor.execute(
                "UPDATE levels SET level = ? WHERE user = ? AND guild = ?",
                (level, member.id, interaction.guild.id),
            )
            await interaction.response.send_message(
                f"{member.mention} has received {amount} levels!", ephemeral=True
            )
        await self.bot.db1.commit()

    @nextcord.slash_command(description="Add xp to a user [admin only]")
    @application_checks.has_permissions(administrator=True)
    async def add_xp(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="The member whos xp you want to add!"
        ),
        amount: int = None,
    ):
        if not amount:
            return await interaction.response.send_message(
                "Please provide an amount of levels to add!", ephemeral=True
            )
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?",
                (interaction.guild.id,),
            )
            levelsys = await cursor.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    await interaction.response.send_message(
                        "Level system is disabled in this server.", ephemeral=True
                    )
                    return
            await cursor.execute(
                "SELECT xp FROM levels WHERE user = ? AND guild = ?",
                (member.id, interaction.guild.id),
            )
            xp = await cursor.fetchone()
            xp = xp[0]
            xp += amount
            await cursor.execute(
                "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?",
                (xp, member.id, interaction.guild.id),
            )
            await interaction.response.send_message(
                f"{member.mention} has received {amount} xp!", ephemeral=True
            )
        await self.bot.db1.commit()

    @nextcord.slash_command(description="Remove levels from a user [admin only]")
    @application_checks.has_permissions(administrator=True)
    async def subtract_level(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="The member whos level you want to subscract"
        ),
        amount: int = None,
    ):
        if not amount:
            return await interaction.response.send_message(
                "Please provide an amount of levels to add!", ephemeral=True
            )
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?",
                (interaction.guild.id,),
            )
            levelsys = await cursor.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    await interaction.response.send_message(
                        "Level system is disabled in this server.", ephemeral=True
                    )
                    return
            await cursor.execute(
                "SELECT level FROM levels WHERE user = ? AND guild = ?",
                (member.id, interaction.guild.id),
            )
            level = await cursor.fetchone()
            level = level[0]
            level -= amount
            await cursor.execute(
                "UPDATE levels SET level = ? WHERE user = ? AND guild = ?",
                (level, member.id, interaction.guild.id),
            )
            await interaction.response.send_message(
                f"{member.mention} lost {amount} levels.", ephemeral=True
            )
        await self.bot.db1.commit()

    @nextcord.slash_command(description="Remove xp from a user [admin only]")
    @application_checks.has_permissions(administrator=True)
    async def subtract_xp(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="The member whos xp you want to subscract"
        ),
        amount: int = None,
    ):
        if not amount:
            return await interaction.response.send_message(
                "Please provide an amount of levels to add!", ephemeral=True
            )
        async with self.bot.db1.cursor() as cursor:
            await cursor.execute(
                "SELECT levelsys FROM levelSettings WHERE guild = ?",
                (interaction.guild.id,),
            )
            levelsys = await cursor.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    await interaction.response.send_message(
                        "Level system is disabled in this server.", ephemeral=True
                    )
                    return
            await cursor.execute(
                "SELECT xp FROM levels WHERE user = ? AND guild = ?",
                (member.id, interaction.guild.id),
            )
            xp = await cursor.fetchone()
            xp = xp[0]
            xp -= amount
            await cursor.execute(
                "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?",
                (xp, member.id, interaction.guild.id),
            )
            await interaction.response.send_message(
                f"{member.mention} lost {amount} xp.", ephemeral=True
            )
        await self.bot.db1.commit()


def setup(bot):
    bot.add_cog(LevelCog(bot))
    print("Leveling is loaded")
