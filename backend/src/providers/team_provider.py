from agno.team.team import Team
from agno.team import Team as OldTeam
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from src.agents.graph_rag_agent import GraphRAGAgent
from src.agents.news_agent import NewsAgent
from src.agents.deep_search_agent import DeepSearchAgent
from src.services.working_memory_service import WorkingMemoryService
from agno.models.message import Message
from typing import List, Union
from typing import Literal, Any
from pydantic import BaseModel
import time
from src.utils.prompts import final_team_agent_instructions, _clean_final_response, _update_team_instructions_with_context

class ChatServiceResponseData(BaseModel):
    type: Literal["reasoning", "response", "end", "error"]
    data: Any

import asyncio


class TeamAgent:
    
    def __init__(self, graph_rag_agent:GraphRAGAgent, news_api_agent:NewsAgent, search_deepsearch_agent:DeepSearchAgent, working_memory_service:WorkingMemoryService, openai_chat_model: OpenAIChat, anthropic_chat_model:Claude, openai_client):
        # Store model reference for potential future optimizations
        self.openai_chat_model = openai_chat_model
        self.anthropic_chat_model = anthropic_chat_model
        self.openai_client = openai_client
        self.team = Team(
            name="Global-Supply-Chain-Agentic-Team",
            mode="route",  # Must specify mode
            model=anthropic_chat_model,
            description="Expert team of Global Supply Chain Query Resolver",
            instructions=final_team_agent_instructions,
            members=[
                graph_rag_agent.agent,
                search_deepsearch_agent.agent,
                news_api_agent.agent,
                working_memory_service.agent
            ],
            show_members_responses=True,
            stream=True,
            # debug_mode=True,
            stream_intermediate_steps=True,
        )   

    def _clean_final_response(self, response: str, user_query: str) -> str:
        """Clean the final response to remove thinking tokens, routing info, and other artifacts"""
        try:
            cleaning_prompt = _clean_final_response(user_query=user_query, response=response)

            response_obj = self.openai_client.responses.create(
                model="gpt-4o-mini",
                input=cleaning_prompt
            )
            
            cleaned = response_obj.output_text
            
            if not cleaned:
                return response
            
            return cleaned.strip()
            
        except Exception as e:
            print(f"Warning: Response cleaning failed: {e}")
            return response  # Return original if cleaning fails
    

    async def arun_team_intermediate_steps(
        self,
        session_id: str,
        user_id: str,
        current_message: Message,
        history_string: str = "",
        episodic_context:str=""
    ):
        final_response:str=""
        thinking_response:str=""
        processed_events = set()  # Track processed events to avoid duplication

        # Store original instructions to restore them in the finally block
        original_instructions = self.team.instructions
        
        try:
            # Temporarily update instructions with dynamic context for this run
            self.team.instructions = _update_team_instructions_with_context(
                original_instructions=original_instructions,
                history_string=history_string,
                episodic_context=episodic_context
            )
            team_start = time.time()
            print(f"⏱️ TeamAgent: Starting team.arun() at {team_start}")
            
            # Add timing for arun initialization
            arun_call_start = time.time()
            team_stream = await self.team.arun(message=current_message, stream=True, session_id=session_id, user_id=user_id, stream_intermediate_steps=True)
            arun_call_end = time.time()
            print(f"⏱️ TeamAgent: team.arun() call took {arun_call_end - arun_call_start:.2f}s")
            
            stream_ready = time.time()
            print(f"⏱️ TeamAgent: Stream ready in {stream_ready - team_start:.2f}s")
            
            first_event_received = False
            
            # Log before starting to iterate over events
            iteration_start = time.time()
            print(f"⏱️ TeamAgent: Starting event iteration at {iteration_start - team_start:.2f}s")    
            
            async for event in team_stream:
                # Handle team events and yield responses
                if not first_event_received:
                    first_event_time = time.time()
                    print(f"⏱️ TeamAgent: First event received in {first_event_time - team_start:.2f}s")
                    print(f"⏱️ TeamAgent: Event type: {event.event}")
                    first_event_received = True
                
                # Log each event type for debugging
                event_time = time.time()
                print(f"⏱️ TeamAgent: Event '{event.event}' at {event_time - team_start:.2f}s")
                
                # Create unique event identifier to avoid duplicates
                event_id = f"{event.event}_{getattr(event, 'tool_call_id', '')if hasattr(event, 'tool_call_id') else id(event)}"
                
                if event_id in processed_events:
                    continue
                processed_events.add(event_id)
                
                if event.event == "TeamRunResponseContent":
                    # Only yield reasoning if there's thinking content but no response content
                    # This avoids mixing agent response chunks with reasoning
                    if event.thinking and not event.content:
                        thinking_response += event.thinking
                        yield ChatServiceResponseData(
                            type='reasoning',
                            data=event.thinking
                        )
                    # Don't accumulate content here - wait for TeamRunCompleted for clean content
                    
                elif event.event == "TeamRunCompleted":
                    # TeamRunCompleted contains the final clean response
                    if hasattr(event, 'content') and event.content:
                        final_response = event.content  # Use clean content from TeamRunCompleted
                    if hasattr(event, 'thinking') and event.thinking:
                        thinking_response += '\n'+event.thinking+'\n'
                        yield ChatServiceResponseData(
                            type='reasoning',
                            data=event.thinking
                        )

                elif event.event == "ToolCallStarted":
                    if event.tool:
                        # Parse tool arguments into readable format
                        args_text = self._parse_tool_args(event.tool.tool_name, event.tool.tool_args)
                        tool_info = f"\n⚙️ Agent Tool: {event.tool.tool_name}\n{args_text}"
                        thinking_response += tool_info
                        print(f"\nMember tool call started: {event.tool.tool_name} {tool_info}")
                        
                        yield ChatServiceResponseData(
                            type='reasoning',
                            data=tool_info
                        )


                elif event.event == "ToolCallCompleted":
                    if event.tool:
                        args_text = self._parse_tool_args(event.tool.tool_name, getattr(event.tool, 'tool_args', {}))
                        success = "✅ SUCCESS" if not getattr(event.tool, 'tool_call_error', False) else "❌ FAILED"
                        tool_info = f"\n🏁 Tool Completed: {event.tool.tool_name}\n{args_text}   → Result: {success}\n"
                        thinking_response += tool_info
                        print(f"Tool call completed: {event.tool.tool_name} - {success} {tool_info}")
                        
                        yield ChatServiceResponseData(
                            type='reasoning',
                            data=tool_info
                        )



                elif event.event == "TeamReasoningStep":
                    # Extract reasoning content properly
                    if hasattr(event, 'reasoning_content') and event.reasoning_content:
                        reasoning_str = event.reasoning_content
                    else:
                        reasoning_str = str(event.content) if event.content else ""
                    thinking_response += f"🧠 Reasoning: {reasoning_str}\n\n"
                    print(f"Reasoning step: {reasoning_str}")
                    
                    yield ChatServiceResponseData(
                        type='reasoning',
                        data=event.reasoning_content
                    )



                elif event.event == "TeamReasoningCompleted":
                    if event.content:
                        content_str = str(event.content)
                        reasoning_info = f"🏁 Reasoning Completed: {content_str}\n\n"
                        thinking_response += reasoning_info
                        print(f"Team reasoning completed: {content_str}")

                        yield ChatServiceResponseData(
                            type='reasoning',
                            data=reasoning_info
                        )

        finally:
            # Always restore the original instructions to keep the team stateless
            self.team.instructions = original_instructions

        # Yield final thoughts and response
        if thinking_response and "thinking" not in processed_events:
            # This part of your function remains the same
            yield ChatServiceResponseData(
                type='reasoning',
                data='\n\n-------------------------------------------\n🚀 Preparing final response... ✨\n---'
            )
            cleaned_response = self._clean_final_response(final_response, current_message.content)
            yield ChatServiceResponseData(
                type='response',
                data=cleaned_response
            )
        
        yield ChatServiceResponseData(
                type='end',
                data=(final_response, thinking_response)
            )
    

    # helper function to parse streaming tool events into userpresntable strings
    def _parse_tool_args(self, tool_name: str, tool_args: dict) -> str:
        """Parse tool arguments into readable format based on tool type"""
        if not tool_args:
            return "   (No arguments)\n"
        
        if tool_name == "think":
            return f"""   📝 Title: {tool_args.get('title', 'N/A')}
   💭 Thought: {tool_args.get('thought', 'N/A')[:400]}{'...' if len(str(tool_args.get('thought', ''))) > 400 else ''}
   🎯 Action: {tool_args.get('action', 'N/A')}
   🎲 Confidence: {tool_args.get('confidence', 'N/A')}
"""
        
        elif tool_name == "compare_retrieval_strategies" or tool_name == "search_news_everything" or tool_name=="perplexity_search" or tool_name=='fetch_recent_history' or tool_name=='fetch_all_session_history':
            strategies = tool_args.get('strategies', [])
            strategies_str = ', '.join(strategies) if isinstance(strategies, list) else str(strategies)
            return f"""   🔍 Query: {tool_args.get('query', 'N/A')}
   📊 Strategies: {strategies_str}
   🔢 Top K: {tool_args.get('top_k', 'N/A')}
"""
        
        elif tool_name == "analyze":
            result_preview = str(tool_args.get('result', 'N/A'))[:400]
            analysis_preview = str(tool_args.get('analysis', 'N/A'))[:400]
            return f"""   📝 Title: {tool_args.get('title', 'N/A')}
   📋 Result: {result_preview}{'...' if len(str(tool_args.get('result', ''))) > 400 else ''}
   🔬 Analysis: {analysis_preview}{'...' if len(str(tool_args.get('analysis', ''))) > 400 else ''}
   ➡️ Next Action: {tool_args.get('next_action', 'N/A')}
   🎲 Confidence: {tool_args.get('confidence', 'N/A')}
"""
        
        else:
            # Generic parsing for unknown tools
            parsed_args = []
            for key, value in tool_args.items():
                value_str = str(value)[:400] + ('...' if len(str(value)) > 400 else '')
                parsed_args.append(f"   {key}: {value_str}")
            return '\n'.join(parsed_args) + '\n'



# /home/username/global-supply-chain/.venv/lib/python3.12/site-packages/agno/run/team.py -> all events type and classes
# /home/username/global-supply-chain/.venv/lib/python3.12/site-packages/agno/run/response.py 