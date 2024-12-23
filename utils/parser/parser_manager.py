
import os
import time
from db.services.file_service import FileService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from utils.file_util import ensure_dir_exists, rewrite_json_file

CHUNK_BASE_PATH = "data/parser/"

class ParserManager:
    parser_map = {}

    @staticmethod
    def register_parser(parser_name, parser):
       ParserManager.parser_map[parser_name] = parser

    @staticmethod
    def parse(doc_id):
        doc_info = FileService().get_file_by_id(doc_id)
        if doc_info is None:
            raise ValueError(f'No file found with doc_id {doc_id}')
        if doc_info.is_chunked == 1:
            raise ValueError(f'File with doc_id {doc_id} has already been chunked')
        file_path = doc_info.file_path
        file_type = doc_info.file_type
        parser = ParserManager.parser_map.get(file_type)
        if parser is None:
            raise ValueError(f'No parser found for file type {file_type}')
        chunks = parser(file_path)
        final_chunks = []
        for chunk in chunks:
            chunk = chunk
            chunk["doc_id"] = doc_info.doc_id
            chunk["id"] = int(time.time())
            chunk["classification"] = doc_info.classification
            chunk["affect_range"] = doc_info.affect_range
            ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/data_format_prompt.j2", chunk)
            if ans is not None:
                chunk["text"] = ans["response"]["text"]
                chunk["summary"] = ans["response"]["summary"]
                chunk["keywords"] = ans["response"]["keyword"]
                chunk["query"] = ans["response"]["query"]
            final_chunks.append(chunk)
        file_name = doc_info.file_name + '.json'

        dir_path=os.path.join(CHUNK_BASE_PATH, doc_info.file_type, doc_info.classification, "chunks")
        ensure_dir_exists(dir_path)
        rewrite_json_file(filepath=os.path.join(dir_path, file_name), json_data=final_chunks)
        return final_chunks

    