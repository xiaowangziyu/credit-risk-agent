import os
from typing import List, Dict, Any, Optional
from config.settings import settings


class KnowledgeBaseReader:
    def __init__(self):
        self.base_dir = settings.KNOWLEDGE_BASE_DIR

    def list_documents(self) -> List[str]:
        docs = []
        if os.path.exists(self.base_dir):
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.md'):
                    docs.append(filename)
        return docs

    def read_document(self, filename: str) -> Optional[str]:
        filepath = os.path.join(self.base_dir, filename)
        if os.path.exists(filepath) and filename.endswith('.md'):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def read_all(self) -> Dict[str, str]:
        documents = {}
        for doc_name in self.list_documents():
            content = self.read_document(doc_name)
            if content:
                documents[doc_name] = content
        return documents

    def read_rules(self) -> Optional[str]:
        return self.read_document('rules.md')

    def read_scorecard_guide(self) -> Optional[str]:
        return self.read_document('scorecard.md')

    def read_credit_guide(self) -> Optional[str]:
        return self.read_document('credit.md')

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        results = []
        all_docs = self.read_all()
        for doc_name, content in all_docs.items():
            if keyword.lower() in content.lower():
                lines = content.split('\n')
                relevant_lines = []
                for i, line in enumerate(lines):
                    if keyword.lower() in line.lower():
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        relevant_lines.extend(lines[start:end])
                results.append({
                    "document": doc_name,
                    "relevant_content": '\n'.join(relevant_lines[:10])
                })
        return results


knowledge_base_reader = KnowledgeBaseReader()
