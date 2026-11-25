import asyncio
import http.client
import json
import re
import sys
from urllib.parse import urlsplit

import pytest


@pytest.mark.slow
def test_serve_and_comments(tmp_path):
    async def exercise():
        doc = tmp_path / "page.md"
        doc.write_text("# Title\n", encoding="utf-8")
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "tavle",
            "serve",
            str(doc),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            assert process.stdout is not None
            url = (
                (await asyncio.wait_for(process.stdout.readline(), 10)).decode().strip()
            )
            parsed = urlsplit(url)
            assert parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
            conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
            try:
                conn.request("GET", "/")
                response = conn.getresponse()
                assert response.status == 200
                assert response.getheader("Content-Security-Policy")
                page = response.read().decode()
                match = re.search(r'name="varde-token" content="([^"]+)"', page)
                assert match is not None
                body = json.dumps({"anchor": "title", "quote": "Title", "text": "note"})
                headers = {
                    "Content-Type": "application/json",
                    "Origin": url.rstrip("/"),
                }
                conn.request("POST", "/comments", body, headers)
                response = conn.getresponse()
                assert response.status == 403
                response.read()
                headers["X-Varde-Token"] = match.group(1)
                conn.request("POST", "/comments", body, headers)
                response = conn.getresponse()
                assert response.status == 201
                response.read()
            finally:
                conn.close()
            listing = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "tavle",
                "comments",
                str(doc),
                "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(listing.communicate(), 10)
                assert listing.returncode == 0, stderr.decode()
                assert json.loads(stdout)["comments"][0]["text"] == "note"
            finally:
                if listing.returncode is None:
                    listing.kill()
                    await listing.communicate()
        finally:
            if process.returncode is None:
                process.terminate()
            try:
                await asyncio.wait_for(process.communicate(), 5)
            except TimeoutError:
                process.kill()
                await process.communicate()

    asyncio.run(exercise())
