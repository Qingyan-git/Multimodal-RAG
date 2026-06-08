
import asyncio

from retrieval.retrieval import answer_user_question
from scripts.models import openai_model
from scripts.config import settings


async def contextualise_query(question,chat_history):

    context_string = ""

    for i, item in enumerate(chat_history):
        context_string += f'Chat History Item Number : {i}\n'
        context_string += f'Question asked by user : {item['Question']}\n'
        context_string += f'Response given by LLM : {item['Response']}\n'

    context_string += f'Current query : {question}\n'

    rewritten_query = await openai_model.rewrite_query(context_string)

    return rewritten_query


async def answer_question_contextual(user_id,question):
    
    intent = await openai_model.classify_query(question)

    if intent == 'chitchat':
        response = await openai_model.respond_to_chitchat(question)
        
        return response

    else:
        chat_history = get_chats(user_id)
        contextualised_question = await contextualise_query(query,chat_history)
        answer = await answer_user_question(contextualise_question)

        return answer



