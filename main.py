import json
import logging
import os
import random
import sys
from pathlib import Path

import aiosqlite
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

from dotenv import load_dotenv

from database.manager import DatabaseManager

# API client
from libs.client import AuthenticatedClient

# Constants
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DATABASE_DIR = BASE_DIR / "database"
COGS_DIR = BASE_DIR / "cogs"
LOG_FILE = BASE_DIR / "discord.log"
# get process PID
PID = os.getpid()

if not CONFIG_PATH.is_file():
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(CONFIG_PATH) as file:
        config = json.load(file)

intents = discord.Intents.default()
intents.message_content = True


class LoggingFormatter(logging.Formatter):
    # Colors
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    # Styles
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, self.reset)
        fmt = (
            f"{self.black}{self.bold}{{asctime}}{self.reset} "
            f"{log_color}{{levelname:<8}}{self.reset} "
            f"{self.green}{self.bold}{{name}}{self.reset} {{message}}"
        )
        formatter = logging.Formatter(fmt, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())

file_handler = logging.FileHandler(filename=LOG_FILE, encoding="utf-8", mode="w")
file_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            commands.when_mentioned_or(config["prefix"]),
            intents=intents,
            help_command=None,
        )
        self.logger = logger
        self.config = config
        self.database = None

        self.api_client = AuthenticatedClient(
            base_url=os.getenv("API_BASE_URL"), token=os.getenv("API_TOKEN")
        )

    async def init_db(self) -> None:
        db_path = DATABASE_DIR / "database.db"
        schema_path = DATABASE_DIR / "schema.sql"
        async with aiosqlite.connect(db_path) as db:
            with open(schema_path) as file:
                await db.executescript(file.read())
            await db.commit()

    async def load_cogs(self) -> None:
        for file in COGS_DIR.glob("*.py"):
            extension = file.stem
            try:
                await self.load_extension(f"cogs.{extension}")
                self.logger.info(f"Loaded extension '{extension}'")
            except Exception as e:
                self.logger.error(
                    f"Failed to load extension {extension}\n{type(e).__name__}: {e}"
                )

    @tasks.loop(minutes=1.0)
    async def status_task(self) -> None:
        await self.change_presence(
            activity=discord.Streaming(
                name="Live Development live-term.lovita.io",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            )
        )

    @status_task.before_loop
    async def before_status_task(self) -> None:
        await self.wait_until_ready()
        await self.tree.sync()

    async def setup_hook(self) -> None:
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"PID: ${PID}")
        self.logger.info("-------------------")
        await self.init_db()
        await self.load_cogs()

        self.status_task.start()

        db_connection = await aiosqlite.connect(DATABASE_DIR / "database.db")
        self.database = DatabaseManager(connection=db_connection)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_command_completion(self, ctx: Context) -> None:
        command = ctx.command.qualified_name.split()[0]
        if ctx.guild:
            self.logger.info(
                f"Executed {command} in {ctx.guild.name} (ID: {ctx.guild.id}) by {ctx.author} (ID: {ctx.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {command} by {ctx.author} (ID: {ctx.author.id}) in DMs"
            )

    async def on_command_error(
        self, ctx: Context, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            retry = self.format_retry(error.retry_after)
            embed = discord.Embed(
                description=f"**Please slow down** - You can use this command again in {retry}.",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                description="You are not the owner of the bot!", color=0xE02B2B
            )
            await ctx.send(embed=embed)
            self.log_owner_error(ctx)
        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                description=f"You are missing the permission(s) `{perms}` to execute this command!",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                description=f"I am missing the permission(s) `{perms}` to fully perform this command!",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!",
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(
                title="Error!",
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, discord.NotFound):
            await ctx.message.add_reaction("❌")
        else:
            embed = discord.Embed(
                title="Error!",
                description="Something went wrong. Please try again later.",
                # description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)

    def format_retry(self, retry_after: float) -> str:
        minutes, seconds = divmod(retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        parts = []
        if hours:
            parts.append(f"{int(hours)} hours")
        if minutes:
            parts.append(f"{int(minutes)} minutes")
        if seconds:
            parts.append(f"{int(seconds)} seconds")
        return " ".join(parts)

    def log_owner_error(self, ctx: Context) -> None:
        if ctx.guild:
            self.logger.warning(
                f"{ctx.author} (ID: {ctx.author.id}) tried to execute an owner only command in {ctx.guild.name} (ID: {ctx.guild.id}), but is not an owner."
            )
        else:
            self.logger.warning(
                f"{ctx.author} (ID: {ctx.author.id}) tried to execute an owner only command in DMs, but is not an owner."
            )


load_dotenv()

bot = DiscordBot()

try:
    bot.run(os.getenv("TOKEN"))
except KeyboardInterrupt:
    bot.logger.info("Shutting down bot...")
    sys.exit()
