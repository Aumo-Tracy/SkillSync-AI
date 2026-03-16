"""
LangChain Agent - Simple Working Version
Uses OpenAI Functions agent instead of React agent
"""
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, Tool
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.schema import SystemMessage
from langchain.memory import ConversationBufferMemory
from app.config import settings
from app.core.logging import get_logger, usage_logger
from app.core.errors import OpenAIException
from app.services.rag.retriever import get_rag_retriever
from app.services.tools import ALL_TOOLS
from app.services.langchain.prompts import SYSTEM_PROMPT
from app.models.schemas import ChatResponse, TokenUsage, ToolCall

logger = get_logger(__name__)


class SupportAgent:
    """E-commerce customer support AI agent"""
    
    def __init__(self):
        """Initialize the agent with LLM, tools, and RAG"""
        logger.info("Initializing SupportAgent...")
        
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.retriever = get_rag_retriever()
        self.tools = ALL_TOOLS
        self.memories: Dict[str, ConversationBufferMemory] = {}
        
        logger.info(f"Agent initialized with {len(self.tools)} tools")
    
    def _get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for a session"""
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )
            logger.info(f"Created new memory for session: {session_id}")
        return self.memories[session_id]
    
    def _should_use_rag(self, message: str) -> bool:
        """Determine if query should use RAG retrieval"""
        rag_keywords = [
            'policy', 'return', 'refund', 'shipping', 'delivery',
            'how', 'what', 'when', 'where', 'why', 'can i', 'do you',
            'long does', 'much does', 'cost', 'time', 'days'
        ]
        
        message_lower = message.lower()
        data_lookup_keywords = ['order', 'track', 'discount', 'code', 'product']
        
        if any(keyword in message_lower for keyword in data_lookup_keywords):
            if not any(keyword in message_lower for keyword in ['how', 'what', 'policy', 'can i']):
                return False
        
        return any(keyword in message_lower for keyword in rag_keywords)
    
    async def chat(
        self,
        message: str,
        session_id: str,
        user_email: Optional[str] = None,
        include_sources: bool = True
    ) -> ChatResponse:
        """Process a chat message"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing message", extra={"session_id": session_id})
            
            memory = self._get_or_create_memory(session_id)
            use_rag = self._should_use_rag(message)
            
            # Retrieve context if needed
            context_text = ""
            sources = []
            
            if use_rag:
                logger.info("Using RAG retrieval for context")
                try:
                    context_text, sources = self.retriever.smart_retrieve(message)
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")
                    context_text = ""
                    sources = []
            
            # Build system message with context
            system_content = SYSTEM_PROMPT
            if context_text:
                system_content += f"\n\nRELEVANT CONTEXT FROM KNOWLEDGE BASE:\n{context_text}"
            if user_email:
                system_content += f"\n\nUser email: {user_email}"
            
            system_message = SystemMessage(content=system_content)
            
            # Create OpenAI Functions agent (simpler, more reliable)
            agent = OpenAIFunctionsAgent.from_llm_and_tools(
                llm=self.llm,
                tools=self.tools,
                system_message=system_message
            )
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                return_intermediate_steps=True
            )
            
            # Execute agent
            result = await agent_executor.ainvoke({"input": message})
            
            response_text = result.get("output", "I apologize, but I'm having trouble processing your request.")
            
            # Extract tool calls
            tool_calls = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2:
                        action, observation = step[0], step[1]
                        tool_calls.append(ToolCall(
                            tool_name=action.tool,
                            arguments=action.tool_input if hasattr(action, 'tool_input') else {},
                            result=str(observation),
                            execution_time_ms=0,
                            success=True
                        ))
            
            # Calculate metrics
            response_time_ms = (time.time() - start_time) * 1000
            prompt_tokens = len(system_content + message) // 4
            completion_tokens = len(response_text) // 4
            total_tokens = prompt_tokens + completion_tokens
            
            cost = settings.calculate_cost(
                settings.OPENAI_MODEL,
                prompt_tokens,
                completion_tokens
            )
            
            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=cost,
                model=settings.OPENAI_MODEL
            )
            
            usage_logger.info(
                "Chat completed",
                extra={
                    "session_id": session_id,
                    "response_time_ms": response_time_ms,
                    "tokens": total_tokens,
                    "tools_used": len(tool_calls)
                }
            )
            
            response = ChatResponse(
                response=response_text,
                session_id=session_id,
                sources=sources if include_sources and sources else None,
                tool_calls=tool_calls if tool_calls else None,
                token_usage=token_usage,
                response_time_ms=response_time_ms
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error in chat processing: {e}", exc_info=True)
            raise OpenAIException(
                f"Failed to process message: {str(e)}",
                detail="The AI service encountered an error. Please try again."
            )
    
    def clear_session(self, session_id: str):
        """Clear conversation memory for a session"""
        if session_id in self.memories:
            del self.memories[session_id]
            logger.info(f"Cleared memory for session: {session_id}")
    
    def get_session_history(self, session_id: str) -> List:
        """Get conversation history for a session"""
        if session_id not in self.memories:
            return []
        
        memory = self.memories[session_id]
        messages = []
        
        for msg in memory.chat_memory.messages:
            from langchain.schema import HumanMessage
            messages.append({
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return messages


# Global agent instance
_agent_instance = None


def get_support_agent() -> SupportAgent:
    """Get or create support agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SupportAgent()
    return _agent_instance


__all__ = ['SupportAgent', 'get_support_agent']