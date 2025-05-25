from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from database.users_chats_db import db
from info import ADMINS

DEFAULT_VERIFICATION = {
    'short': "1",
    'date': "1999-12-31",
    'time': "23:59:59"
}

# Command handler
@Client.on_message(filters.command("updateverify") & filters.user(ADMINS))
async def update_verification_at_once(client, message):
    args = message.text.split()
    if len(args) > 1:
        # Update specific user
        try:
            user_id = int(args[1])
            await db.update_verification(user_id, **DEFAULT_VERIFICATION)
            await message.reply(f"Verification status updated for user {user_id}.")
        except Exception as e:
            await message.reply(f"Error: {e}")
    else:
        # No user_id provided: Ask for confirmation to update all users
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Yes", callback_data="confirm_update_all"),
                    InlineKeyboardButton("❌ No", callback_data="cancel_update_all"),
                ]
            ]
        )
        await message.reply(
            "Are you sure you want to update verification status for **all users**?",
            reply_markup=keyboard
        )

# Callback query handler for the buttons
@Client.on_callback_query(filters.regex("confirm_update_all|cancel_update_all"))
async def handle_confirmation(client, query: CallbackQuery):
    if query.data == "confirm_update_all":
        count = 0
        async for user in db.get_all_users():
            await db.update_verification(user['id'], **DEFAULT_VERIFICATION)
            count += 1
        await query.edit_message_text(f"Verification status updated for **{count} users**.")
    elif query.data == "cancel_update_all":
        await query.edit_message_text("Operation cancelled.")