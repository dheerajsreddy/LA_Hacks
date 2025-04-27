from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage, TextContent, ChatAcknowledgement,
    chat_protocol_spec
)
from datetime import datetime
from uuid import uuid4
import json

class ContractorSearchRequest(Model):
    user_query: str
    location: str

class ContractorSearchResponse(Model):
    contractors: list

# Initialize the agent with a seed for deterministic address generation
contractor_agent = Agent(
    name="contractor_agent",
    port=8001,
    seed="contractor recovery phrase"  # This will generate the same address each time
)

chat_proto = Protocol(spec=chat_protocol_spec)

@contractor_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Contractor agent started with address: {ctx.agent.address}")

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
                
                if "user_query" in data and "location" in data:
                    from contractor_backend import get_search_term_from_gemini, find_contractors_google_places
                    search_term = get_search_term_from_gemini(data["user_query"])
                    contractors = find_contractors_google_places(
                        search_term=search_term,
                        latitude=34.0522,  # Example: LA
                        longitude=-118.2437,
                        radius=15 * 1609
                    )
                    response = ContractorSearchResponse(contractors=contractors)
                    await ctx.send(sender, response)
            except Exception as e:
                ctx.logger.error(f"Error processing message: {e}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent
contractor_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    contractor_agent.run() 