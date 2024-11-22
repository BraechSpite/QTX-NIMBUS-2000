from telethon import TelegramClient, events
import re
from aiohttp import web
import os

# Telegram API credentials
api_id = 23844616
api_hash = "4aeca3680a20f9b8bc669f9897d5402f"

# Input and Output channel IDs
input_channel_id = -1002168438523
output_channel_id = -1002449919371

# Initialize the Telegram client
client = TelegramClient("trading_signal_bot", api_id, api_hash)

# Global variable to store the last signal details
last_signal = {"pair": None, "time": None, "direction": None}

# Function to reformat result messages
def reformat_result(result_text):
    result_pattern = r"Result for ([\w/]+)_otc: (WIN ✅¹?|💔 Loss)"
    result_match = re.search(result_pattern, result_text)

    if result_match:
        pair = result_match.group(1).replace("_", "-").upper() + "-OTC"
        result = result_match.group(2)

        # Use the last stored signal details for time and direction
        time = last_signal.get("time", "N/A")
        direction = last_signal.get("direction", "N/A")

        # Format the result as required
        formatted_result = f"**🏁 {pair} | {time} | {direction} : {result}**"
        return formatted_result
    return None

# Function to reformat signal messages
def reformat_signal(signal_text):
    pair_pattern = r"PAIR\s*-\s*([\w/]+)_otc"
    time_pattern = r"TIME\s*-\s*([\d:]+)"
    direction_pattern = r"DIRECTION\s*-\s*(UP|DOWN)\s*(🟩|🟥)"
    martingale_pattern = r"(✅¹\s*1 Step-Martingale)"
    owner_pattern = r"OWNER\s*-\s*(@\w+)"

    pair_match = re.search(pair_pattern, signal_text)
    time_match = re.search(time_pattern, signal_text)
    direction_match = re.search(direction_pattern, signal_text)
    martingale_match = re.search(martingale_pattern, signal_text)
    owner_match = re.search(owner_pattern, signal_text)

    formatted_signal = []
    if pair_match:
        pair = pair_match.group(1).replace("_", "-").upper() + "-OTC"
        formatted_signal.append(f"**📊 PAIR - {pair}**")
        last_signal["pair"] = pair  # Update last signal pair
    if time_match:
        time = time_match.group(1)[:-3]
        formatted_signal.append(f"**⏰ TIME - {time}**")
        last_signal["time"] = time  # Update last signal time
    if direction_match:
        direction = f"{direction_match.group(1)} {direction_match.group(2)}"
        formatted_signal.append(f"**↕️ DIRECTION - {direction}**")
        last_signal["direction"] = direction  # Update last signal direction
    if martingale_match:
        formatted_signal.append(f"**{martingale_match.group(1)}**")
    if owner_match:
        formatted_signal.append(f"**🧔🏻 OWNER - @Advik_Ahooja**")

    return "\n".join(formatted_signal)

# Event handler for new messages
@client.on(events.NewMessage(chats=input_channel_id))
async def handle_new_message(event):
    original_message = event.message.message

    # Determine if the message is a result or signal
    if "Result for" in original_message:
        formatted_result = reformat_result(original_message)
        if formatted_result:
            # Send the result message
            await client.send_message(output_channel_id, formatted_result)
            # Send the separator
            await client.send_message(output_channel_id, "➖➖➖➖➖➖➖➖➖➖")
    else:
        formatted_signal = reformat_signal(original_message)
        if formatted_signal:
            await client.send_message(output_channel_id, formatted_signal)

# Define a basic HTTP handler for health checks
async def handle_healthcheck(request):
    return web.Response(text="Service is up and running!")

# Create an aiohttp application
app = web.Application()
app.add_routes([web.get('/', handle_healthcheck)])

# Start the Telegram client
print("Bot is running...")
client.start()

# Get the port from environment variables (Render provides this)
port = int(os.getenv("PORT", 8080))

# Run the Telegram client and HTTP server together
try:
    web.run_app(app, port=port)
finally:
    client.run_until_disconnected()
