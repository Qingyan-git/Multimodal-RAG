
import os
import io
import base64
import asyncio
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage



class OpenAIModel:

    def __init__(self):

        model = os.getenv('openai_model')
        api_key = os.getenv('openai_api_key')

        self.model = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0,
            max_tokens=4096,
            timeout=60,
            max_retries=2,
            reasoning_effort='minimal'
        )


    def get_image_description(self,pil_image):

        buffered = io.BytesIO()
        pil_image = pil_image.convert("RGB")
        pil_image.save(buffered, format="JPEG", quality=95)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{img_str}"

        messages = [
            SystemMessage(content="""You are an expert Document Layout and Visual Data Extraction engine. 
            Your single task is to convert the provided image into a dense, highly accurate textual representation optimized for vector-database indexing and semantic retrieval.

            Observe these strict extraction guardrails:
            1. DOCUMENT LAYOUT & STRATEGY: If the image is a flowchart, architecture diagram, or process map, explicitly list the nodes, relationships, directional flows, and logical dependencies ("X connects to Y via Z").
            2. DATA ISOLATION: If the image is a chart, graph, or matrix, extract every visible data point, axis label, metric scale, legend key, and observed statistical trend.
            3. SEMANTIC WEIGHT: Use rich, explicit domain-specific keywords. Do not summarize abstractly if you can describe concretely. Avoid vague descriptions like "a beautiful chart". Instead use "Bar chart illustrating 2026 projected fiscal growth metrics".
            4. OUTPUT FORMAT: Start directly with the factual analysis. Do not include introductory phrases like "Sure, here is the description" or conversational sign-offs. Write in clean, structural paragraph blocks or technical markdown lists."""
            ),
            HumanMessage(
                content=[
                    {
                        "type": "text", 
                        "text": "Analyze this extracted image layout element and output its semantic text equivalent for database serialization."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url}
                    }
                ]
            )
        ]

        response = self.model.invoke(messages)
        content = response.content

        return content

