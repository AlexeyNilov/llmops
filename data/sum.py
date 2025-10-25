from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate


# Define model
MODEL_NAME = "gemma3:270m"
llm = OllamaLLM(model=MODEL_NAME, temperature=0.2, top_k=10, top_p=0.5, keep_alive=3600)

# Define summarization prompt
prompt = PromptTemplate(
    input_variables=["text"],
    template="""You are an expert QA engineer. Summarize in one short sentence, including key details.
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
