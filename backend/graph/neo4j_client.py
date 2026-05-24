import logging
from neo4j import AsyncGraphDatabase
from contextlib import asynccontextmanager
from backend.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self._driver = AsyncGraphDatabase.driver(
            uri, auth=(user, password), max_connection_pool_size=50
        )
    
    async def close(self):
        if self._driver:
            await self._driver.close()
            
    @asynccontextmanager
    async def session(self):
        from backend.core.resilience import with_retry
        
        @with_retry(max_attempts=3)
        async def _get_session():
            return self._driver.session()
            
        # We can't retry the yielded block easily, but we can retry session creation
        # which is often where connection pool errors occur
        try:
            async with self._driver.session() as session:
                yield session
        except Exception as e:
            logger.error(f"Neo4j session error: {e}")
            raise
            
    async def check_health(self) -> bool:
        try:
            async with self.session() as session:
                result = await session.run("RETURN 1 AS num")
                record = await result.single()
                return record and record["num"] == 1
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False
            
    async def create_constraints(self):
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symbol) REQUIRE s.chunk_id IS UNIQUE",
            "CREATE INDEX symbol_qname_repo IF NOT EXISTS FOR (s:Symbol) ON (s.qualified_name, s.repo_id)",
            "CREATE INDEX file_path_repo IF NOT EXISTS FOR (f:File) ON (f.path, f.repo_id)",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (svc:Service) REQUIRE svc.name IS UNIQUE"
        ]
        async with self.session() as session:
            for query in queries:
                await session.run(query)

neo4j_client = Neo4jClient(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
