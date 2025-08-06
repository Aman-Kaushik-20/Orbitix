from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
import neo4j
from neo4j_graphrag.llm import OpenAILLM
from src.providers.voyage_embedder import VoyageEmbeddings
from neo4j_graphrag.embeddings.base import Embedder
from typing import List, Dict, Any
from loguru import logger

class Neo4jGraphBuilder():

    def __init__(self, driver:neo4j.GraphDatabase.driver, ex_llm:OpenAILLM, embedder:Embedder|VoyageEmbeddings) -> None:
        self.driver=driver
        self.ex_llm=ex_llm
        self.embedder=embedder
    

    async def populate_graph_unstructured(self, entities:List[str], relations:List[str], prompt_template:str, pdf_file_paths:List[str]):
        try:
            kg_builder_pdf = SimpleKGPipeline(
                llm=self.ex_llm,
                driver=self.driver,
                text_splitter=FixedSizeSplitter(chunk_size=1000, chunk_overlap=100),
                embedder=self.embedder,
                entities=entities,
                relations=relations,
                prompt_template=prompt_template,
                from_pdf=True
            )

            for path in pdf_file_paths:
                print(f"Processing : {path}")
                pdf_result = await kg_builder_pdf.run_async(file_path=path)
                print(f"Result: {pdf_result}")

        except Exception as ex:
            raise ex


    async def populate_graph_structured(self,
                                     comtrade_files: List[str] = None,
                                     unido_files: List[str] = None,
                                     lpi_files: List[str] = None,
                                     pdf_files: List[str] = None):
        """Build comprehensive supply chain knowledge graph."""
        all_processed_data = []
        
        if comtrade_files:
            for file_path in comtrade_files:
                if data := self.data_processor.process_comtrade_data(file_path):
                    all_processed_data.append(data)
                    await self._create_trade_flow_graph(data)
        
        if unido_files:
            for file_path in unido_files:
                if data := self.data_processor.process_unido_data(file_path):
                    all_processed_data.append(data)
                    await self._create_industry_graph(data)
        
        if lpi_files:
            for file_path in lpi_files:
                if data := self.data_processor.process_lpi_data(file_path):
                    all_processed_data.append(data)
                    await self._create_logistics_graph(data)
        
        # This step processes the *summaries* from the structured data
        await self._process_structured_data_summaries(all_processed_data)
        logger.info("🎉 Supply chain knowledge graph building complete!")

    async def _create_trade_flow_graph(self, data: Dict[str, Any]):
        """Create structured nodes and relationships from Comtrade data using a TradeFlow node."""
        logger.info(f"Creating graph entities from {data['file_path']}")
        with self.driver.session() as session:
            for flow in data.get('structured_trade_flows', []):
                # This query uses a TradeFlow node to correctly model the relationship
                # between countries, products, and the trade event itself.
                # This avoids the "Type mismatch" error.
                session.run("""
                    // 1. Find or create the primary nodes
                    MERGE (reporter:Country {name: $reporter})
                    MERGE (partner:Country {name: $partner})
                    MERGE (p:Product {name: $commodity_desc, code: $commodity_code})

                    // 2. Create a unique TradeFlow node to represent the event
                    MERGE (tf:TradeFlow {
                        reporter_name: $reporter,
                        partner_name: $partner,
                        product_code: $commodity_code,
                        year: $year,
                        flow: $flow
                    })
                    ON CREATE SET
                        tf.value_usd = $value,
                        tf.quantity = $quantity,
                        tf.weight_kg = $weight
                    ON MATCH SET
                        tf.value_usd = tf.value_usd + $value,
                        tf.quantity = tf.quantity + $quantity

                    // 3. Connect the nodes to the new TradeFlow node
                    MERGE (reporter)-[:REPORTED]->(tf)
                    MERGE (tf)-[:WITH_PARTNER]->(partner)
                    MERGE (tf)-[:OF_PRODUCT]->(p)
                """, **flow)

    async def _create_industry_graph(self, data: Dict[str, Any]):
        """Create structured nodes and relationships from UNIDO data."""
        logger.info(f"Creating graph entities from {data['file_path']}")
        with self.driver.session() as session:
            for metric in data.get('structured_industry_metrics', []):
                # Fix 2: Changed invalid {{...}} to valid {...} for relationship properties
                session.run("""
                    MERGE (c:Country {name: $country})
                    MERGE (i:IndustrySector {name: $industry})
                    MERGE (c)-[r:HAS_INDUSTRY_METRIC {year: $year, variable: $variable}]->(i)
                    ON CREATE SET r.value_usd = $value_usd
                    ON MATCH SET r.value_usd = $value_usd
                """, **metric)

    async def _create_logistics_graph(self, data: Dict[str, Any]):
        """Create structured nodes and relationships from LPI data."""
        logger.info(f"Creating graph entities from {data['file_path']}")
        with self.driver.session() as session:
            for score in data.get('structured_lpi_scores', []):
                prop_key = score['indicator'].split(',')[0].lower().replace(' ', '_').replace('(', '').replace(')', '')
                session.run(f"""
                    MERGE (c:Country {{name: $country}})
                    MERGE (ls:LogisticsScore {{country: $country, year: $year}})
                    MERGE (c)-[:HAS_LPI_SCORE]->(ls)
                    SET ls.`{prop_key}` = $score
                """, country=score['country'], year=score['year'], score=score['score'])