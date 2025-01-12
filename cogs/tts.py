import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from libs.models import (
    PostTtsInferenceTextBody,
    PostTtsInferenceTextResponse200,
)
from libs.api.tts import post_tts_inference_text
from utils import get_buffer

# Constants
VOICE_CHOICES = [
    app_commands.Choice(name="Sarah_American", value="EXAVITQu4vr4xnSDxMaL"),
    app_commands.Choice(name="Charlotte_Swedish", value="XB0fDUnXU5powFXDhCwa"),
    app_commands.Choice(name="Alice_British", value="Xb7hH8MSUJpSbSDYk0k2"),
    app_commands.Choice(name="Cewe_Cakep", value="bUpviYlwHTokA1nrQQGA"),
    app_commands.Choice(name="Scarlett", value="tjRIRog2dZyjowKmVpka"),
]

EMBED_COLOR_SUCCESS = 0xBEBEFE
EMBED_COLOR_ERROR = 0xE02B2B
AUDIO_FILENAME = "gen_tts.mp3"


class Tts(commands.Cog, name="TTS"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="tts",
        description="Generate a TTS audio from the given text.",
    )
    @app_commands.describe(
        text="The text to generate the TTS audio from.",
        voice="The voice to use for generating the TTS audio.",
    )
    @app_commands.choices(voice=VOICE_CHOICES)
    async def tts(
        self,
        ctx: Context,
        text: str,
        voice: app_commands.Choice[str],
    ) -> None:
        body = PostTtsInferenceTextBody(
            text=text,
            voice_id=voice.value,
        )
        await ctx.defer()
        resp = await post_tts_inference_text.asyncio(
            client=self.bot.api_client, body=body
        )

        if isinstance(resp, PostTtsInferenceTextResponse200):
            embed = discord.Embed(
                description=f"`{text[:4096]}`",
                color=EMBED_COLOR_SUCCESS,
            )
            buffer = await get_buffer(resp.result.audios[0])
            await ctx.send(
                embed=embed,
                file=discord.File(buffer, filename=AUDIO_FILENAME),
            )
        else:
            embed = discord.Embed(
                title="Error!",
                description=resp.message or "An error occurred.",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tts(bot))
