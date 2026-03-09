#!/usr/bin/env ./venv/bin/python3
import asyncio
import telnetlib3
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv(override=True)

# Clean credentials and remove any spaces
HOST = os.getenv("TELNET_HOST", "127.0.0.1").strip()
USER = os.getenv("TELNET_USER", "admin").strip()
PASS = os.getenv("TELNET_PASS", "password").strip()
PORT = int(os.getenv("TELNET_PORT", 23))

async def query_onu_status(sn: str = None):
    """
    Connects to OLT via Telnet and queries ONU status.
    If sn is provided, runs 'show onu by-sn <sn>'.
    Returns the OLT output as a string.
    """
    output_log = []
    
    async def expect(reader, prompt, timeout=15):
        buffer = ""
        try:
            while prompt not in buffer:
                char = await asyncio.wait_for(reader.read(1), timeout=timeout)
                if not char:
                    break
                buffer += char
        except asyncio.TimeoutError:
            pass
        return buffer

    try:
        reader, writer = await telnetlib3.open_connection(HOST, PORT)
        
        # 1. Login
        await expect(reader, 'User name:')
        await asyncio.sleep(0.5)
        writer.write(USER + '\r')
        
        await expect(reader, 'Password:')
        await asyncio.sleep(0.5)
        writer.write(PASS + '\r')

        # 2. Commands
        await expect(reader, '>')
        writer.write('enable\r')
        await asyncio.sleep(0.3)
        
        await expect(reader, '#')
        writer.write('conf\r')
        await asyncio.sleep(0.3)

        # 3. Specific Query
        await expect(reader, '(config)#')
        if sn:
            cmd = f'show onu by-sn {sn}\r'
        else:
            cmd = 'show version\r' # fallback
            
        writer.write(cmd)
        
        # Capture result (we wait for the prompt again)
        result = await expect(reader, '(config)#', timeout=20)
        output_log.append(result)

        writer.close()
        return "".join(output_log)

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test execution
    res = asyncio.run(query_onu_status())
    print(res)
