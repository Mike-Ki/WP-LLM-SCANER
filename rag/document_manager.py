import os
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter


class DocumentManager:


    def __init__(self, directory_path, glob_pattern="./*.md"):
        current_file = os.path.dirname(os.path.abspath(__file__))
        self.directory_path = os.path.join(current_file, directory_path)
        self.glob_pattern = glob_pattern
        self.documents = []
        self.all_sections = []


    def load_documents(self):
        loader = DirectoryLoader(self.directory_path, glob=self.glob_pattern, show_progress=True, loader_cls=TextLoader)
        self.documents = loader.load()


    def split_documents(self):
        headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3"), ("####", "Header 4")]
        text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers = False)
        for doc in self.documents:
            sections = text_splitter.split_text(doc.page_content)
            self.all_sections.extend(sections)
