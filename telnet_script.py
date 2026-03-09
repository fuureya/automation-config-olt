#!/usr/bin/env ./venv/bin/python3
import asyncio
import telnetlib3
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

# Clean credentials and remove any spaces
HOST = os.getenv("TELNET_HOST", "127.0.0.1").strip()
USER = os.getenv("TELNET_USER", "admin").strip()
PASS = os.getenv("TELNET_PASS", "password").strip()
PORT = int(os.getenv("TELNET_PORT", 23))

async def telnet_client():
    print(f"Connecting to {HOST}:{PORT} using telnetlib3...")
    try:
        # Connect to the OLT
        reader, writer = await telnetlib3.open_connection(HOST, PORT)
        
        async def expect(prompt, timeout=15):
            buffer = ""
            try:
                while prompt not in buffer:
                    char = await asyncio.wait_for(reader.read(1), timeout=timeout)
                    if not char:
                        break
                    buffer += char
                    # Print without extra spaces to see exact OLT output
                    print(char, end='', flush=True)
            except asyncio.TimeoutError:
                print(f"\n[Warning] Timeout waiting for: '{prompt}'")
            return buffer

        # 1. Wait for User name prompt
        await expect('User name:')
        await asyncio.sleep(0.5)
        # Using '\r' instead of '\r\n' to avoid double-submitting (which causes empty password/fail)
        writer.write(USER + '\r')
        print(f" [Sent Username]")

        # 2. Wait for Password prompt
        await expect('Password:')
        await asyncio.sleep(0.5)
        writer.write(PASS + '\r')
        print(f" [Sent Password]")

        # 3. Wait for Command Prompt (successful login)
        # Some OLTs might stay at '>' or '#'
        res = await expect('>', timeout=10)
        
        if 'Authentication fail' in res:
            print("\n[Error] Login failed. Please check your credentials in .env")
            return

        print("\nLogin Successful!")
        
        # Send test command
        await asyncio.sleep(0.5)
        writer.write('enable \r')

        await asyncio.sleep(0.5)
        writer.write('conf \r')
        
        # Read response for a bit
        await expect('>', timeout=5)

        # property access for waiter_closed (Future)
        await writer.protocol.waiter_closed
        print("\nConnection closed.")

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(telnet_client())
    except KeyboardInterrupt:
        print("\nStopped by user.")
