import random
import os
import asyncio
from dotenv import load_dotenv
from agno.agent import Agent, RunResponseEvent
from agno.models.google import Gemini
from src.agents.elevenlabs.elevenlabs_toolkit import ElevenLabsTools
from agno.models.message import Image, Video, Audio, File
from typing import Dict, List, AsyncGenerator


# --- Environment and API Key Setup ---
load_dotenv('backend/.env')


class AudioTourAgent:
    def __init__(self, gemini_api_key):
        """
        Initializes the AudioTourAgent.
        """
        self.gemini_api_key=gemini_api_key
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

        # --- Agent Definition ---
        agent = Agent(
            name='Audio Tour Agent',
            model=Gemini(id="gemini-1.5-pro", api_key=self.gemini_api_key),
            tools=[
                ElevenLabsTools(
                    voice_id=selected_voice["id"],
                    model_id="eleven_multilingual_v2",
                    target_directory="audio_generations",
                ),
            ],
            description="You are an Audio Tour Guide AI. You create engaging audio stories based on images, videos, audio clips, and documents provided by the user.",
            instructions=[
                "You are an AI travel guide. Your main goal is to produce cinematic and engaging audio stories about historical places, cultural topics, and more.",
                "**Workflow:**",
                "1. **Analyze Attachments:** Carefully examine all attached files (images, videos, audio, documents). Understand what they are about.",
                "2. **Research:** When a user asks for audio, you MUST first use the `perplexity_search` tool to research the topic. Gather details about its history, cool facts, construction, cultural significance, local folktales, and archaeological findings. When Asked about any Person...find about its biography, related history, facts and figures acc. to that person and context only",
                "3. **Scripting:** From your research, write a well-structured, cinematic script. It should be captivating and educational, not a dry, bookish report. Make it interesting enough to keep listeners engaged.",
                "4. **Audio Generation:** Use the `generate_audio` tool to convert your script into speech.",
                "5. **Response:** Return the URL of the generated audio file embedded in an HTML audio player. For example: `<audio controls src=\"URL_HERE\" title=\"Generated Audio\"></audio>`  to be propley rendered in markdown and the Text along with that audio supporting the contents of audio",
            ],
            markdown=True,
            stream=True
        )
        return agent
    

    async def run_async(self, text_message: str, attachments: List[Dict[str, str]] = None) -> AsyncGenerator[Dict, None]:
        """
        Runs the agent asynchronously with attachments and streams the response.

        Args:
            text_message (str): The user's text prompt.
            attachments (List[Dict[str, str]], optional): A list of attachments. Defaults to None.

        Yields:
            Dict: A dictionary representing a single event from the agent's run.
        """
        images, videos, audios, files = [], [], [], []

        if attachments:
            for attachment in attachments:
                attachment_type = attachment.get('type')
                url = attachment.get('url')
                if not attachment_type or not url:
                    continue
                
                if attachment_type == 'image':
                    images.append(Image(url=url))
                elif attachment_type == 'video':
                    videos.append(Video(url=url))
                elif attachment_type == 'audio':
                    audios.append(Audio(url=url))
                elif attachment_type == 'file':
                    files.append(File(url=url))

        # Stream with detailed intermediate steps
        response_stream = await self.agent.arun(
            message=text_message,
            images=images or None,
            videos=videos or None,
            audios=audios or None,
            files=files or None,
            stream=True,
            stream_intermediate_steps=True
        )

        # Handle different event types
        async for event in response_stream:
            if event.event == "RunResponseContent":
                if event.content:
                    print(f"Content: {event.content}")
                    yield {'type': 'response', 'data': event.content}
            elif event.event == "ToolCallStarted":
                tool_name = event.tool.tool_name if hasattr(event.tool, 'tool_name') else 'Unknown Tool'
                print(f"Tool call started: {tool_name}")
                yield {'type': 'reasoning', 'data': f"Tool call started: {tool_name}"}
            elif event.event == "ReasoningStep":
                if event.reasoning_content:
                    print(f"Reasoning: {event.reasoning_content}")
                    yield {'type': 'reasoning', 'data': event.reasoning_content}




if __name__ == "__main__":
    try:
        async def main():
            """Asynchronous function to set up and run the agent."""
            agent_instance = AudioTourAgent()
            
            prompt = "Generate an audio tour for the landmark in the image."
            attachments = [
                {
                    'type': 'image',
                    'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg/800px-Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg'
                },
                {
                    'type': 'file',
                    'url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
                }
            ]

            print(f"--- User Prompt ---\n{prompt}\n")
            print(f"--- Attachments ---\n{attachments}\n")
            print("--- Agent Running ---")

            try:
                async for response_part in agent_instance.run_async(prompt, attachments=attachments):
                    print(f"\n--- Agent Event ---\n{response_part}")
            except Exception as e:
                print(f"\nAn error occurred during agent execution: {e}")
            finally:
                print("\n--- Agent Run Finished ---")

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent run interrupted by user.")