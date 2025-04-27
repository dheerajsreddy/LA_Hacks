from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage, TextContent, ChatAcknowledgement,
    chat_protocol_spec
)
from datetime import datetime
from uuid import uuid4
import json

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
imagegen_agent = Agent(
    name="imagegen_agent",
    port=8004,
    seed="imagegen recovery phrase"  # This will generate the same address each time
)

chat_proto = Protocol(spec=chat_protocol_spec)

@imagegen_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"ImageGen agent started with address: {ctx.agent.address}")

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
                
                if all(key in data for key in ["room_image_path", "product_image_path", "user_query", "output_path"]):
                    from image_generation_backend import generate_room_image, generate_image_prompt
                    from pathlib import Path
                    image_prompt = generate_image_prompt(data["user_query"])
                    success = generate_room_image(
                        Path(data["room_image_path"]),
                        Path(data["product_image_path"]),
                        data["user_query"],
                        Path(data["output_path"])
                    )
                    response = ImageGenResponse(success=success, output_path=data["output_path"], image_prompt=image_prompt)
                    await ctx.send(sender, response)
            except Exception as e:
                ctx.logger.error(f"Error processing message: {e}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent
imagegen_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    imagegen_agent.run() 