import aiohttp
import asyncio


async def check_key():
    url = 'http://0.0.0.0:8080/api-key'
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={'api-key': 'lrlDtjtHZiZQjFdCJXtkiFLwELkvYAmjZuSDUHKdPngGnFdTWrqPXRLUSrAzYguv'})\
                as response:
            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])
            print(await response.json())


async def main():

    async with aiohttp.ClientSession() as session:
        async with session.get('http://0.0.0.0:8080/ping') as response:

            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])

            html = await response.text()
            print("Body:", html[:150], "...")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_until_complete(check_key())
