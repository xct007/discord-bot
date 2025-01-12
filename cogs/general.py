import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from time import sleep

# import modules from the api libs
from libs.models import (
    PostSdapiTxt2ImgBody,
    PostSdapiTxt2ImgResponse200,
    PostSdapiTxt2ImgBodyAlgorithmType,
    PostSdapiTxt2ImgBodyUseKarrasSigmas,
)
from libs.api.sdapi import post_sdapi_txt2img
from utils import get_buffer


class FeedbackForm(discord.ui.Modal, title="Feedback"):
    feedback = discord.ui.TextInput(
        label="What do you think about this bot?",
        style=discord.TextStyle.long,
        placeholder="Type your answer here...",
        required=True,
        max_length=256,
    )

    async def on_submit(self, interaction: discord.Interaction):
        self.answer = self.feedback.value
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Thank you for your feedback!",
                color=0xBEBEFE,
            ),
            ephemeral=True,
        )
        app_owner = (await interaction.client.application_info()).owner
        await app_owner.send(
            embed=discord.Embed(
                title="New Feedback",
                description=f"{interaction.user} (<@{interaction.user.id}>) submitted feedback:\n```\n{self.answer}\n```",
                color=0xBEBEFE,
            )
        )


class General(commands.Cog, name="general"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.setup_context_menus()

    def setup_context_menus(self):
        self.bot.tree.add_command(
            app_commands.ContextMenu(name="Grab ID", callback=self.grab_id)
        )
        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name="Remove spoilers", callback=self.remove_spoilers
            )
        )

    async def remove_spoilers(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        embed = discord.Embed(
            title="Message without spoilers",
            description=message.content.replace("||", ""),
            color=0xBEBEFE,
        )
        spoiler_attachment = next(
            (att for att in message.attachments if att.is_spoiler()), None
        )
        if spoiler_attachment:
            embed.set_image(url=spoiler_attachment.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def grab_id(
        self, interaction: discord.Interaction, user: discord.User
    ) -> None:
        embed = discord.Embed(
            description=f"The ID of {user.mention} is `{user.id}`.",
            color=0xBEBEFE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="help", description="List all commands the bot has loaded."
    )
    async def help(self, ctx: Context) -> None:
        prefix = self.bot.config.get("prefix", "/")
        embed = discord.Embed(
            title="Help", description="List of available commands:", color=0xBEBEFE
        )
        for cog_name, cog in self.bot.cogs.items():
            if cog_name == "owner" and not await self.bot.is_owner(ctx.author):
                continue
            commands_list = [
                f"{prefix}{cmd.name} - {cmd.description.splitlines()[0]}"
                for cmd in cog.get_commands()
            ]
            embed.add_field(
                name=cog_name.capitalize(),
                value=f"```{chr(10).join(commands_list)}```",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="serverinfo", description="Get information about the server."
    )
    @commands.guild_only()
    async def serverinfo(self, ctx: Context) -> None:
        guild = ctx.guild
        roles = ", ".join([role.name for role in guild.roles[:50]]) + (
            f", and {len(guild.roles) - 50} more" if len(guild.roles) > 50 else ""
        )
        embed = discord.Embed(title="Server Information", color=0xBEBEFE)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Server ID", value=guild.id)
        embed.add_field(name="Member Count", value=guild.member_count)
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name=f"Roles ({len(guild.roles)})", value=roles)
        embed.set_footer(text=f"Created on {guild.created_at.strftime('%Y-%m-%d')}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ping", description="Check if the bot is alive.")
    async def ping(self, ctx: Context) -> None:
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {latency}ms.",
            color=0xBEBEFE,
        )
        await ctx.send(embed=embed)

    @app_commands.command(
        name="feedback", description="Submit feedback for the bot's owners."
    )
    async def feedback(self, interaction: discord.Interaction) -> None:
        feedback_form = FeedbackForm()
        await interaction.response.send_modal(feedback_form)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
