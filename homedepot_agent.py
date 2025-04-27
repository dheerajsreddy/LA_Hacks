from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage, TextContent, ChatAcknowledgement,
    chat_protocol_spec
)
from datetime import datetime
from uuid import uuid4
import json

class ProductSearchRequest(Model):
    user_query: str
    serpapi_key: str

class ProductSearchResponse(Model):
    products: list

class DownloadImagesRequest(Model):
    products: list
    images_dir: str

class DownloadImagesResponse(Model):
    downloaded_images: list

# Initialize the agent with a seed for deterministic address generation
homedepot_agent = Agent(
    name="homedepot_agent",
    port=8002,
    seed="homedepot recovery phrase"  # This will generate the same address each time
)

chat_proto = Protocol(spec=chat_protocol_spec)

@homedepot_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Home Depot agent started with address: {ctx.agent.address}")

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if isinstance(item, TextContent):
            ctx.logger.info(f"Received message from {sender}: {item.text}")
            
            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)
            
            # Process the message based on its content
            try:
                # Parse the message text as JSON
                data = json.loads(item.text.replace("'", '"'))
                
                if "user_query" in data and "serpapi_key" in data:
                    from homedepot_backend import get_search_query_from_gemini, search_home_depot_serpapi
                    search_query = get_search_query_from_gemini(data["user_query"])
                    products = search_home_depot_serpapi(data["serpapi_key"], search_query)
                    response = ProductSearchResponse(products=products)
                    await ctx.send(sender, response)
                
                elif "products" in data and "images_dir" in data:
                    from homedepot_backend import download_product_images
                    downloaded_images = download_product_images(data["products"], data["images_dir"])
                    response = DownloadImagesResponse(downloaded_images=[str(p) for p in downloaded_images])
                    await ctx.send(sender, response)
            except Exception as e:
                ctx.logger.error(f"Error processing message: {e}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent
homedepot_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    homedepot_agent.run() 