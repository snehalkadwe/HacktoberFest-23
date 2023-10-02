import cooldowns
import datetime
import random
import asyncio
import aiosqlite

import nextcord
from nextcord.abc import GuildChannel
from nextcord.ext import commands, application_checks
from nextcord import SlashOption, ChannelType


class Welcome(commands.Cog, name="Welcome"):
    """setwelcome"""

    def __init__(self, bot):
        self.bot = bot
        self.responses = [
            "Welcome {}. Annuit Coeptis Novus Ordo Seclorum.",
            "Welcome, {}!",
            "Welcome  {}. Come freely, go safely, and leave something of the happiness you bring.",
            "Dear {}, enter freely and of your own free will!",
            "Welcome to our world, {}.",
            "Good day to you, {}! I was not expecting such honored company today.",
            "Welcome, {}. No one leaves this beautiful place feeling the same way they came.",
            "We welcome {} with open arms.",
            "Welcome {}! Feel free to introduce yourself!",
        ]
        self.responses = [
            "Welcome {}. Annuit Coeptis Novus Ordo Seclorum.",
            "Welcome, {}!",
            "Welcome  {}. Come freely, go safely, and leave something of the happiness you bring.",
            "Dear {}, enter freely and of your own free will!",
            "Welcome to our world, {}.",
            "Good day to you, {}! I was not expecting such honored company today.",
            "Welcome, {}. No one leaves this beautiful place feeling the same way they came.",
            "We welcome {} with open arms.",
            "Welcome {}! Feel free to introduce yourself!",
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        setattr(self.bot, "db4", await aiosqlite.connect("welcome.db"))
        await asyncio.sleep(3)
        async with self.bot.db4.cursor() as cursor:
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS welcome (guild INTEGER, welcomeChannel INTEGER)"
            )
        await self.bot.db4.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        async with self.bot.db4.cursor() as cursor:
            await cursor.execute(
                "SELECT welcomeChannel FROM welcome WHERE guild = ?", (member.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = member.guild.get_channel(channelID)
        if not channel:
            return
        response = random.choice(self.responses)

        embed = nextcord.Embed(
            color=0xFD9FA1,
            description=random.choice(self.responses).format(member.mention),
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name=f"{member.name}", icon_url=member.display_avatar)
        embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon.url}")
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    @nextcord.slash_command(description="Sets the welcome channel [per guild]")
    @application_checks.has_permissions(manage_channels=True)
    @cooldowns.cooldown(1, 20, bucket=cooldowns.SlashBucket.author)
    async def setwelcome(
        self,
        interaction: nextcord.Interaction,
        channel: GuildChannel = SlashOption(channel_types=[ChannelType.text]),
    ):
        if channel is None:
            channel = 0
        async with self.bot.db4.cursor() as cursor:
            await cursor.execute(
                "SELECT welcomeChannel FROM welcome WHERE guild = ?",
                (interaction.guild.id,),
            )
            data = await cursor.fetchone()
            if data:
                if channel == 0:
                    await cursor.execute(
                        "UPDATE welcome SET welcomeChannel = ? WHERE guild = ?",
                        (
                            0,
                            interaction.guild.id,
                        ),
                    )
                    await interaction.send("Removed welcome channel")
                else:
                    if not channel:
                        return await interaction.send("Cannot find mentioned channel")
                    channel = interaction.guild.get_channel(channel.id)
                    await cursor.execute(
                        "UPDATE welcome SET welcomeChannel = ? WHERE guild = ?",
                        (
                            channel.id,
                            interaction.guild.id,
                        ),
                    )
                    await interaction.send(
                        f"The welcome channel has been set to {channel.mention}"
                    )
            else:
                channel = interaction.guild.get_channel(channel.id)
                if not channel:
                    return await interaction.send("Cannot find mentioned channel")
                await cursor.execute(
                    f"INSERT INTO welcome (guild, welcomeChannel) VALUES (?,?)",
                    (interaction.guild.id, channel.id),
                )
                await interaction.send(
                    f"The welcome channel has been set to {channel.mention}"
                )
        await self.bot.db4.commit()


def setup(bot):
    bot.add_cog(Welcome(bot))
    print("Welcome is loaded")
