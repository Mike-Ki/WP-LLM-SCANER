from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
load_dotenv()

class EmbeddingManager:


    def __init__(self, all_sections, persist_directory='db'):
        self.all_sections = all_sections
        self.persist_directory = persist_directory
        self.vectordb = None


    # Method to create and persist embeddings
    def create_and_persist_embeddings(self):
        # Creating an instance of OpenAIEmbeddings
        embedding = OpenAIEmbeddings(model="text-embedding-3-small")
        # Creating an instance of Chroma with the sections and the embeddings
        self.vectordb = Chroma.from_documents(documents=self.all_sections, embedding=embedding, persist_directory=self.persist_directory)
         # Persisting the embeddings
        self.vectordb.persist()


    def query(self, query: str, k: int = 3):
        results = self.vectordb.similarity_search(query, k=k)
        for idx, doc in enumerate(results):
            print(f"Result {idx + 1}:")
            print(doc.page_content)
            print("------")
        return results