from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import ZhipuAIEmbeddings
embeddings = ZhipuAIEmbeddings(api_key=API_KEY, model="embedding-2")

loader = TextLoader("哲学.txt", encoding="utf-8")
documents = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0)
docs = text_splitter.split_documents(documents)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(docs, embeddings)

import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ZHIPU_API_KEY")

def chat(prompt):
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "glm-4-flash",   # 免费模型
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API调用失败：{e}"

def answer(question):
    docs = vectorstore.similarity_search(question, k=2)
    context = "\n".join([doc.page_content for doc in docs])
    prompt = f"基于以下内容回答问题：\n{context}\n问题：{question}\n回答："
    return chat(prompt)   # 复用第一步的chat函数

if __name__ == "__main__":
    question = input("请输入您的问题：")
    response = answer(question)
    print("回答：", response)