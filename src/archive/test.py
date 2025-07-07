from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.mcp import MCPServerSSE
from agents import analysis_model

with open("prompts/creative_coupon.txt", "r", encoding="utf-8") as file:
    prompt = file.read()

server = MCPServerSSE(url='http://localhost:3001/sse')
agent = Agent(
    model=analysis_model,
    mcp_servers=[server],
    system_prompt=prompt)

async def main():
    async with agent.run_mcp_servers():
        with open("order_kpis_summary.json", "r") as file:
            summary_json = file.read()
        results = await agent.run(user_prompt=summary_json)
        print(results.output)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

# Initialize message history
# message_history: list[ModelMessage] = []

# async def main(user_prompt: str):
#     global message_history  # Declare that we want to modify the global variable
    
#     async with agent.run_mcp_servers():  
#         result = await agent.run(
#             user_prompt=user_prompt,
#             message_history=message_history
#         )
#         # Update the global message history
#         message_history = result.all_messages()
    
#     print("Bot:", result.output)
#     return result

# if __name__ == '__main__':
#     import asyncio
    
#     while True:
#         user_prompt = input("You: ")
#         if user_prompt.lower() in ['quit', 'exit', 'bye']:
#             break
#         try:
#             asyncio.run(main(user_prompt=user_prompt))
#         except KeyboardInterrupt:
#             print("\nGoodbye!")
#             break
#         except Exception as e:
#             print(f"Error: {e}")
#             continue