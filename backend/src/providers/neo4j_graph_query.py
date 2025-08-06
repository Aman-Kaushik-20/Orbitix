import neo4j
from typing import List, Optional, Dict, Any
import json
from enum import Enum


from src.providers.voyage_embedder import VoyageEmbeddings
from src.utils.prompts import cypher_rag_retriever_prompt, rag_template_prompt, vector_rag_prompt, graph_rag_prompt, hybrid_rag_prompt

from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import RagTemplate
from neo4j_graphrag.generation.graphrag import GraphRAG
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.retrievers import VectorCypherRetriever, HybridRetriever, HybridCypherRetriever
from neo4j_graphrag.generation.prompts import PromptTemplate
from loguru import logger


class strategy(str, Enum):
    vector="vector"
    vector_cypher="vector_cypher"
    hybrid="hybrid"
    hybrid_cypher="hybrid_cypher"


class Neo4jGraphQuery():
    def __init__(self,
        driver: neo4j.Driver,
        ex_llm : OpenAILLM,
        embedder: Optional[Embedder] = None,
        index_name: str="voyage_embeddings",

        ):
        self.driver=driver
        self.index_name=index_name
        self.embedder=embedder
        self.ex_llm=ex_llm

        self.setup_retriever()
        self.setup_graph_rag()


    def setup_retriever(self):
        # Enhanced retrieval setup with multiple strategies
        self.vector_retriever_voyage = VectorRetriever(
            self.driver,
            index_name=self.index_name,
            embedder=self.embedder,
            return_properties=["text"],
        )

        # Enhanced vector+cypher retriever for supply chain traversal
        self.vc_retriever_voyage_cypher = VectorCypherRetriever(
            self.driver,
            index_name=self.index_name,
            embedder=self.embedder,
            retrieval_query=cypher_rag_retriever_prompt
        )
        
        # Hybrid retriever for text + vector search
        try:
            self.hybrid_retriever = HybridRetriever(
                self.driver,
                vector_index_name=self.index_name,
                fulltext_index_name="fulltext_chunk_index",
                embedder=self.embedder,
                return_properties=["text"]
            )
        except Exception as e:
            logger.warning(f"Hybrid retriever setup failed: {e}")
            self.hybrid_retriever = None

        # Hybrid + Cypher for comprehensive retrieval
        try:
            self.hybrid_cypher_retriever = HybridCypherRetriever(
                self.driver,
                vector_index_name=self.index_name,
                fulltext_index_name="fulltext_chunk_index", 
                embedder=self.embedder,
                retrieval_query=cypher_rag_retriever_prompt
            )
        except Exception as e:
            logger.warning(f"Hybrid Cypher retriever setup failed: {e}")
            self.hybrid_cypher_retriever = None



    def create_index(self, new_index_name:str, new_dimension:int, similarity_fn:str):
        # Create a NEW index with a different name and the correct dimensions for Voyage
        create_vector_index(
            self.driver, 
            name=new_index_name, 
            label="Chunk",
            embedding_property="embedding", 
            dimensions=new_dimension,  # Correct dimension for Voyage models
            similarity_fn=similarity_fn
        )


    def create_fulltext_index(self):
        """Create fulltext search index for hybrid retrieval"""
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE FULLTEXT INDEX fulltext_chunk_index IF NOT EXISTS
                    FOR (n:Chunk) ON EACH [n.text]
                """)
                logger.info("Fulltext index created successfully")
        except Exception as e:
            logger.error(f"Failed to create fulltext index: {e}")

    def setup_graph_rag(self,):
        vector_cypher_rag_template = RagTemplate(
            template=graph_rag_prompt,
            expected_inputs=['query_text', 'context']
        )
        hybrid_cypher_rag_template=RagTemplate(
            template=graph_rag_prompt,
            expected_inputs=['query_text', 'context']
        )
        hybrid_rag_template=RagTemplate(
            template=hybrid_rag_prompt,
            expected_inputs=['query_text', 'context']
        )
        vector_rag_template=RagTemplate(
            template=vector_rag_prompt,
            expected_inputs=['query_text', 'context']
        )
        vector_cypher = GraphRAG(
                llm=self.ex_llm, 
                retriever=self.vc_retriever_voyage_cypher, 
                prompt_template=vector_cypher_rag_template
            )
        hybrid_cypher_graph_rag = GraphRAG(
                llm=self.ex_llm, 
                retriever=self.hybrid_cypher_retriever, 
                prompt_template=hybrid_cypher_rag_template
            )
        vector_graph_rag = GraphRAG(
                llm=self.ex_llm, 
                retriever=self.vector_retriever_voyage, 
                prompt_template=vector_rag_template
            )
        hybrid_graph_rag = GraphRAG(
                llm=self.ex_llm, 
                retriever=self.hybrid_retriever, 
                prompt_template=hybrid_rag_template
            )
        self.graph_rag_dict={
           "vector_cypher": vector_cypher,
           "hybrid_cypher":hybrid_cypher_graph_rag,
           "hybrid":hybrid_graph_rag,
           "vector":vector_graph_rag
        }


    def query_graph_rag(self, 
        query_text: str,
        retrieval_strategy: str = "vector_cypher",  # "vector", "vector_cypher", "hybrid", "hybrid_cypher"
        top_k: int = 5,
        include_analytics: bool = True):
        """
        Enhanced GraphRAG querying with multiple retrieval strategies
        
        Args:
            query_text: The question to answer
            retrieval_strategy: Strategy for retrieving relevant information
            top_k: Number of top results to retrieve  
            include_analytics: Whether to include supply chain analytics
        """
        try:
            graph_rag=self.graph_rag_dict.get(retrieval_strategy, None)
            if graph_rag is None:
                logger.error(f'GraphRag Initialization Failed at src.providers.neo4j_graph_query.py')
                raise
            
            result = graph_rag.search(
                query_text, 
                retriever_config={'top_k': top_k}
            )
            
            response = {
                "strategy": retrieval_strategy,
                "answer": result.answer,
                "retrieval_config": {"top_k": top_k, "strategy": retrieval_strategy}
            }
            
            if include_analytics:
                # Add supply chain specific analytics if available
                response["metadata"] = self._extract_supply_chain_metadata(result)
                
            return response
            
        except Exception as e:
            logger.error(f"GraphRAG query failed: {e}")
            return {
                "strategy": retrieval_strategy,
                "answer": f"Query failed: {str(e)}",
                "error": True
            }

    def _extract_supply_chain_metadata(self, result) -> Dict[str, Any]:
        """Extract supply chain specific metadata from results"""
        metadata = {}
        
        # This would be enhanced based on your specific result structure
        # For now, return basic metadata
        metadata["query_successful"] = True
        metadata["response_length"] = len(result.answer) if hasattr(result, 'answer') else 0
        
        return metadata

    def compare_retrieval_strategies(self, query_text: str, top_k: int = 3, strategies:List[strategy]=["vector", "vector_cypher", "hybrid", "hybrid_cypher"]):
        """Compare different retrieval strategies for the same query"""
            
        results = {}
        
        for strategy in strategies:
            try:
                result = self.query_graph_rag(
                    query_text=query_text,
                    retrieval_strategy=strategy,
                    top_k=top_k,
                    include_analytics=False
                )
                results[strategy] = result
            except Exception as e:
                results[strategy] = {"error": str(e)}
                
        return results
