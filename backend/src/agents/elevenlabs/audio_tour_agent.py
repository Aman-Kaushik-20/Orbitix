import random
import os
import httpx
import asyncio
from dotenv import load_dotenv
from agno.agent import Agent, RunResponseEvent
from agno.models.google import Gemini
from agno.tools import tool
from src.agents.elevenlabs.elevenlabs_toolkit import ElevenLabsTools
from agno.models.message import Image, Video, Audio, File
from typing import Dict, List, AsyncGenerator, Literal
from pydantic import BaseModel
from openai import OpenAI

class Media(BaseModel):
    type:Literal['image', 'audio', 'file', 'video']
    url : str

class AudioTourAgentParams(BaseModel):
    text_message:str
    attachments: List[Media]


# --- Environment and API Key Setup ---
load_dotenv('backend/.env')
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class AudioTourAgent:
    def __init__(self, gemini_api_key):
        """
        Initializes the AudioTourAgent.
        """
        self.gemini_api_key=gemini_api_key
        self.perplexity_api_key = PERPLEXITY_API_KEY
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.agent = self.setup_agent()

    def setup_agent(self) -> Agent:
        """
        Sets up and configures the agent with its tools and instructions.

        Returns:
            Agent: A fully configured instance of the agno.agent.Agent.
        """
        # --- Voice Selection ---
        voices = [
            {"id": "EiNlNiXeDU1pqqOPrYMO", "name": "John Doe - Deep"},
            {"id": "EkK5I93UQWFDigLMpZcX", "name": "James - Husky & Engaging"},
            {"id": "NOpBlnGInO9m6vDvFkFC", "name": "Grandpa Spuds Oxley"},
        ]
        selected_voice = random.choice(voices)

        # Create perplexity search tool
        @tool(
            name="perplexity_search",
            description="Research historical places, cultural topics, monuments, and people using Perplexity AI",
            show_result=True
        )
        async def perplexity_search(query: str) -> str:
            """
            Search for information about historical places, monuments, cultural topics, or people.
            
            Args:
                query: The search query about a place, monument, culture, or person
            
            Returns:
                Detailed information about the topic
            """
            if not self.perplexity_api_key:
                return "Perplexity API key not configured"
            
            try:
                headers = {
                    "Authorization": f"Bearer {self.perplexity_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "sonar-reasoning",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a knowledgeable tour guide assistant. Provide detailed, engaging information about historical places, monuments, cultural topics, and historical figures. Focus on interesting facts, history, cultural significance, and stories that would make for compelling audio content."
                        },
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.1,
                    "return_citations": True
                }
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(PERPLEXITY_API_URL, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return content
                    else:
                        return f"Error: Unable to research the topic. Status: {response.status_code}"
            except Exception as e:
                return f"Error researching topic: {str(e)}"

        # --- Agent Definition ---
        agent = Agent(
            name='Audio Tour Agent',
            model=Gemini(id="gemini-2.5-pro", api_key=self.gemini_api_key),
            tools=[
                ElevenLabsTools(
                    voice_id=selected_voice["id"],
                    model_id="eleven_multilingual_v2",
                    target_directory="audio_generations",
                ),
                perplexity_search,
            ],
            description="You are an Audio Tour Guide AI. You create engaging audio stories based on images, videos, audio clips, and documents provided by the user.",
            instructions=[
                "You are an AI travel guide. Your main goal is to produce cinematic and engaging audio stories about historical places, cultural topics, and more.",
                "**Workflow:**",
                "1. **Analyze Attachments:** Carefully examine all attached files (images, videos, audio, documents). Understand what they are about.",
                "2. **Research:** When a user asks for audio, you MUST first use the `perplexity_search` tool to research the topic. Gather details about its history, cool facts, construction, cultural significance, local folktales, and archaeological findings. When Asked about any Person...find about its biography, related history, facts and figures acc. to that person and context only",
                "3. **Scripting:** From your research, write a well-structured, cinematic script. It should be captivating and educational, not a dry, bookish report. Make it interesting enough to keep listeners engaged.",
                "4. **Audio Generation:** Use the `text_to_speech` tool to convert your script into speech.",
                "5. **Response:** Return the URL of the generated audio file embedded in an HTML audio player. For example: `<audio controls src=\"URL_HERE\" title=\"Generated Audio\"></audio>`  to be propley rendered in markdown and the Text along with that audio supporting the contents of audio",
            ],
            markdown=True,
            stream=True
        )
        return agent
    

    async def run_async(self, text_message: str, attachments: List[Dict[str, str]] = None) -> AsyncGenerator[Dict, None]:
        """
        Runs the agent asynchronously with attachments.

        Args:
            text_message (str): The user's text prompt.
            attachments (List[Dict[str, str]], optional): A list of attachments with URLs.

        Yields:
            Dict: An event from the agent's run.
        """
        # images, videos, audios, files = [], [], [], []

        # if attachments:
        #     for attachment in attachments:
        #         attachment_type = attachment.get('type')
        #         url = attachment.get('url')
        #         if not attachment_type or not url:
        #             continue
                
        #         # The agno library expects a `url` parameter for remote URLs.
        #         if attachment_type == 'image':
        #             images.append(Image(url=url))
        #         elif attachment_type == 'video':
        #             videos.append(Video(url=url))
        #         elif attachment_type == 'audio':
        #             audios.append(Audio(url=url))
        #         elif attachment_type == 'file':
        #             files.append(File(url=url))

        # # Stream with detailed intermediate steps
        # response_stream = await self.agent.arun(
        #     message=text_message,
        #     images=images or None,
        #     videos=videos or None,
        #     audio=audios or None,
        #     files=files or None,
        #     stream=True,
        #     stream_intermediate_steps=True
        # )

        # # Collect all response content and reasoning steps
        # all_content = []
        # reasoning_steps = []
        
        # # Handle different event types and collect them
        # async for event in response_stream:
        #     if event.event == "RunResponseContent":
        #         if event.content:
        #             print(f"Content: {event.content}")
        #             all_content.append(event.content)
        #     elif event.event == "ToolCallStarted":
        #         tool_name = event.tool.tool_name if hasattr(event.tool, 'tool_name') else 'Unknown Tool'
        #         print(f"Tool call started: {tool_name}")
        #         reasoning_steps.append(f"🔧 Tool call started: {tool_name}")
        #     elif event.event == "ReasoningStep":
        #         if event.reasoning_content:
        #             print(f"Reasoning: {event.reasoning_content}")
        #             reasoning_steps.append(event.reasoning_content)
        
        # # Send reasoning steps first
        # if reasoning_steps:
        #     for step in reasoning_steps:
        #         yield {'type': 'reasoning', 'data': step}
        
        with open(r'/home/username/Orbitix/wrong_rome.md', 'r') as file:
            all_content = file.read()
            combined_content=all_content


        # Combine all content and format it properly
        if all_content:
        #     combined_content = ''.join(all_content)
            formatted_content = await self._format_response_with_openai(combined_content)
            yield {'type': 'response', 'data': formatted_content}
        else:
            yield {'type': 'response', 'data': 'No content generated'}
    
    

    def clean_openai_text(self, api_text: str) -> str:
        # Ensure proper line endings, avoid re-decoding UTF-8 unnecessarily
        return api_text.replace("\r\n", "\n")

    async def _format_response_with_openai(self, raw_content: str) -> str:
        """
        Format the raw agent response using OpenAI to ensure proper markdown formatting
        and preserve line breaks, headings, and audio tags for rendering.
        """
        if not self.openai_client:
            return raw_content

        try:
            system_prompt = """
            You are a markdown formatting expert. Your task is to take the raw audio tour guide
            response and transform it into a single, clean, and beautifully formatted markdown document to be shown to users in UI.

            Rules:
            1. Format the main script with proper markdown: headings (#, ##), bold text (**text**), lists, etc.
            2. Keep the <audio> HTML tag exactly as it appears — do not escape it.
            3. Merge any summary text into the main script only if it adds unique value; otherwise discard it.
            4. Remove debugging artifacts or repeated phrases.
            5. Render special characters (—, “”, etc.) as proper UTF-8, not escaped codes.
            6. Use actual newlines, not literal '\\n'.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-5-2025-08-07",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please format this audio tour content properly:\n\n{raw_content}"}
                ],
            )

            openai_text = response.choices[0].message.content
            clean_content = self.clean_openai_text(openai_text)

            # Replace escaped newlines with real ones
            formatted_content = clean_content.replace("\\n", "\n")

            # Normalize multiple blank lines
            while "\n\n\n" in formatted_content:
                formatted_content = formatted_content.replace("\n\n\n", "\n\n")

            # Strip leading/trailing whitespace
            formatted_content = formatted_content.strip()

            # Save after formatting
            with open("rome_try3.md", "w", encoding="utf-8") as f:
                f.write(formatted_content)

            return formatted_content

        except Exception as e:
            print(f"Error formatting response with OpenAI: {e}")
            return raw_content.replace("\r\n", "\n").strip()




# if __name__ == "__main__":
#     try:
#         async def main():
#             """Asynchronous function to set up and run the agent."""
#             agent_instance = AudioTourAgent()
            
#             prompt = "Generate an audio tour for the landmark in the image."
#             attachments = [
#                 {
#                     'type': 'image',
#                     'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg/800px-Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg'
#                 },
#                 {
#                     'type': 'file',
#                     'url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
#                 }
#             ]

#             print(f"--- User Prompt ---\n{prompt}\n")
#             print(f"--- Attachments ---\n{attachments}\n")
#             print("--- Agent Running ---")

#             try:
#                 async for response_part in agent_instance.run_async(prompt, attachments=attachments):
#                     print(f"\n--- Agent Event ---\n{response_part}")
#             except Exception as e:
#                 print(f"\nAn error occurred during agent execution: {e}")
#             finally:
#                 print("\n--- Agent Run Finished ---")

#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("\nAgent run interrupted by user.")