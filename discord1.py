from pprint import pprint
from time import sleep
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, \
    CallbackQueryHandler
import telegram.ext.filters as filters
from pymongo import MongoClient
import requests
from ddd import discord_client, Discord_Token
import asyncio


SEARCH_QUERY, SEARCH_RESULTS, DISPLAY_PRODUCT, SELECT_OPTION, ORDER_PRODUCT, ORDER_OPTION, GET_COUNTRY, GET_STATE, GET_LOCATION, GET_QUANTITY, ORDER_COMPLETE, CONV_OPTION = range(
    12)

client = MongoClient(
    "")
db = client["Tech_store"]
collection = db["orders"]

Token = ""


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome to Laylas Tech Store chatbot and assistant! Use /help to see available "
                                    "commands.")


# Define the /help command handler
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/search - Search for products\n"
        "/get_products - List all available products\n"
        # "/get_product_by_category <category> - Get products by category\n"
        "/get_product_category - Get all products categories\n"
        "/get_help to talk to an assistant directly\n "
        "/update to update a specific order\n"
    )


# Define the /search command handler
async def search(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("You are now in search mode. Please enter your search query:")
    return SEARCH_QUERY


async def get_products(update: Update, context: CallbackContext) -> None:
    # Send a message informing the user that their request is being processed
    await update.message.reply_text("Retrieving products...")

    response = requests.get("https://dummyjson.com/products?skip=0&limit=0")

    if response.status_code == 200:
        products = response.json()
        # Extract relevant information from the response
        product_names = [product['title'] for product in products.get('products', [])]
        # Construct the message text to send back to the user
        message_text = "\n".join(product_names)
    else:
        message_text = "Failed to retrieve products."

    # Send the compiled message text back to the user
    await update.message.reply_text(message_text)


# async def get_product_by_category(update: Update, context: CallbackContext) -> None:
#     # Send a message prompting the user to input the name of the items they wish to search for
#     await update.message.reply_text("Please input the category of name of the item you wish to search for.")
#     # Update the user's state to indicate that they are in the search state
#     context.user_data['state'] = 'search'
#     # Check if the user has provided a search query after the command
#     if context.args:
#         search_query = ' '.join(context.args)
#         # Make an API request to the search endpoint
#
#         response = requests.get(f"https://dummyjson.com/products/category/{search_query}?limit=0")
#         if response.status_code == 200:
#             search_results = response.json()
#             print(search_query)
#             pprint(search_results)
#             # Assuming the API returns a list of items, and you want to send back titles
#             messages = [product['title'] for product in search_results.get('products', [])]
#             message_text = '\n'.join(messages) if messages else "Category not found."
#         else:
#             message_text = "Failed to retrieve search results."
#     else:
#         message_text = "Please provide a search query after the command. E.g., /get_product_by_category book"
#
#     # Send the compiled message text back to the user
#     await update.message.reply_text(message_text)


async def get_product_category(update: Update, context: CallbackContext) -> None:
    # Send a message informing the user that their request is being processed
    await update.message.reply_text("Retrieving categories...")

    # Make an API request to fetch the products
    response = requests.get("https://dummyjson.com/products/categories?skip=0&limit=0")

    if response.status_code == 200:
        products = response.json()
        # Extract relevant information from the response
        product_names = [product for product in products]
        # Construct the message text to send back to the user
        message_text = "\n".join(product_names)
        await update.message.reply_text(message_text)
        await update.message.reply_text("Do you want to search using the product category??")
        await update.message.reply_text("Please select an option:\n 1. Enter search state \n 2. Cancel")
        return CONV_OPTION

    else:
        message_text = "Failed to retrieve categories."
        await update.message.reply_text(message_text)


async def conv_option(update: Update, context: CallbackContext):
    option = update.message.text
    if option == "1":
        await update.message.reply_text("You are now in search mode. Please enter your search query:")
        return SEARCH_QUERY
    elif option == "2":
        # Transition back to the previous state to allow the user to search for products again
        await update.message.reply_text("Action cancelled")
    else:
        # Inform user if an invalid option is selected
        await update.message.reply_text("Invalid option. Please select a valid option.")
        await update.message.reply_text("Please select an option:\n 1. Enter search state \n 2. Cancel")
        return CONV_OPTION


async def search_query(update: Update, context: CallbackContext):
    search_query = update.message.text
    # Store the search query for potential future use or modification
    context.user_data['search_query'] = search_query

    # Example API call (assuming async operation, replace with your actual async call if available)
    response = requests.get(
        f"https://dummyjson.com/products/search?q={search_query}&limit=0", timeout=30)  # Adjust according to your API

    if response.status_code == 200:
        search_results = response.json()
        products = search_results.get('products', [])
        if products:
            context.user_data['search_results'] = products
            for product in products:
                message_text = f"ID: {product['id']}\n\n TITLE: {product['title']}\n\nDESCRIPTION: {product['description']}\n"
                images = product.get('thumbnail', [])
                if images:
                    await update.message.reply_text(message_text)
                    await context.bot.send_photo(update.effective_chat.id, photo=images)
                else:
                    # Send only the product details if no image is available
                    await update.message.reply_text(message_text)
            await update.message.reply_text(
                "Please select a given product ID to select a product to see a more detailed description or place an order:")
            return DISPLAY_PRODUCT
        else:
            await update.message.reply_text("No products found. Try another search.")
            return SEARCH_QUERY
    else:
        await update.message.reply_text("Failed to retrieve search results. Please try again.")
        return SEARCH_QUERY


async def display_product(update: Update, context: CallbackContext):
    # await update.message.reply_text("Please select a given product ID to select a product to order:")
    product_id = update.message.text
    search_results = context.user_data.get('search_results')
    # Find the product with the given ID
    selected_product = None
    for product in search_results:
        if str(product['id']) == product_id:
            selected_product = product
            context.user_data['selected_product'] = selected_product
            break

    if selected_product:
        # Display the details of the selected product
        message_text = f"ID: {selected_product['id']}\n\n TITLE: {selected_product['title']}\n\nDESCRIPTION: {selected_product['description']}\n\n PRICE:{selected_product['price']}\n\nDISCOUNTED PERCENTAGE: {selected_product['discountPercentage']}\n\nSTOCK: {selected_product['stock']}\n\nBRAND: {selected_product['brand']}\n\nCATEGORY: {selected_product['category']}"
        images = selected_product.get('images', [])
        if images:
            await update.message.reply_text(message_text)
            for image_url in images:
                await context.bot.send_photo(update.effective_chat.id, photo=image_url)
        else:
            # Send only the product details if no image is available
            await update.message.reply_text(message_text)
        await update.message.reply_text("Please select an option:\n 1. Order selected product\n 2. Go back")
        return SELECT_OPTION
    else:
        # Inform user if product with given ID is not found
        await update.message.reply_text("Product ID not found. Please enter a valid product ID.")
    return ConversationHandler.END


async def select_option(update: Update, context: CallbackContext):
    option = update.message.text
    if option == "1":
        # Transition to a new state to handle ordering the selected product
        await update.message.reply_text("Please you will be required to fill in some details......")
        sleep(1)
        await update.message.reply_text("Please provide your name.")
        return ORDER_PRODUCT
    elif option == "2":
        # Transition back to the previous state to allow the user to search for products again
        await update.message.reply_text("You are now in search mode. Please enter your search query:")
        return SEARCH_QUERY
    else:
        # Inform user if an invalid option is selected
        await update.message.reply_text("Invalid option. Please select a valid option.")
        # Stay in the same state
        await update.message.reply_text("Please select an option:\n 1. Order selected product\n 2. Go back")
        return SELECT_OPTION


async def order_product(update: Update, context: CallbackContext):
    name = update.message.text
    context.user_data['name'] = name

    await update.message.reply_text("Please provide your country.")
    return GET_COUNTRY


async def get_country(update: Update, context: CallbackContext):
    # Get the user's country from the message
    country = update.message.text
    context.user_data['country'] = country

    # Prompt the user for their state
    await update.message.reply_text("Please provide your state.")
    return GET_STATE


async def get_state(update: Update, context: CallbackContext):
    # Get the user's state from the message
    state = update.message.text
    context.user_data['state'] = state

    # Prompt the user for their location
    await update.message.reply_text("Please provide your location.")
    return GET_LOCATION


async def get_location(update: Update, context: CallbackContext):
    # Get the user's location from the message
    location = update.message.text
    context.user_data['location'] = location

    # Prompt the user for the quantity
    await update.message.reply_text("Please provide the quantity.")
    return GET_QUANTITY


async def get_quantity(update: Update, context: CallbackContext):
    # Get the quantity from the message
    quantity = update.message.text
    context.user_data['quantity'] = quantity

    name = context.user_data.get('name')
    country = context.user_data.get('country')
    state = context.user_data.get('state')
    location = context.user_data.get('location')

    order_details = f"Your details are: NAME:{name}\nCOUNTRY: {country}\n STATE: {state}\nLOCATION: {location}\nQUANTITY: {quantity}"
    await update.message.reply_text(order_details)
    await update.message.reply_text("Please select an option:\n 1. Continue to place an order \n 2. Change order "
                                    "details\n 3.Cancel")
    return ORDER_OPTION


async def order_option(update: Update, context: CallbackContext):
    option = update.message.text
    if option == "1":
        # Transition to a new state to handle ordering the selected product
        await update.message.reply_text("Your order is being processed..")
        await order_complete(update, context)
    elif option == "2":
        await update.message.reply_text("Please provide your name.")
        return ORDER_PRODUCT
    elif option == "3":
        # Transition back to the previous state to allow the user to search for products again
        await update.message.reply_text("Order has been cancelled ")
        await update.message.reply_text("You are now in search mode. Please enter your search query:")
        return SEARCH_QUERY
    else:
        # Inform user if an invalid option is selected
        await update.message.reply_text("Invalid option. Please select a valid option.")
        # Stay in the same state
        await update.message.reply_text("Please select an option:\n 1. Continue to place an order \n 2. Change order "
                                        "details\n 3.Cancel")
        return ORDER_OPTION


def save_order_details(order_details):
    try:
        collection.insert_one(order_details)
        print("Order details saved successfully.")
    except Exception as e:
        print(f"Error occurred while saving order details: {e}")


async def order_complete(update: Update, context: CallbackContext):
    selected_product = context.user_data.get('selected_product')
    product_id = selected_product.get('id')
    title = selected_product.get('title')
    price = selected_product.get('price')
    discount_percentage = selected_product.get('discountPercentage')
    name = context.user_data.get('name')
    country = context.user_data.get('country')
    state = context.user_data.get('state')
    location = context.user_data.get('location')
    quantity = context.user_data.get('quantity')
    user_username = update.effective_user.username

    order_details = {
        "name": name,
        "country": country,
        "state": state,
        "location": location,
        "quantity": quantity,
        "telegram_username": user_username,
        "product_id": product_id,
        "title": title,
        "price": price,
        "discount_percentage": discount_percentage,
        "sent": False
    }

    try:
        save_order_details(order_details)
        await update.message.reply_text("Order details saved successfully.")
    except Exception as e:
        await update.message.reply_text(f"Error occurred while saving order details: {e}")
        print(f"Error occurred while saving order details: {e}")


async def search_results(update: Update, context: CallbackContext):
    # This would handle the user's selection from the search results, assuming you use InlineKeyboardMarkup for results
    query = update.callback_query
    await query.answer()

    selected_product_id = query.data  # Assuming you pass product ID as callback data
    # Fetch and display product details, etc.


# Define other command handlers similarly

# Set up the updater and add the command handlers
def main() -> None:
    app = Application.builder().token(Token).build()

    search_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('search', search),
                      CommandHandler("get_product_category", get_product_category)],
        states={
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)],
            DISPLAY_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, display_product)],
            SEARCH_RESULTS: [CallbackQueryHandler(search_results)],
            SELECT_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_option)],
            ORDER_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_product)],
            GET_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            GET_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_state)],
            GET_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            GET_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            ORDER_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_option)],
            ORDER_COMPLETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_complete)],
            CONV_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_option)]
        },
        fallbacks=[],

    )

    # category_conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler("get_product_category", get_product_category)],
    #     states={
    #         CONV_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_option)]
    #     },
    #     fallbacks=[],
    #
    # )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    # app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("get_products", get_products))
    # app.add_handler(CommandHandler("get_product_by_category", get_product_by_category))
    # app.add_handler(CommandHandler("get_product_category", get_product_category))
    app.add_handler(search_conv_handler)
    # app.add_handler(category_conv_handler)

    # Add other command handlers similarly

    app.run_polling()
    discord_client.run(Discord_Token)


if __name__ == "__main__":
    main()
    # discord_client.run(Discord_Token)

