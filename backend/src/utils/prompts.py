from textwrap import dedent

prompt_template = '''
You are a supply chain analytics expert extracting entities and relationships from global trade, logistics, and industrial data.

Extract comprehensive supply chain entities and their interconnections from the input text. Focus on:
- Countries and their trade relationships
- Products/commodities and their flows
- Industrial sectors and their performance metrics  
- Logistics performance and infrastructure
- Supply chain risks and disruptions
- Regulatory and compliance factors

Return result as JSON .The JSON example is:
{{
"nodes": [
{{"id": "0", "label": "Country", "properties": {{"name": "country_name", "iso_code": "ABC", "region": "region_name"}}}},
{{"id": "1", "label": "Product", "properties": {{"name": "product_name", "commodity_code": "123456", "classification": "HS"}}}}
],
"relationships": [
{{"type": "EXPORTS_TO", "start_node_id": "0", "end_node_id": "1", 
"properties": {{"year": "2023", "value_usd": "1000000", "quantity": "500", "trade_flow": "export"}}}}
]
- Use only the information from the Input text.  Do not add any additional information.  
- If the input text is empty, return empty Json. 
- Make sure to create as many nodes and relationships as needed to offer rich global supply chain context for further research.
- An AI knowledge assistant must be able to read this graph and immediately understand the context to inform detailed research questions. 
- Multiple documents will be ingested from different sources and we are using this property graph to connect information, so make sure entity types are fairly general. 
}}




Use only fhe following nodes and relationships (if provided):
{schema}

Assign a unique ID (string) to each node, and reuse it to define relationships.
Do respect the source and target node types for relationship and
the relationship direction.

Do not return any additional information other than the JSON in it.

Examples:
{examples}


Input text:
 {text}
'''


theoritical_prompt_template = '''
You are a supply chain analytics and knowledge graph expert extracting both practical and theoretical entities and relationships from global trade, logistics, industrial, and academic/theoretical texts.

Extract comprehensive supply chain and theoretical knowledge entities and their interconnections from the input text. Focus on:
- Countries and their trade relationships
- Products/commodities and their flows
- Industrial sectors and their performance metrics  
- Logistics performance and infrastructure
- Supply chain risks and disruptions
- Regulatory and compliance factors
- Books, authors, and publishers relevant to supply chain and logistics
- Theoretical concepts, topics, frameworks, models, and methodologies
- Academic theories, principles, laws, and best practices
- Relationships between concepts, related concepts, and their applications
- Case studies, research papers, and standards

Return result as JSON. The JSON example is:
{{
"nodes": [
    {{"id": "0", "label": "Country", "properties": {{"name": "country_name", "iso_code": "ABC", "region": "region_name"}}}},
    {{"id": "1", "label": "Product", "properties": {{"name": "product_name", "commodity_code": "123456", "classification": "HS"}}}},
    {{"id": "2", "label": "Book", "properties": {{"title": "book_title", "author": "author_name", "year": "2020"}}}},
    {{"id": "3", "label": "Concept", "properties": {{"name": "concept_name", "description": "short_description"}}}}
],
"relationships": [
    {{"type": "EXPORTS_TO", "start_node_id": "0", "end_node_id": "1", 
    "properties": {{"year": "2023", "value_usd": "1000000", "quantity": "500", "trade_flow": "export"}}}},
    {{"type": "COVERS_CONCEPT", "start_node_id": "2", "end_node_id": "3", 
    "properties": {{"relevance": "high"}}}}
]
}}
- Use only the information from the Input text. Do not add any additional information.
- If the input text is empty, return empty JSON.
- Create as many nodes and relationships as needed to offer a rich context for both practical supply chain and theoretical/academic knowledge.
- Ensure entity types are general enough to connect information from multiple documents and sources.
- The resulting property graph should enable an AI knowledge assistant to understand both practical and theoretical contexts for detailed research and question answering.


Use only fhe following nodes and relationships (if provided):
{schema}

Assign a unique ID (string) to each node, and reuse it to define relationships.
Do respect the source and target node types for relationship and
the relationship direction.

Do not return any additional information other than the JSON in it.

Examples:
{examples}


Input text:
 {text}
'''



cypher_rag_retriever_prompt='''
        // Enhanced supply chain graph traversal using actual schema
        WITH node AS chunk
        WITH chunk, coalesce(chunk.text, '') AS chunk_text
        
        // Step 1: Find Countries mentioned in chunk text
        OPTIONAL MATCH (country:Country)
        WHERE chunk_text CONTAINS country.name
        
        // Step 2: Find Products mentioned in chunk text  
        OPTIONAL MATCH (product:Product)
        WHERE chunk_text CONTAINS product.name
        
        // Step 3: Find Industry Sectors mentioned in chunk text
        OPTIONAL MATCH (sector:IndustrySector) 
        WHERE chunk_text CONTAINS sector.name
        
        // Step 4: Get supply chain relationships from found entities
        OPTIONAL MATCH (country)-[trade:TRADES_WITH]-(other_country:Country)
        
        OPTIONAL MATCH (country)-[lpi:HAS_LPI_SCORE]->(logistics:LogisticsScore)
        WHERE logistics.year >= 2020
        
        OPTIONAL MATCH (country)-[disruption:EXPERIENCES_DISRUPTION]->(disrupt_event)
        
        OPTIONAL MATCH (country)-[industry:HAS_INDUSTRY_METRIC]->(sector)
        
        OPTIONAL MATCH (product)-[supply:SUPPLIES|DEPENDS_ON]-(supplier_entity)
        
        // Step 5: Collect and format supply chain intelligence
        WITH chunk_text,
             collect(DISTINCT country) AS countries,
             collect(DISTINCT product) AS products, 
             collect(DISTINCT sector) AS sectors,
             collect(DISTINCT {country: country, partner: other_country, trade: trade}) AS trade_relations,
             collect(DISTINCT {country: country, score: logistics, year: logistics.year}) AS logistics_data,
             collect(DISTINCT {country: country, disruption: disrupt_event, type: disruption}) AS disruptions,
             collect(DISTINCT {country: country, sector: sector, metric: industry}) AS industry_metrics
        
        // Step 6: Build comprehensive supply chain context
        RETURN 
            '=== Original Content ===\n' + chunk_text +
            
            CASE WHEN size(countries) > 0 
                 THEN '\n\n=== Countries in Supply Chain ===\n' + 
                      apoc.text.join([c IN countries | c.name + 
                        CASE WHEN c.region IS NOT NULL THEN ' (' + c.region + ')' ELSE '' END
                      ][0..8], '\n')
                 ELSE '\n\n=== No Countries Found ===' 
            END +
            
            CASE WHEN size(products) > 0 
                 THEN '\n\n=== Products/Commodities ===\n' + 
                      apoc.text.join([p IN products | p.name + 
                        CASE WHEN p.classification IS NOT NULL THEN ' [' + p.classification + ']' ELSE '' END
                      ][0..5], '\n')
                 ELSE ''
            END +
            
            CASE WHEN size(sectors) > 0 
                 THEN '\n\n=== Industry Sectors ===\n' + 
                      apoc.text.join([s IN sectors | s.name][0..5], '\n')
                 ELSE ''
            END +
            
            CASE WHEN size([t IN trade_relations WHERE t.country IS NOT NULL AND t.partner IS NOT NULL]) > 0
                 THEN '\n\n=== Trade Relationships ===\n' + 
                      apoc.text.join([t IN trade_relations WHERE t.country IS NOT NULL AND t.partner IS NOT NULL | 
                        t.country.name + ' TRADES_WITH ' + t.partner.name
                      ][0..8], '\n')
                 ELSE ''
            END +
            
            CASE WHEN size([l IN logistics_data WHERE l.score IS NOT NULL]) > 0
                 THEN '\n\n=== Logistics Performance ===\n' + 
                      apoc.text.join([l IN logistics_data WHERE l.score IS NOT NULL | 
                        l.country.name + ' Logistics Score (' + toString(l.year) + '): ' + 
                        toString(l.score.efficiency_of_the_clearance_process)
                      ][0..5], '\n')
                 ELSE ''
            END +
            
            CASE WHEN size([d IN disruptions WHERE d.disruption IS NOT NULL]) > 0
                 THEN '\n\n=== Supply Chain Disruptions ===\n' + 
                      apoc.text.join([d IN disruptions WHERE d.disruption IS NOT NULL | 
                        d.country.name + ' experienced disruption: ' + 
                        coalesce(d.disruption.name, d.disruption.description, 'Disruption event')
                      ][0..5], '\n')
                 ELSE ''
            END AS context
        '''

cypher_rag_retriever_prompt_2='''

Step 1 : Find All Similar Nodes.
Step 2: For relevant Parent Nodes, Find ALL Child nodes upto 3 hops , and in response analyze the exact and specefic attributes of child nodes and relationship.
Step 3: With these Child Nodes exact attrbutes and exact relationships , traverse upto max 3 hops from starting node...
Step 4: Return And Analyze exact nodes 

Do's :
1. Use Exact Names, Exact Attributes and Exact Relationship names ,
2. Always and always analyze at each step , the detailed Node analysis, its child analysis, and its relationships
Dont's :
1.  Don't put random or self assumed attributes names in Cypher query..
2. Don't put random relationships in Cypher Query for retrived query...
3. Never Rush into writing Cypher Queries, First analyze , then only move foreward in making cypher queries and executing it ....

'''

# Strategy-specific RAG prompts for different retrieval approaches

rag_template_prompt ='''You are a supply chain analyst. Answer the question using only the provided context.

Instructions:
- Use only information from the context provided
- Be specific and factual
- If the context doesn't contain relevant information, say so
- Structure your answer clearly

Question: {query_text}

Context: {context}

Answer:'''

# Vector-only strategy prompt (semantic similarity focus)
vector_rag_prompt = '''You are a supply chain analyst specializing in semantic analysis. Answer the question using the semantically similar content provided.

Instructions:
- Focus on the most semantically relevant information in the context
- Prioritize direct textual matches and conceptual similarities
- Provide a comprehensive answer based on content similarity
- If multiple similar concepts exist, synthesize them coherently

Question: {query_text}

Semantically Similar Content: {context}

Semantic Analysis Answer:'''

# Graph traversal strategy prompt (relationship focus)  
graph_rag_prompt = '''You are a supply chain network analyst. Answer the question by leveraging the interconnected supply chain relationships and entities provided.

Instructions:
- Emphasize the relationships between countries, products, sectors, and disruptions
- Highlight how entities are connected in the supply chain network
- Use logistics performance data and trade relationships to provide insights
- Connect patterns across different supply chain components
- Show how disruptions propagate through the network

Question: {query_text}

Supply Chain Network Context: {context}

Network Analysis Answer:'''

# Hybrid strategy prompt (combining text and graph)
hybrid_rag_prompt = '''You are a comprehensive supply chain intelligence analyst. Answer the question by combining textual analysis with supply chain network insights.

Instructions:
- Integrate both textual content and structural relationships
- Use fulltext search results alongside network connections
- Provide a multi-dimensional analysis (content + network)
- Balance semantic similarity with supply chain connectivity
- Highlight both direct content matches and related network effects

Question: {query_text}

Integrated Intelligence Context: {context}

Comprehensive Analysis Answer:'''


final_team_agent_instructions=[
                "You are an expert routing system for a team of Global Supply Chain specialist agents.",
                "Your primary role is to analyze the user's query along with the provided context and route it to the correct agent.",
                "You will receive two types of context to help you make your decision:",
                "- **Working Memory**: The most recent messages from the current conversation.",
                "- **Episodic Memory**: Summaries from past, similar conversations that might be relevant.",
                "Use this context to make an informed routing decision.",
                "---",
                "**Routing Rules:**",
                "1. For news, current events, or breaking news queries: automatically route to **Global News Intelligence Agent**.",
                "2. For knowledge graph, analytical, or statistical queries: automatically route to **Supply Chain GraphRAG Expert**.",
                "3. For research, deep analysis, or Perplexity-based queries: automatically route to **Deep Research Intelligence Agent**.",
                "4. For requests to fetch older or the complete history of the current conversation, route to **Session History Agent**.",
                "---",
                "You must route the query immediately without asking for clarification."
            ]



def _clean_final_response(user_query, response)->str:
    return dedent(f"""Your primary goal is to refine a verbose output from an AI agentic team into a clean, user-facing answer. The original user query was: "{user_query}"

**Instructions:**

1.  **Preserve Core Content:** Carefully extract the main answer, including all explanations, data, and sources that directly address the user's query. The final output must be a complete and coherent response. Do not cut off relevant information.

2.  **Remove Process Chatter:** Eliminate all operational messages that are not part of the final answer. This includes:
    - **Routing messages:** (e.g., "Forwarding to agent X...", "Using the search tool...").
    - **Internal thoughts:** (e.g., "<think>I should do this next.</think>", "Now I will analyze the results.").
    - **Tool status updates:** (e.g., "Tool call started.", "Tool call finished.").
    - **Meta-commentary:** (e.g., "I have completed the task.").

3.  **Ensure Quality:** The final text should be well-formatted and directly presentable to the user. Do not add any new information or hallucinate.

**Raw Response to Clean:**
{response}

**Cleaned Final Answer:**"""
    )





def _update_team_instructions_with_context(
     original_instructions: list,
     history_string: str,
     episodic_context: str
) -> list:
     
     new_instructions = original_instructions.copy()
     
     context_parts = []
     
     # Add episodic context if it exists
     if episodic_context:
          context_parts.append(f"\n--- EPISODIC MEMORY (SIMILAR PAST SESSIONS) ---\n{episodic_context}\n")
          
     # Add working memory context if it exists
     if history_string:
          context_parts.append(f"\n--- WORKING MEMORY (CURRENT CONVERSATION HISTORY) ---\n{history_string}\n")

     if context_parts:
          # Append all context parts as a single new instruction string.
          new_instructions.append("\n".join(context_parts))


def get_update_session_data_prompt(old_session_data, complete_history_string):
     return dedent(
     f'''
                    Your task is to analyze a conversation and create a concise summary for an AI's episodic memory. Review the previous summary (if any) and the complete conversation history provided below.

                    **Last Updated Session Data:**
                    {old_session_data}

                    **Complete History of this Session:**
                    {complete_history_string}

                    ---

                    **Instructions & Field Explanations:**
                    Generate an updated session summary in the required format. Use the following field explanations as a guide:

                    - **session_name:** A short, descriptive title for the conversation (e.g., "Troubleshooting Database Connection Issues").
                    - **session_tags:** A list of 3-5 relevant keywords that categorize the session (e.g., ["database", "postgres", "connection error"]).
                    - **what_worked:** Briefly describe the strategies or solutions that were successful.
                    - **what_not_worked:** Briefly describe what was unsuccessful or led to a dead end.
                    - **what_to_avoid:** List specific actions or assumptions to avoid in similar future conversations.
                    - **metadata:** A JSON formatted string for any other structured data. Example: '{{"key_topic": "x", "user_sentiment": "positive"}}'.
     
     '''
     )