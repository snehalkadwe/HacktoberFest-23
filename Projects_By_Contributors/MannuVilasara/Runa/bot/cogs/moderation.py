import nextcord
import datetime
import humanfriendly

from nextcord.ext import *
from nextcord import *


class ModCog(commands.Cog, name="Moderation"):
    """purge, kick, ban, timeout, untimeout, nickname, dm, message"""

    def __init__(self, bot):
        self.bot = bot

    # purge command
    @nextcord.slash_command(
        description="Purges a number of messages from a channel, max 100. Please specify a reason."
    )
    @application_checks.has_permissions(manage_channels=True)
    async def purge(self, interaction, *, number: int, reason):
        deleted = await interaction.channel.purge(limit=number)
        await interaction.send(
            f"Messages purged by {interaction.user.mention}: `{len(deleted)}` (max is 100)\n Reason: {reason}"
        )

    # kick command
    @nextcord.slash_command(description="Kicks a user. Please specify the reason.")
    @application_checks.has_permissions(manage_channels=True)
    async def kick(self, interaction, user: nextcord.Member, *, reason=None):
        try:
            await user.send(
                f"You have been kicked from {user.guild} because of: \n {reason}."
            )
            await interaction.guild.kick(user=user, reason=reason)
        except Exception:
            await interaction.send("Failed to DM the user, oh well.")
            await interaction.guild.kick(user=user, reason=reason)
        embed = nextcord.Embed(
            title="Kicked User",
            description=f"I have successfully kicked `{user}` for the reason of: `{reason}`",
            color=0xFD9FA1,
        )
        await interaction.send(embed=embed)

    # ban command
    @nextcord.slash_command(description="Bans a user. Please specify the reason.")
    @application_checks.has_permissions(administrator=True)
    async def ban(self, interaction, user: nextcord.User, *, reason=None):
        try:
            await user.send(
                f"You have been banned from {user.guild} because of: \n {reason}."
            )
            await interaction.send(
                f"I have DMed {user.name} that they have been banned for: {reason}"
            )
        except Exception:
            await interaction.send("Failed to DM the user, oh well.")
        await interaction.guild.ban(user=user, reason=reason)
        embed = nextcord.Embed(
            title="Banned User",
            description=f"I have successfully banned `{user}` for the reason of: `{reason}`",
            color=0xFD9FA1,
        )
        await interaction.send(embed=embed)

    # unban command
    @nextcord.slash_command(description="Unbans a user. Please specify the reason.")
    @application_checks.has_permissions(administrator=True)
    async def unban(self, interaction, user: nextcord.User, *, reason=None):
        await interaction.guild.unban(user=user, reason=reason)
        title = f"Unbanned {user}"
        description = (
            f"I have successfully unbanned {user.mention} for reason: {reason}."
        )
        embed = nextcord.Embed(title=title, description=description, color=0xFD9FA1)
        await interaction.send(embed=embed)

    # timeout command
    @nextcord.slash_command(description="Timeouts a user. Please specify the reason.")
    @application_checks.has_permissions(administrator=True)
    async def timeout(self, interaction, member: nextcord.Member, time, *, reason):
        times = humanfriendly.parse_timespan(time)
        await member.edit(
            timeout=nextcord.utils.utcnow() + datetime.timedelta(seconds=times)
        )
        await interaction.send(
            f"{member.mention} has been timed out for {time} because of {reason}. What a meanie."
        )
        try:
            await member.send(
                f"You have been timed out in {interaction.guild.name} for {time} because of: \n {reason}"
            )
        except Exception:
            await interaction.send("Failed to DM the user, oh well.")

    # untimeout command
    @nextcord.slash_command(description="Untimeouts a user. Please specify the reason.")
    @application_checks.has_permissions(administrator=True)
    async def untimeout(self, interaction, member: nextcord.Member, *, reason):
        await member.edit(timeout=None)
        await interaction.send(
            f"{member.mention} has been untimed out because of {reason}. Yay!"
        )
        try:
            await member.send(
                f"You have been untimed out in the {interaction.guild.name} because of: \n {reason}."
            )
        except Exception:
            await interaction.send("Failed to DM the user, oh well.")

    # change nickname
    @nextcord.slash_command(
        description="Changes the nickname of a user. Please specify the reason."
    )
    @application_checks.has_permissions(administrator=True)
    async def nickname(
        self, interaction, user: nextcord.Member, *, reason, nickname=None
    ):
        nickname = nickname.strip()
        await user.edit(nick=nickname)
        await interaction.send(
            f"I have changed {user.mention}'s nickname to: {nickname} for reason: {reason}."
        )
        try:
            await user.send(
                f"Your nickname in the {interaction.guild.name} has been changed to: {nickname} because: {reason}."
            )
        except Exception:
            await interaction.send(f"I was not able to DM {user.mention}.")

    # send a message
    @nextcord.slash_command(description="Sends a message from Runa to a channel.")
    @application_checks.has_permissions(administrator=True)
    async def message(self, interaction, channel: nextcord.TextChannel, *, message):
        await channel.send(f"A mod has sent the message: {message}")
        await interaction.send(
            f"I have sent the message: `{message}` to the channel: {channel.mention}"
        )

    # dm user
    @nextcord.slash_command(description="DMs a user a message from Runa.")
    @application_checks.has_permissions(administrator=True)
    async def dm(
        self,
        interaction,
        user: nextcord.Member,
        *,
        message,
        attachment: nextcord.Attachment = None,
    ):
        try:
            await user.send(
                f"You have received a message from {interaction.guild.name}: \n{message}"
            )
            await interaction.send(f"I have sent {user.mention} the message: {message}")
            if attachment:
                await user.send(attachment)
                await interaction.send(f"{attachment}")
        except Exception:
            await interaction.send(f"Failed to DM {user.mention}.")


def setup(bot):
    bot.add_cog(ModCog(bot))
    print("Moderation is loaded")
