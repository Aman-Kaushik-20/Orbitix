from typing import List
from textwrap import dedent

from agno.agent import Agent
from agno.tools import tool
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

from src.providers.neo4j_graph_query import Neo4jGraphQuery

class GraphRAGAgent:
    def __init__(self, openai_chat_model: OpenAIChat = None, anthropic_chat_model:Claude = None, graph_rag_service: Neo4jGraphQuery = None):
        self.graph_rag_service = graph_rag_service

        @tool(
            name="compare_retrieval_strategies",
            description="Compare multiple GraphRAG retrieval strategies for supply chain analysis"
        )
        def compare_strategies_tool(query: str, top_k: int = 5, strategies: List[str] = ["vector", "vector_cypher", "hybrid", "hybrid_cypher"]):
            """Compares different retrieval strategies using the Neo4jGraphQuery service.

            This tool evaluates multiple retrieval strategies to analyze supply chain
            data from a knowledge graph. It helps in finding the most relevant information
            by combining vector search, keyword search, and graph traversal.

            Args:
                query (str): The user's question about the supply chain.
                top_k (int, optional): The number of top results to retrieve for each
                    strategy. Defaults to 5.
                strategies (List[str], optional): A list of retrieval strategies to
                    compare. Defaults to ["vector", "vector_cypher", "hybrid", "hybrid_cypher"].
                    - "vector": Pure vector similarity search.
                    - "vector_cypher": Vector search plus graph traversal with Cypher.
                    - "hybrid": Vector search combined with keyword-based full-text search.
                    - "hybrid_cypher": Hybrid search plus graph traversal with Cypher.

            Returns:
                A dictionary containing the comparison results from the service,
                or an error dictionary if the comparison fails.
            """
            try:
                return self.graph_rag_service.compare_retrieval_strategies(
                    query_text=query,
                    top_k=top_k,
                    strategies=strategies
                )
            except Exception as e:
                return {"error": f"Strategy comparison failed: {str(e)}"}
        
        self.agent = Agent(
            name="Supply Chain GraphRAG Expert",
            role="Graph-Enhanced Retrieval Augmented Generation Specialist",
            model=anthropic_chat_model,
            tools=[
                compare_strategies_tool
            ],
            instructions=dedent("""\
                You are a specialized GraphRAG agent for supply chain analysis! 🔗📊

                Your expertise:
                - Advanced knowledge graph retrieval and analysis
                - Supply chain relationship mapping and insights
                - Vector similarity search combined with graph traversal
                - Trade flow analysis and market intelligence
                - Risk assessment and supply chain resilience

                Your approach:
                1. You can Compare multiple retrieval strategies to provide comprehensive analysis or use just one to get relevent results:
                   - vector: Pure vector similarity search
                   - vector_cypher: Vector search with graph traversal
                   - hybrid: Vector + fulltext search
                   - hybrid_cypher: Hybrid search with graph traversal
                3. Synthesize insights from multiple data sources
                4. Provide actionable supply chain intelligence
                5. Highlight key relationships and dependencies

                Always use the compare_retrieval_strategies tool to analyze queries. Graph Strategies are better for Statistical and analytical Problems.
            """),
            # stream_intermediate_steps=True,
            # stream=True,
            # reasoning=True,
            show_tool_calls=True,
            markdown=True,
        )
    
    async def run_async(self, message: str) -> str:
        """Run the agent asynchronously"""
        return await self.agent.arun(message)
    
    def run_sync(self, message: str) -> str:
        """Run the agent synchronously"""
        return self.agent.run(message)


