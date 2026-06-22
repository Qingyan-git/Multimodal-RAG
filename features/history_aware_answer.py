
import asyncio
from fastapi import HTTPException, status

from retrieval.retrieval import answer_user_question
from scripts.models import openai_model
from scripts.config import settings
from scripts.supabase import get_non_cached, append_summary, convert_cached, create_chat, create_chatitem, get_chat_history




async def contextualise_query(question, chat_summary, uncached_chats):

    summary_text = chat_summary if chat_summary else "No long-term consolidated memory available for this session."

    history_lines = []
    if uncached_chats:
        for turn in uncached_chats:
            history_lines.append(f"User: {turn['question']}\nAssistant: {turn['response']}")
        history_text = "\n\n".join(history_lines)
    else:
        history_text = "No immediate recent message turns recorded."

    formatted_prompt = f"""You are an advanced conversational AI context engine. Your task is to analyze a user's new question along with their conversation history, and rewrite the question into a clear, standalone, optimized search query for a document retrieval engine.

        --- CONVERSATIONAL MEMORY LAYERS ---

        <long_term_cached_summary>
        {summary_text}
        </long_term_cached_summary>

        <recent_uncached_history>
        From oldest to most recent :
        {history_text}
        </recent_uncached_history>

        --- CURRENT USER INPUT ---
        User's Question : {question}

        Provide only the rewritten, standalone query without any preambles, explanation text, or conversational tone."""

    rewritten_query = await openai_model.rewrite_query(formatted_prompt)

    return rewritten_query


async def summarise_chat(user_id, chat_id):

    chat_items = await get_non_cached(user_id, chat_id)
    chat_ids = [item['chatitemid'] for item in chat_items]

    if len(chat_ids) < 5:
        return

    summarised_chat = await openai_model.summarise_chat_history(chat_items)

    result = await append_summary(user_id,chat_id,summarised_chat)

    if not result:
        raise ValueError(f'ChatID does not match up with UserID\n')

    await convert_cached(chat_ids)

    return


async def process_user_question(question,chat_id,user_id):

    prompt_safety = await openai_model.check_guardrail(question)
    is_safe = prompt_safety.is_safe

    if is_safe == False:
        violation = prompt_safety.violation_category
        reasoning = prompt_safety.reasoning

        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Query rejected due to : {violation}. Reason: {reasoning}"
            )
    
    else:
        intent = await openai_model.classify_query(question)

        if chat_id == -1:
            chat_name = f'{question[:20]}...'
            chat_id = await create_chat(chat_name,user_id)

        if intent == 'chitchat':
            answer = await openai_model.respond_to_chitchat(question)
            sources = []

        else:
            chat_summary, uncached_chats = await get_chat_history(user_id, chat_id)
            rewritten_query = await contextualise_query(question, chat_summary, uncached_chats)
            answer, used_sources = await answer_user_question(rewritten_query)
            sources = [
                {
                    'pdf_name' : src['pdf_name'],
                    'page_num' : src['page_num'],
                    'image_base64' : src['image_base64']
                }
                for src in used_sources
            ]

        await create_chatitem(question,answer,user_id,chat_id)
        await summarise_chat(user_id, chat_id)

        return {
            'chat_id' : chat_id,
            'answer' : answer,
            'sources' : sources
        }
