
import asyncio
import json
from pathlib import Path
from curl_cffi.requests import AsyncSession
import aiofiles

async def download_file(session, url, output_path):
    async with session.stream("GET", url) as response:
        async with aiofiles.open(output_path, 'wb') as f:
            async for chunk in response.aiter_content(chunk_size=8192):
                await f.write(chunk)

async def fetch_media(session, url):
    response = await session.post(
        "https://api.seekin.ai/ikool/media/download",
        json={"url": url},
        headers={
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://www.seekin.ai",
            "referer": "https://www.seekin.ai/",
        },
        impersonate="chrome"
    )
    return response.json()

async def process_url(url, proxy, output_dir):
    try:
        async with AsyncSession(impersonate="chrome", proxies={"http": proxy, "https": proxy}) as session:
            data = await fetch_media(session, url)
            
            if data['code'] != '0000':
                print(f"Failed to fetch {url}: {data['msg']}")
                return
            
            title = data['data']['title']
            medias = data['data']['medias']
            
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            
            best_video = None
            best_size = 0
            
            for media in medias:
                if media.get('format') and 'mp4' in media.get('format', '').lower():
                    size = media.get('fileSize', 0)
                    if size and size > best_size:
                        best_video = media
                        best_size = size
            
            if not best_video:
                best_video = next((m for m in medias if m.get('format') and 'mp4' in m.get('format', '').lower()), None)
            
            if not best_video:
                print(f"No video found for {url}")
                return
            
            file_ext = '.mp4'
            output_path = output_dir / f"{safe_title}{file_ext}"
            
            print(f"Downloading: {title}")
            await download_file(session, best_video['url'], output_path)
            print(f"Saved: {output_path}")
        
    except Exception as e:
        print(f"Error processing {url}: {e}")

async def main():
    input_file = Path("input.txt")
    proxy_file = Path("proxies.txt")
    output_dir = Path("output")
    
    output_dir.mkdir(exist_ok=True)
    
    urls = input_file.read_text().strip().split('\n')
    proxies = proxy_file.read_text().strip().split('\n')
    
    tasks = []
    for i, url in enumerate(urls):
        proxy = proxies[i % len(proxies)]
        tasks.append(process_url(url.strip(), proxy, output_dir))
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())



