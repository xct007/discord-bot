import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from libs.models import (
    PostSdapiTxt2ImgBody,
    PostSdapiTxt2ImgResponse200,
    PostSdapiTxt2ImgBodyAlgorithmType,
    PostSdapiTxt2ImgBodyUseKarrasSigmas,
)
from libs.api.sdapi import post_sdapi_txt2img
from utils import get_buffer

# Constants
MODEL_CHOICES = [
    app_commands.Choice(name="DreamShaper", value="dreamshaper"),
    app_commands.Choice(name="MeinaMix", value="meinamix"),
    app_commands.Choice(name="MeinaUnreal", value="meina-unreal"),
    app_commands.Choice(name="NukeColorMaxAnime", value="nuke-colormax-anime"),
    app_commands.Choice(name="RealisticVisionV5", value="real-vis-v5"),
]

EMBED_COLOR_SUCCESS = 0xBEBEFE
EMBED_COLOR_ERROR = 0xE02B2B
IMAGE_FILENAME = "image.png"


class SdApi(commands.Cog, name="SDAPI"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="imagine",
        description="Generate an image from the given text prompt.",
    )
    @app_commands.describe(
        prompt="The text prompt to generate an image from.",
        model="The model to use for generating the image.",
    )
    @app_commands.choices(model=MODEL_CHOICES)
    async def imagine(
        self,
        ctx: Context,
        prompt: str,
        model: app_commands.Choice[str],
    ) -> None:
        body = PostSdapiTxt2ImgBody(
            prompt=prompt,
            model_id=model.value,
            width=512,
            height=512,
            num_inference_steps=25,
            scheduler="DDPMScheduler",
            clip_skip=2,
            use_karras_sigmas=PostSdapiTxt2ImgBodyUseKarrasSigmas.YES,
            algorithm_type=PostSdapiTxt2ImgBodyAlgorithmType.DPMSOLVER,
        )
        await ctx.defer()
        resp = await post_sdapi_txt2img.asyncio(client=self.bot.api_client, body=body)

        if isinstance(resp, PostSdapiTxt2ImgResponse200):
            embed = discord.Embed(
                description=f"Prompt: `{prompt}`\nModel: `{model.name}`",
                color=EMBED_COLOR_SUCCESS,
            )
            await asyncio.sleep(float(resp.result.generation_time))
            # buffer = await get_buffer(resp.result.images[0])
            buffer = None
            # or retry 3 times
            for _ in range(3):
                try:
                    buffer = await get_buffer(resp.result.images[0])
                    await asyncio.sleep(1)
                    break
                except Exception:
                    pass

            await ctx.send(
                embed=embed,
                file=discord.File(buffer, filename=IMAGE_FILENAME),
            )
        else:
            embed = discord.Embed(
                title="Error!",
                description=resp.message or "An error occurred.",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SdApi(bot))
