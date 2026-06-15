
import asyncio

from retrieval.retrieval import answer_user_question
from scripts.models import openai_model
from scripts.config import settings



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
    chat_ids = [item['ChatItemID'] for item in chat_items]

    if len(chat_ids) < 5:
        return

    summarised_chat = await openai_model.summarise_chat_history(chat_items)

    result = await append_summary(user_id,chat_id,summarised_chat)

    if not result:
        raise ValueError(f'ChatID does not match up with UserID\n')

    await convert_cached(chat_ids)

    return
