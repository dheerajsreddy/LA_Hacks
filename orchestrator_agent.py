from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage, TextContent, ChatAcknowledgement,
    chat_protocol_spec
)
from datetime import datetime
from uuid import uuid4

class OrchestratorRequest(Model):
    user_query: str
    room_image_path: str
    serpapi_key: str
    output_path: str

class OrchestratorResponse(Model):
    products: list
    contractors: list
    imagegen: dict

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

class ContractorSearchRequest(Model):
    user_query: str
    location: str

class ContractorSearchResponse(Model):
    contractors: list

class ImageGenRequest(Model):
    room_image_path: str
    product_image_path: str
    user_query: str
    output_path: str

class ImageGenResponse(Model):
    success: bool
    output_path: str
    image_prompt: str

# Initialize the agent with a seed for deterministic address generation
orchestrator = Agent(
    name="orchestrator",
    port=8003,
    seed="orchestrator recovery phrase"  # This will generate the same address each time
)

chat_proto = Protocol(spec=chat_protocol_spec)

@orchestrator.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Orchestrator agent started with address: {ctx.agent.address}")

@orchestrator.on_message(OrchestratorRequest)
async def orchestrate(ctx: Context, sender: str, msg: OrchestratorRequest):
    # Get the addresses of other agents from their startup logs
    homedepot_address = "agent1q0d5djrn4g3vpnz9zxyuha6m0fs2awncduc7a527pgvnxkvparuhce4zh5a"  # Replace with actual address
    contractor_address = "agent1qgd329n6xh8l4mrnt62jj5zqxadplk5l9fa7xr5fdy0zqazll9ncx7dtqwv"  # Replace with actual address
    imagegen_address = "agent1qf6hkzqz0z0s5ck0lppy0w2g3r7jwgllq3w5msyw8j8qwzawp63mjsjpjp3"    # Replace with actual address

    # 1. Product search
    message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=str({"user_query": msg.user_query, "serpapi_key": msg.serpapi_key}))]
    )
    await ctx.send(homedepot_address, message)
    prod_resp = await ctx.recv()
    products = prod_resp.products

    # 2. Download images
    message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=str({"products": products, "images_dir": "images"}))]
    )
    await ctx.send(homedepot_address, message)
    img_resp = await ctx.recv()
    downloaded_images = img_resp.downloaded_images

    # 3. Contractor search
    message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=str({"user_query": msg.user_query, "location": "Los Angeles, CA"}))]
    )
    await ctx.send(contractor_address, message)
    cont_resp = await ctx.recv()
    contractors = cont_resp.contractors

    # 4. Image generation
    product_image_path = downloaded_images[0]
    message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=str({
            "room_image_path": msg.room_image_path,
            "product_image_path": product_image_path,
            "user_query": msg.user_query,
            "output_path": msg.output_path
        }))]
    )
    await ctx.send(imagegen_address, message)
    imggen_resp = await ctx.recv()

    # 5. Aggregate and respond
    response = OrchestratorResponse(
        products=products,
        contractors=contractors,
        imagegen={
            'success': imggen_resp.success,
            'output_path': imggen_resp.output_path,
            'image_prompt': imggen_resp.image_prompt
        }
    )
    await ctx.send(sender, response)

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

@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent
orchestrator.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    orchestrator.run() 