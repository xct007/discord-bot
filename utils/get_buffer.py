import aiohttp
import io


async def get_buffer(url: str) -> io.BytesIO:
	try:
		async with aiohttp.ClientSession() as session:
			async with session.get(url) as response:
				if response.status != 200:
					raise RuntimeError(f"Failed to fetch {url}")
				return io.BytesIO(await response.read())
	except aiohttp.ClientError as e:
		raise RuntimeError(f"Failed to fetch {url}") from e
