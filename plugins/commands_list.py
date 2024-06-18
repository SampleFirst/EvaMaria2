import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message


def extract_commands_from_file(file_path):
    commands = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.search(r'filters\.command\(["\'](\w+)["\']', line)
            if match:
                commands.append(match.group(1))
    return commands


@Client.on_message(filters.command("commands"))
async def list_commands(client: Client, message: Message):
    repo_path = "plugins"
    all_commands = []

    for root, dirs, files in os.walk(repo_path):
        for file in sorted(files):  # Sorting files to ensure consistent order
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                all_commands.extend(extract_commands_from_file(file_path))
                
    # Removing duplicates while maintaining order
    seen = set()
    unique_commands = []
    for command in all_commands:
        if command not in seen:
            seen.add(command)
            unique_commands.append(command)
    
    await message.reply_text("\n".join(f"/{command}" for command in unique_commands))
