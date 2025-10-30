from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import requests
import json


# Define model
MODEL_NAME = "gemma3:270m"
llm = OllamaLLM(model=MODEL_NAME, temperature=0.2, top_k=10, top_p=0.5, keep_alive=-1)

# Define summarization prompt
prompt = PromptTemplate(
    input_variables=["text"],
    template="""Summarize in one short sentence, including key details (error, exception).
===
{text}
""",
)

# Create the summarization chain
summarize_chain = prompt | llm


def summarize_text(text: str) -> str:
    # Use .invoke() for a single input/output, which is the standard LCEL method
    # Pass input as a dictionary matching the prompt's input_variables
    result = summarize_chain.invoke({"text": text})
    return result.strip()


def fast_summarize(text: str, model=MODEL_NAME):
    payload = {
        "model": model,
        "prompt": f"Summarize in one short sentence, including key details (error, exception).\n===\n{text}",
        "options": {"temperature": 0.2, "top_k": 10, "top_p": 0.5},
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload)
    summary = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            if "response" in data:
                summary += data["response"]
    return summary.strip()
