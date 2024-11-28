from db.services.file_service import FileService


class ParserManager:
    parser_map = {}

    @staticmethod
    def registaer_parser(parser_name, parser):
       ParserManager.parser_map[parser_name] = parser

    @staticmethod
    def parse(doc_id):
        doc_info = FileService.get_file_by_id(doc_id)
        if doc_info is None:
            raise ValueError(f'No file found with doc_id {doc_id}')
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
            chunk["classification"] = doc_info.classification
            chunk["affect_range"] = doc_info.affect_range
            final_chunks.append(chunk)
        return final_chunks

    