import asyncio
from backend.src.service.chat.agent import AgentService
from backend.src.schemas.message import RoomMessage, MessageType, Sender
from sqlalchemy.orm import Session

async def chat_with_agent():
    # Initialize agent service (None for db since we're just testing)
    agent = AgentService(db=None)
    
    print("Agent initialized! You can start chatting (type 'quit' to exit)")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            break
            
        # Create user message
        user_message = RoomMessage(
            type=MessageType.text,
            content=user_input,
            sender=Sender.user
        )
        
        # Get agent's response
        response = await agent.get_agent_response(user_message)
        
        # Print agent response
        print(f"\n{agent.state['persona'].name}: {response.content}")
        
        # Print emotion and affinity if available
        if response.emotion:
            print(f"Emotion: {response.emotion.emotion} (Affinity: {response.emotion.likeability:.2f})")
        
        # Print scenario info if available
        if response.scenario_info:
            print(f"\nCurrent Scenario: {response.scenario_info.title}")
            print(f"Progress: {response.scenario_info.current_progress:.0%}")
        
        # Print tips if available
        if response.tips:
            print(f"\nRelationship Tips:\n{response.tips}")

if __name__ == "__main__":
    asyncio.run(chat_with_agent()) 