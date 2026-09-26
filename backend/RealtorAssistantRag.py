# RealtorAssistantRag.py: builds (or loads) a per-property FAISS index and a RetrievalQA chain
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from decouple import config
import os

def load_qa_chain_for_property(property_id: int) -> RetrievalQA:
    base_dir = os.getenv("PROPERTIES_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "properties")))
    property_folder = os.path.join(base_dir, f"Property{property_id}", "RealtorChat")
    index_path = os.path.join(base_dir, f"Property{property_id}", "faiss_index")

    text_loader_kwargs = {'encoding': 'utf-8'}
    openai_api_key = config("OPEN_AI_KEY")
    if not openai_api_key:
        raise ValueError("[FATAL] OPEN_AI_KEY not loaded from .env")

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    if not os.path.exists(index_path):
        loader = DirectoryLoader(property_folder, glob="*.txt", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs)
        documents = loader.load()
        db = FAISS.from_documents(documents, embeddings)
        db.save_local(index_path)
    else:
        db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    retriever = db.as_retriever(search_kwargs={"k": 2})
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-4",
        openai_api_key=openai_api_key,
        max_tokens=300,
        streaming=False
    )

    prompt_template = PromptTemplate.from_template("""
    You are a helpful real estate assistant. Answer user questions based only on the provided context. 
    Keep your response brief, conversational, and easy to understand. Limit your response to 3-4 sentences.

    Context:
    {context}

    Question: {question}
    Answer:
    """)

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_template}
    )
