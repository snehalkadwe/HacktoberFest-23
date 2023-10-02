import nextcord
import datetime
import cooldowns
import asyncio
import aiosqlite
from nextcord.ext import commands
from nextcord.ext import *
from nextcord.abc import GuildChannel
from nextcord import *


class LogCog(commands.Cog, name="Log"):
    """setlog, shutdown, load, unload, reload, ping"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        setattr(self.bot, "dblog", await aiosqlite.connect("log.db"))
        await asyncio.sleep(3)
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS log (guild INTEGER, logChannel INTEGER)"
            )
        await self.bot.dblog.commit()

    @nextcord.slash_command(description="Sets the log channel [per guild]")
    @application_checks.has_permissions(manage_channels=True)
    @cooldowns.cooldown(1, 20, bucket=cooldowns.SlashBucket.author)
    async def setlog(
        self,
        interaction: nextcord.Interaction,
        channel: GuildChannel = SlashOption(channel_types=[ChannelType.text]),
    ):
        if channel is None:
            channel = 0
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (interaction.guild.id,)
            )
            data = await cursor.fetchone()
            if data:
                if channel == 0:
                    await cursor.execute(
                        "UPDATE log SET logChannel = ? WHERE guild = ?",
                        (
                            0,
                            interaction.guild.id,
                        ),
                    )
                    await interaction.send("Removed log channel")
                else:
                    if not channel:
                        return await interaction.send("Cannot find mentioned channel")
                    channel = interaction.guild.get_channel(channel.id)
                    await cursor.execute(
                        "UPDATE log SET logChannel = ? WHERE guild = ?",
                        (
                            channel.id,
                            interaction.guild.id,
                        ),
                    )
                    await interaction.send(
                        f"The log channel has been set to {channel.mention}"
                    )
            else:
                channel = interaction.guild.get_channel(channel.id)
                if not channel:
                    return await interaction.send("Cannot find mentioned channel")
                await cursor.execute(
                    f"INSERT INTO log (guild, logChannel) VALUES (?,?)",
                    (interaction.guild.id, channel.id),
                )
                await interaction.send(
                    f"The log channel has been set to {channel.mention}"
                )
        await self.bot.dblog.commit()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (after.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = after.guild.get_channel(channelID)
        if not channel:
            return
        # nickname
        if before.display_name != after.display_name:
            embed = nextcord.Embed(
                title="Nickname Change",
                description=f"{after.mention}",
                color=0xFD9FA1,
                timestamp=datetime.datetime.utcnow(),
            )
            fields = [
                ("Before", before.display_name, False),
                ("After", after.display_name, False),
            ]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await channel.send(embed=embed)
        # role
        if before.roles != after.roles:
            embed = nextcord.Embed(
                title="Role Changes",
                description=f"{after.mention}",
                color=0xFD9FA1,
                timestamp=datetime.datetime.utcnow(),
            )
            fields = [
                ("Before", ", ".join([r.mention for r in before.roles]), False),
                ("After", ", ".join([r.mention for r in after.roles]), False),
            ]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await channel.send(embed=embed)

    # message edit
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (after.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = after.guild.get_channel(channelID)
        if not channel:
            return
        if not after.author.bot:
            try:
                if before.content != after.content:
                    embed = nextcord.Embed(
                        title="Message edit",
                        description=f"Edit by {after.author.mention} in {before.channel.mention} {before.jump_url}",
                        color=0xFD9FA1,
                        timestamp=datetime.datetime.utcnow(),
                    )
                    fields = [
                        ("Before", before.content, False),
                        ("After", after.content, False),
                    ]
                    for name, value, inline in fields:
                        embed.add_field(name=name, value=value, inline=inline)
                    await channel.send(embed=embed)
            except Exception:
                embed = nextcord.Embed(
                    title="Message edit",
                    description=f"Edit by {after.author.mention} in {before.channel.mention}\nSomeone edited a message that I was not able to log. Maybe it got deleted?",
                    color=0xFD9FA1,
                    timestamp=datetime.datetime.utcnow(),
                )
                await channel.send(embed=embed)

    # message delete
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (message.author.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = message.author.guild.get_channel(channelID)
        if not channel:
            return
        async for entry in message.guild.audit_logs(
            action=nextcord.AuditLogAction.message_delete, limit=1
        ):
            embed = nextcord.Embed(
                title="Message delete",
                description=f"Deleted in {message.channel.mention}\nMessage: {message.content}\nMessage author: {message.author.mention}",
                color=0xFD9FA1,
                timestamp=datetime.datetime.utcnow(),
            )
            if message.author.bot:
                embed.description = f"Deleted in {message.channel.mention}\nMessage: Bot message deleted\nMessage author: {message.author.mention}"
            i = 0
            try:
                await channel.send(embed=embed)
                while i < len(message.attachments):
                    await channel.send(message.attachments[i].proxy_url)
                    i += 1
                    return
            except IndexError:
                pass
                await channel.send(embed=embed)

    # member join
    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (member.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = member.guild.get_channel(channelID)
        if not channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1,
            description=f"{member.mention} {member.name}",
            title="Member Joined",
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon.url}")
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    # member kick or leave
    @commands.Cog.listener()
    async def on_member_remove(self, member: nextcord.Member):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (member.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = member.guild.get_channel(channelID)
        if not channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1,
            description=f"{member.mention} {member.name}",
            title="Member Left",
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon.url}")
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    # member ban
    @commands.Cog.listener()
    async def on_member_ban(self, guild: nextcord.Guild, member: nextcord.Member):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = guild.get_channel(channelID)
        if not channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1,
            description=f"{member.mention} {member.name}",
            title="Member Banned",
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_footer(text=f"{guild}", icon_url=f"{guild.icon.url}")
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    # member unban
    @commands.Cog.listener()
    async def on_member_unban(self, guild: nextcord.Guild, member: nextcord.Member):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = guild.get_channel(channelID)
        if not channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1,
            description=f"{member.mention} {member.name}",
            title="Member Unbanned",
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_footer(text=f"{guild}", icon_url=f"{guild.icon.url}")
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    # member voice channel
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: nextcord.Member, before, after):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (member.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        Channel = member.guild.get_channel(channelID)
        if not Channel:
            return
        if before.channel is None and after.channel:
            # User has connected to a VoiceChannel
            channel = after.channel
            embed = nextcord.Embed(
                color=0xFD9FA1,
                description=f"{member.mention} {member.name} joined voice channel {channel.mention}",
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_footer(
                text=f"{member.guild}", icon_url=f"{member.guild.icon.url}"
            )
            embed.timestamp = datetime.datetime.utcnow()
            await Channel.send(embed=embed)
        elif before.channel and after.channel is None:
            # User has disconnected from a VoiceChannel
            channel = before.channel
            embed = nextcord.Embed(
                color=0xFD9FA1,
                description=f"{member.mention} {member.name} left voice channel {channel.mention}",
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_footer(
                text=f"{member.guild}", icon_url=f"{member.guild.icon.url}"
            )
            embed.timestamp = datetime.datetime.utcnow()
            await Channel.send(embed=embed)
        elif before.channel is not after.channel:
            # User has changed VoiceChannels
            embed = nextcord.Embed(
                color=0xFD9FA1,
                description=f"{member.mention} {member.name} switched voice channels {before.channel.mention} -> {after.channel.mention}",
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_footer(
                text=f"{member.guild}", icon_url=f"{member.guild.icon.url}"
            )
            embed.timestamp = datetime.datetime.utcnow()
            await Channel.send(embed=embed)

    # channel create
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (channel.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        Channel = channel.guild.get_channel(channelID)
        if not Channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1, description=f"{channel.mention}", title="Channel Created"
        )
        embed.timestamp = datetime.datetime.utcnow()
        await Channel.send(embed=embed)

    # channel delete
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (channel.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        Channel = channel.guild.get_channel(channelID)
        if not Channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1, description=f"#{channel.name}", title="Channel Deleted"
        )
        embed.timestamp = datetime.datetime.utcnow()
        await Channel.send(embed=embed)

    # channel update
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (after.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        Channel = after.guild.get_channel(channelID)
        if not Channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1, description=f"{after.mention}", title="Channel Updated"
        )
        embed.timestamp = datetime.datetime.utcnow()
        if before.category != after.category:
            embed.add_field(
                name="Category Change",
                value=f"{after.mention}\nPrevious Category: {before.category}\nNew Category: {after.category}",
            )

        if before.permissions_synced != after.permissions_synced:
            embed.add_field(
                name="Permissions Synced Change",
                value=f"{after.mention}\nPrevious Permissions Synced: {before.permissions_synced}\nNew Permissions Synced: {after.permissions_synced}",
            )

        if before.changed_roles != after.changed_roles:
            embed.add_field(
                name="Role Access Change", value="Role access has been changed."
            )
            beforefields = [
                ("Before", ", ".join([r.mention for r in before.changed_roles]), False)
            ]
            for name, value, inline in beforefields:
                embed.add_field(name=name, value=value, inline=inline)
            afterfields = [
                ("After", ", ".join([r.mention for r in after.changed_roles]), False)
            ]
            for name, value, inline in afterfields:
                embed.add_field(name=name, value=value, inline=inline)

        if before.overwrites != after.overwrites:
            embed.add_field(
                name="Overwrites Change", value="Overwrites have been changed."
            )
            beforefields = [
                ("Before", ", ".join([r.mention for r in before.overwrites]), False)
            ]
            for name, value, inline in beforefields:
                embed.add_field(name=name, value=value, inline=inline)
            afterfields = [
                ("After", ", ".join([r.mention for r in after.overwrites]), False)
            ]
            for name, value, inline in afterfields:
                embed.add_field(name=name, value=value, inline=inline)

        if before.position != after.position:
            embed.add_field(
                name="Position Change",
                value=f"{after.mention}\nPrevious Position: {before.position}\nNew Position: {after.position}",
            )

        if before.name != after.name:
            embed.add_field(
                name="Name Change",
                value=f"{after.mention}\nPrevious Name: {before.name}\nNew Name: {after.name}",
            )

        await Channel.send(embed=embed)

    # role create
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (role.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = role.guild.get_channel(channelID)
        if not channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1, description=f"{role.mention}", title="Role Created"
        )
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    # role update
    @commands.Cog.listener()
    async def on_guild_role_update(self, before: nextcord.Role, after: nextcord.Role):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (after.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = after.guild.get_channel(channelID)
        if not channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1, title="Role Updated", timestamp=datetime.datetime.utcnow()
        )
        if before.name != after.name:
            embed.add_field(
                name="Name Change",
                value=f"{after.mention}\nPrevious Name: {before.name}\nNew Name: {after.name}",
            )
        if before.color != after.color:
            embed.add_field(
                name="Color Change",
                value=f"{after.mention}\nPrevious Color: {hex(before.color.value)} \nNew Color: {hex(after.color.value)}",
            )
        if before.permissions != after.permissions:
            embed.add_field(
                name="Permissions Change",
                value=f"{after.mention}\nPrevious Permissions: {before.permissions.value} \nNew Permissions: {after.permissions.value}",
            )
        if before.position != after.position:
            embed.add_field(
                name="Position Change",
                value=f"{after.mention}\nPrevious Position: {before.position}\nNew Position: {after.position}",
            )
        await channel.send(embed=embed)

    # role delete
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (role.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = role.guild.get_channel(channelID)
        if not channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1, description=f"{role.name}", title="Role Deleted"
        )
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    # invite delete
    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (invite.guild.id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = invite.guild.get_channel(channelID)
        if not channel:
            return
        embed = nextcord.Embed(color=0xFD9FA1, title="Invite Link Deleted")
        async for entry in invite.guild.audit_logs(
            action=nextcord.AuditLogAction.invite_delete
        ):
            embed.description = f"Deleted by: {entry.user}\n{invite}"
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    # bulk message delete
    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        async with self.bot.dblog.cursor() as cursor:
            await cursor.execute(
                "SELECT logChannel FROM log WHERE guild = ?", (payload.guild_id,)
            )
            channelID = await cursor.fetchone()
        if not channelID:
            return
        channelID = channelID[0]
        channel = payload.channel_id
        if not channel:
            return
        embed = nextcord.Embed(
            color=0xFD9FA1,
            title="Bulk Message Delete",
            timestamp=datetime.datetime.utcnow(),
            description=f"Channel: <#{payload.channel_id}>\n{len(payload.message_ids)} messages deleted",
        )
        await self.bot.get_channel(channelID).send(embed=embed)


def setup(bot):
    bot.add_cog(LogCog(bot))
    print("Log is loaded")
