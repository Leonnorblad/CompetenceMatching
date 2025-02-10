import os
import sys
from tqdm import tqdm
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from uuid import uuid4
from langchain_core.documents import Document
import hashlib


from scr.vdb.tags import *
from scr.utils import load_from_file, YYYYMMDD_to_unix

class VDB:
    def __init__(self, collection_name="documents"):
        local_embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.collection_name = collection_name
        self.db = Chroma(
            collection_name=collection_name,
            embedding_function=local_embeddings,
            collection_metadata={"hnsw:space": "cosine"},
            persist_directory="./user_data/vdbs")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""],
        )

        # Check if a database registry exists - if not, create one
        metadata_path = f"./user_data/vdbs/{collection_name}.json"
        if not os.path.exists(metadata_path):
            with open(metadata_path, "w") as f:
                json.dump([], f)
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)
    
    def add_docs(self, folder_path: str):
        self.txt_path = folder_path
        # Iterate through all files in the folder
        for file_name in tqdm(os.listdir(folder_path)):
            # Create the full file path
            file_path = os.path.join(folder_path, file_name)
            # Check if the file is a text file
            if file_name.endswith(".txt"):
                # Load the document using TextLoader
                doc = load_from_file(file_path)
                # Check if file is in database
                doc_hash = hashlib.md5(doc.encode()).hexdigest()
                if doc_hash not in self.metadata:
                    # Add the document to the database
                    self.add_doc(doc, file_path)
                    # Add the document hash to the metadata
                    self.metadata.append(doc_hash)
        
    def add_doc(self, doc: str, source: str):
        # Extract tags from the full document
        tags = extract_tags(doc)
        tags["source"] = source
        tags = convert_tags(tags)
        
        # Split the document into chunks
        chunks = self.text_splitter.split_text(doc)
        
        # Create Document objects with metadata
        documents = [
            Document(page_content=chunk, metadata=tags)
            for chunk in chunks
        ]
        
        # Generate unique IDs for each document
        uuids = [str(uuid4()) for _ in range(len(documents))]
        
        # Add documents to the Chroma database
        self.db.add_documents(documents=documents, ids=uuids)
    
    def write_metadata(self):
        metadata_path = f"./user_data/vdbs/{self.collection_name}.json"
        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f)
    
    def search(self, query, filters_from_llm=None, num_results=5):
        result = self.db.similarity_search_with_score(
            query,
            k=num_results,
            filter=filters_from_llm
        )
        return result
    
    def get_size(self):
        print(f"Database has: {len(self.db.get()['ids'])} chunks.")