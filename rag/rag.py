from .document_manager import DocumentManager
from .embedding_manager import EmbeddingManager
from dotenv import load_dotenv

class RAG:

    def __init__(self, markdown_dir="./marckdown_folder", glob_pattern="./*.md"):
        load_dotenv()
        self.markdown_dir = markdown_dir
        self.glob_pattern = glob_pattern
        self.doc_manager = self.load_documents()
        self.embed_manager = self.create_and_load_embeddings()


    def load_documents(self):
        self.doc_manager = DocumentManager(self.markdown_dir, glob_pattern=self.glob_pattern)
        self.doc_manager.load_documents()
        self.doc_manager.split_documents()
        return self.doc_manager


    def create_and_load_embeddings(self):
        if not self.doc_manager:
            raise ValueError("Documents not loaded yet.")
        self.embed_manager = EmbeddingManager(self.doc_manager.all_sections)
        self.embed_manager.create_and_persist_embeddings()
        return self.embed_manager


    def query(self, query):
        return self.embed_manager.query(query, k=3)

rag = RAG()

if __name__ == "__main__":
    rag.query('SSRF')
    rag.query('Code Injection')