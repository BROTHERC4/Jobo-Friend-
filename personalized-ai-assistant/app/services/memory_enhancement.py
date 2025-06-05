from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import anthropic
from app.services.memory import IntelligentMemoryService
from app.config import get_settings
import logging
import json

logger = logging.getLogger(__name__)
settings = get_settings()

class MemoryConsolidationService:
    """
    Enhanced memory service that adds conversation summarization,
    memory consolidation, and intelligent memory management.
    
    This service helps Jobo maintain high-quality, organized memories
    by summarizing long conversations and organizing related memories.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory_service = IntelligentMemoryService(user_id)
        self.client = None
        self._initialize_claude_client()
    
    def _initialize_claude_client(self):
        """Initialize Claude client for summarization"""
        try:
            if settings.anthropic_api_key:
                self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                logger.debug("✅ Memory consolidation service initialized")
            else:
                logger.warning("❌ Memory consolidation unavailable - no API key")
        except Exception as e:
            logger.error(f"❌ Failed to initialize memory consolidation: {e}")
    
    async def consolidate_conversation(self, conversation_messages: List[Dict[str, Any]]) -> Optional[str]:
        """
        Consolidate a conversation into a meaningful summary for long-term storage.
        
        Args:
            conversation_messages: List of conversation messages
            
        Returns:
            Memory ID of the consolidated summary, or None if failed
        """
        if not self.client or not conversation_messages:
            return None
        
        try:
            # Create conversation text
            conversation_text = self._format_conversation(conversation_messages)
            
            # Generate intelligent summary
            summary = await self._generate_conversation_summary(conversation_text)
            
            if summary:
                # Extract key insights and metadata
                metadata = await self._extract_conversation_metadata(conversation_text, summary)
                
                # Store consolidated memory
                memory_id = self.memory_service.add_memory(
                    text=summary,
                    metadata={
                        **metadata,
                        "type": "conversation_summary",
                        "original_message_count": len(conversation_messages),
                        "consolidated_at": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"✅ Consolidated conversation into memory {memory_id}")
                return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to consolidate conversation: {e}")
        
        return None
    
    def _format_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation messages for summarization"""
        formatted_lines = []
        
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            # Format with role prefix
            if role == 'user':
                prefix = "User:"
            elif role == 'assistant':
                prefix = "Jobo:"
            else:
                prefix = f"{role.title()}:"
            
            formatted_lines.append(f"{prefix} {content}")
        
        return "\n".join(formatted_lines)
    
    async def _generate_conversation_summary(self, conversation_text: str) -> Optional[str]:
        """Generate an intelligent summary of the conversation"""
        try:
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Please create a comprehensive but concise summary of this conversation between a user and Jobo (an AI assistant). Focus on:

1. Key topics discussed
2. Important insights or learning points
3. User's questions, interests, and preferences revealed
4. Any patterns in communication style
5. Actionable outcomes or next steps

Conversation:
{conversation_text}

Summary:"""
                }]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
            return None
    
    async def _extract_conversation_metadata(self, conversation_text: str, summary: str) -> Dict[str, Any]:
        """Extract structured metadata from conversation"""
        try:
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"""Based on this conversation and its summary, extract key metadata in JSON format:

Conversation: {conversation_text[:1000]}...
Summary: {summary}

Please provide JSON with these fields:
- "topics": list of main topics (max 5)
- "user_interests": list of user interests revealed (max 3) 
- "sentiment": overall sentiment (positive/neutral/negative)
- "complexity": conversation complexity (simple/medium/complex)
- "user_learning": what the user learned or was curious about
- "communication_style": user's communication style observations

JSON:"""
                }]
            )
            
            # Try to parse JSON response
            metadata_text = response.content[0].text.strip()
            try:
                return json.loads(metadata_text)
            except json.JSONDecodeError:
                # Fallback to basic metadata
                return {
                    "topics": ["general_conversation"],
                    "sentiment": "neutral",
                    "complexity": "medium"
                }
                
        except Exception as e:
            logger.error(f"Failed to extract conversation metadata: {e}")
            return {"topics": ["general_conversation"]}
    
    async def identify_memory_clusters(self, max_clusters: int = 10) -> List[Dict[str, Any]]:
        """
        Identify clusters of related memories for better organization.
        
        Returns:
            List of memory clusters with their themes and member memories
        """
        if not self.memory_service.chroma_available:
            return []
        
        try:
            # Get all memories for this user
            all_memories = self._get_all_user_memories()
            
            if len(all_memories) < 3:
                return []  # Need at least 3 memories to cluster
            
            # Use Claude to identify thematic clusters
            clusters = await self._generate_memory_clusters(all_memories, max_clusters)
            
            logger.info(f"🧠 Identified {len(clusters)} memory clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to identify memory clusters: {e}")
            return []
    
    def _get_all_user_memories(self) -> List[Dict[str, Any]]:
        """Get all memories for clustering analysis"""
        if not self.memory_service.collection:
            return []
        
        try:
            # Get all memories (limit for performance)
            results = self.memory_service.collection.get(
                limit=100,
                include=['documents', 'metadatas']
            )
            
            memories = []
            documents = results.get('documents', [])
            metadatas = results.get('metadatas', [])
            
            for doc, meta in zip(documents, metadatas):
                memories.append({
                    'text': doc,
                    'metadata': meta or {}
                })
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            return []
    
    async def _generate_memory_clusters(self, memories: List[Dict[str, Any]], max_clusters: int) -> List[Dict[str, Any]]:
        """Use Claude to identify thematic clusters in memories"""
        try:
            # Prepare memory summaries for clustering
            memory_summaries = []
            for i, memory in enumerate(memories[:50]):  # Limit for API call size
                text = memory['text'][:200]  # Truncate for API limits
                memory_summaries.append(f"Memory {i+1}: {text}")
            
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze these memories and identify thematic clusters. Group related memories together and provide:

1. Cluster theme/topic
2. Brief description
3. List of memory numbers that belong to this cluster

Memories:
{chr(10).join(memory_summaries)}

Please identify up to {max_clusters} clusters and format as JSON:
[
  {{
    "theme": "cluster theme",
    "description": "what this cluster represents",
    "memory_indices": [1, 3, 5],
    "strength": "high/medium/low"
  }}
]

JSON:"""
                }]
            )
            
            # Parse response
            clusters_text = response.content[0].text.strip()
            try:
                clusters_data = json.loads(clusters_text)
                
                # Convert to full cluster objects
                full_clusters = []
                for cluster in clusters_data:
                    cluster_memories = []
                    for idx in cluster.get('memory_indices', []):
                        if 0 <= idx-1 < len(memories):  # Convert to 0-based indexing
                            cluster_memories.append(memories[idx-1])
                    
                    if cluster_memories:  # Only add clusters with valid memories
                        full_clusters.append({
                            'theme': cluster.get('theme', 'Unknown Theme'),
                            'description': cluster.get('description', ''),
                            'strength': cluster.get('strength', 'medium'),
                            'memories': cluster_memories,
                            'memory_count': len(cluster_memories)
                        })
                
                return full_clusters
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse cluster JSON response")
                return []
                
        except Exception as e:
            logger.error(f"Failed to generate memory clusters: {e}")
            return []
    
    async def optimize_memory_storage(self) -> Dict[str, Any]:
        """
        Optimize memory storage by consolidating similar memories
        and removing redundant information.
        
        Returns:
            Optimization results and statistics
        """
        try:
            # Get memory statistics before optimization
            initial_stats = self.memory_service.get_memory_statistics()
            
            # Identify clusters for optimization
            clusters = await self.identify_memory_clusters()
            
            optimized_clusters = 0
            memories_consolidated = 0
            
            for cluster in clusters:
                if cluster['memory_count'] >= 3 and cluster['strength'] == 'high':
                    # Consolidate highly related memories
                    consolidated = await self._consolidate_memory_cluster(cluster)
                    if consolidated:
                        optimized_clusters += 1
                        memories_consolidated += cluster['memory_count']
            
            # Get final statistics
            final_stats = self.memory_service.get_memory_statistics()
            
            return {
                "optimization_completed": True,
                "clusters_optimized": optimized_clusters,
                "memories_consolidated": memories_consolidated,
                "initial_memory_count": initial_stats.get('semantic_memory_count', 0),
                "final_memory_count": final_stats.get('semantic_memory_count', 0),
                "space_saved": max(0, initial_stats.get('semantic_memory_count', 0) - final_stats.get('semantic_memory_count', 0))
            }
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {"optimization_completed": False, "error": str(e)}
    
    async def _consolidate_memory_cluster(self, cluster: Dict[str, Any]) -> bool:
        """Consolidate a cluster of related memories into a single comprehensive memory"""
        try:
            # Extract texts from cluster memories
            memory_texts = [mem['text'] for mem in cluster['memories']]
            combined_text = "\n\n".join(memory_texts)
            
            # Generate consolidated summary
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=600,
                messages=[{
                    "role": "user",
                    "content": f"""Consolidate these related memories into a single, comprehensive summary that preserves all important information:

Theme: {cluster['theme']}
Description: {cluster['description']}

Related Memories:
{combined_text}

Create a consolidated memory that:
1. Preserves all key information
2. Eliminates redundancy
3. Maintains chronological context where relevant
4. Includes all important details and insights

Consolidated Memory:"""
                }]
            )
            
            consolidated_text = response.content[0].text.strip()
            
            if consolidated_text:
                # Create new consolidated memory
                consolidated_metadata = {
                    "type": "consolidated_cluster",
                    "theme": cluster['theme'],
                    "original_memory_count": cluster['memory_count'],
                    "consolidation_strength": cluster['strength'],
                    "consolidated_at": datetime.utcnow().isoformat()
                }
                
                # Add the consolidated memory
                memory_id = self.memory_service.add_memory(
                    text=consolidated_text,
                    metadata=consolidated_metadata
                )
                
                # TODO: Remove original memories (would need implementation in memory service)
                # This is commented out to avoid data loss during testing
                # self._remove_cluster_memories(cluster['memories'])
                
                logger.info(f"✅ Consolidated cluster '{cluster['theme']}' into memory {memory_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to consolidate memory cluster: {e}")
        
        return False

# Global instance management
_consolidation_services = {}

def get_memory_consolidation_service(user_id: str) -> MemoryConsolidationService:
    """Get or create memory consolidation service for user"""
    if user_id not in _consolidation_services:
        _consolidation_services[user_id] = MemoryConsolidationService(user_id)
    return _consolidation_services[user_id] 