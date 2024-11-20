from pyrogram import Client, filters


@Client.on_message(filters.command("userinfo"))
async def userinfo(client, message):
    # Extract user ID from the command (e.g., /userinfo 123456789)
    if len(message.command) != 2:
        await message.reply("Please provide a user ID. Example: /userinfo 123456789")
        return

    user_id = message.command[1]
    
    try:
        # Fetch user details using Pyrogram's get_users method
        user = await client.get_users(int(user_id))
        
        # Build the response with user details
        response = (
            f"User Information:\n"
            f"ID: {user.id}\n"
            f"First Name: {user.first_name or 'Not Available'}\n"
            f"Last Name: {user.last_name or 'Not Available'}\n"
            f"Username: @{user.username or 'Not Available'}\n"
            f"Phone Number: {user.phone_number or 'Not Available'}\n"
            f"Is Bot: {'Yes' if user.is_bot else 'No'}"
        )
        await message.reply(response)
    except Exception as e:
        await message.reply(f"Error: Could not find user with ID {user_id}. Please check the ID and try again.\n\nDetails: {e}")

