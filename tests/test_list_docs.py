#!/usr/bin/env python
"""Test the list_available_documents function directly."""

import asyncio
import os
import sys

# Add the project to path
sys.path.insert(0, os.path.dirname(__file__))

from word_document_server.tools import document_tools

async def main():
    directory = r"C:\Users\DavidSant\Contract Tools\SightWatcher"
    result = await document_tools.list_available_documents(directory)
    print("Result from list_available_documents:")
    print(result)
    print("\n" + "="*80 + "\n")
    
    # Now manually list and check each file
    print("Manual filesystem check:")
    for entry in os.scandir(directory):
        if entry.name.endswith('.docx'):
            exists = os.path.isfile(entry.path)
            print(f"  {entry.name}: exists={exists}, isfile={entry.is_file()}")

if __name__ == "__main__":
    asyncio.run(main())
