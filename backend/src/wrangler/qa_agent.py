from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from wrangler.ragUtil import RAGUtils


class OpenAIQuestionAnswerAgent:
    def __init__(self, client: "RAGUtils", model: str = "gpt-4o-mini"):
        self._client = client
        self.model = model

    async def answer(self, question: str, persona: str = "user") -> str:
        """Answer a question using the client's data"""
        openai_client = AsyncOpenAI()
        
        context_chunks = []
        
        search_result = await self._client.search(question, 5)
        for chunk, score in search_result:
            context_chunks.append(f"Content: {chunk.content}\nScore: {score:.2f}")
        
        context = "\n\n".join(context_chunks)
        
        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=SYSTEM_PROMPT.format(context=context, persona=persona)),
            ChatCompletionUserMessageParam(role="user", content=question),
        ] 

        response = await openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )

        response_message = response.choices[0].message
        
        return response_message.content
        
        

SYSTEM_PROMPT = """
You are a helpful assistant that uses a RAG library to answer the user's prompt.
Your task is to provide a concise and accurate answer based on the provided context.
Never make up information, always use the context to answer the question.
If the context does not contain enough information to answer the question, respond with "I cannot answer that based on the provided context.

When generating take into account the persona of the user.

If the persona is "product_owner", you should answer the question by also emphasizing on the system architecture, embedding methods, performance trade-offs.
If the persona is "marketing", you should answer the question by highlighting the conversation metrics and optimization strategies.

Context:
{context}

Persona: {persona}
"""
