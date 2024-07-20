import discord
from pymongo import MongoClient
import asyncio

client = MongoClient(
    "")
db = client["Tech_store"]
collection = db["orders"]


Discord_Token = ""
CHANNEL_ID = int(122)

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


async def check_unsent_entries():
    try:
        # Check MongoDB for new unsent entries
        unsent_entries = collection.find({"sent": False})

        # Send unsent entries to Discord channel
        for entry in unsent_entries:
            message = f"New order received:\n" \
                      f"Name: {entry['name']}\n" \
                      f"Country: {entry['country']}\n" \
                      f"State: {entry['state']}\n" \
                      f"Location: {entry['location']}\n" \
                      f"Quantity: {entry['quantity']}\n" \
                      f"Product ID: {entry['product_id']}\n" \
                      f"Title: {entry['title']}\n" \
                      f"Price: {entry['price']}\n" \
                      f"Discount Percentage: {entry['discount_percentage']}\n" \
                      f"Telegram Username: {entry['telegram_username']}\n"

            # Send message to Discord channel (replace CHANNEL_ID with your channel ID)
            channel = discord_client.get_channel(CHANNEL_ID)
            await channel.send(message)

            # Update "sent" field to True
            collection.update_one({"_id": entry["_id"]}, {"$set": {"sent": True}})
            print("Order details sent to Discord user.")

        # Sleep for 10 seconds before checking again
        await asyncio.sleep(5)

    except Exception as e:
        print(f"error: {e}")


@discord_client.event
async def on_ready():
    print("Discord bot is ready.")
    # Start the task to check for unsent entries
    discord_client.loop.create_task(check_unsent_entries())

