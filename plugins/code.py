from pyrogram import Client, filters
from database.users_chats_db import db
from info import *
import pandas as pd


@Client.on_message(filters.command("export_users"))
async def export_users(client, message):
    # Check if the sender is an admin
    if message.from_user.id not in ADMINS:
        await message.reply("You are not authorized to use this command.")
        return

    # Fetch user IDs from MongoDB asynchronously
    try:
        users_cursor = await db.get_all_users()  # Await the coroutine
        user_ids = [user["id"] for user in await users_cursor.to_list(length=None)]  # Use 'id' instead of 'user_id'
    except Exception as e:
        await message.reply(f"Error fetching users: {e}")
        return

    if not user_ids:
        await message.reply("No user data found in the database.")
        return

    # Prepare a list for user data
    users_data = []

    for user_id in user_ids:
        try:
            # Fetch user info using Telegram API
            user = await client.get_users(user_id)
            users_data.append({
                "User ID": user.id,
                "Username": user.username or "N/A",
                "First Name": user.first_name or "N/A",
                "Last Name": user.last_name or "N/A",
                "Phone Number": user.phone_number or "N/A",
            })
        except Exception as e:
            # Log errors and skip the user if something goes wrong
            print(f"Error fetching data for user_id {user_id}: {e}")
            continue

    if not users_data:
        await message.reply("Could not fetch any user details.")
        return

    # Create a DataFrame for user data
    df = pd.DataFrame(users_data)

    # Generate an Excel file
    file_path = "user_data.xlsx"
    df.to_excel(file_path, index=False)

    # Send the Excel file to the admin
    await client.send_document(chat_id=message.chat.id, document=file_path)
    await message.reply("User data has been exported successfully.")
