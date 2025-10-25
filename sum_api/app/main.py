from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate


app = FastAPI(title="Gemma 3 API", version="0.1.1")

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


class PromptRequest(BaseModel):
    text: str


@app.post("/summarize")
def summarize_text(request: PromptRequest) -> str:
    try:
        result = summarize_chain.invoke({"text": request.text})
        return {"response": result.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
