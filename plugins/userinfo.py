from pyrogram import Client, enums
from pyrogram.types import Message


@Client.on_message(filters.command("userinfo") & filters.private)
async def userinfo(client: Client, message: Message):
    try:
        # Fetch the target user
        if message.reply_to_message:
            user = await client.get_users(message.reply_to_message.from_user.id)
        elif len(message.command) > 1:
            user = await client.get_users(message.command[1])
        else:
            user = await client.get_users(message.from_user.id)

        # Extract user details
        details = [
            f"👤 **User Information**",
            f"**ID:** {user.id}",
            f"**First Name:** {user.first_name or 'N/A'}",
            f"**Last Name:** {user.last_name or 'N/A'}",
            f"**Username:** @{user.username}" if user.username else "**Username:** N/A",
            f"**Is Bot:** {'Yes' if user.is_bot else 'No'}",
            f"**Is Verified:** {'Yes' if user.is_verified else 'No'}",
            f"**Is Premium:** {'Yes' if user.is_premium else 'No'}",
            f"**Last Seen:** {user.status}" if user.status else "**Last Seen:** N/A",
        ]

        # Send the response
        await message.reply_text("\n".join(details), parse_mode=enums.ParseMode.MARKDOWN)

    except Exception as e:
        # Handle errors gracefully
        await message.reply_text(f"⚠️ Unable to fetch user info.\nError: {str(e)}")

# Example usage:
# /userinfo
# /userinfo [UserID/Username]
# /userinfo (reply to a message)