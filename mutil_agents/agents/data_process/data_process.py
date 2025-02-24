import copy
import logging
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.data_state import DataState
from utils.common_util import parallelize_processing
from utils.parser.parser_manager import ParserManager


class DataProcess:
    def check_parse(self, data_state:DataState):
        status = data_state.get("status", None)
        if status != None and status == False:
            return "stop"
        return "continue"
    
    def parse_file(self, data_state:DataState):
        file_path = data_state["file_path"]
        try:
            chunks = ParserManager.parse_by_path(file_path)
        except Exception as e:
            print(f"Error: {e}")
            data_state["status"] = False
            return data_state
        windowed_chunks = []
        for i in range(len(chunks) - 1):
            windowed_chunks.append([chunks[i], chunks[i + 1]])
        windowed_chunks.append([chunks[-1], {"text": ""}])
        data_state["origin_chunks"] = windowed_chunks
        return data_state
    
    @parallelize_processing(field_to_iterate='origin_chunks', result_field='cleaned_chunks', max_workers=2)
    def chunk_clean(self, data_state:DataState, chunk_group):
        data = {
            "text1": chunk_group[0].get("text", ""),
            "text2": chunk_group[1].get("text", "")
        }
        ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/data_process/data_content_clean_prompt.j2", data)
        if ans == None or ans["response"] == None:
            return None
        cleaned_text = ans["response"]["content"]
        chunk_group[0]["text"] = cleaned_text
        return chunk_group[0]

    
    @parallelize_processing(field_to_iterate='cleaned_chunks', result_field='split_chunks')
    def content_split(self, data_state:DataState, chunk):
        ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/data_process/data_content_split_prompt.j2", chunk)
        if ans == None or ans["response"] == None:  
            return None
        splited_texts = ans["response"]["split_content"]
        if type(splited_texts) != list:
            splited_texts = [splited_texts]
        return_chunks = []
        for text in splited_texts:
            cur_chunk = copy.deepcopy(chunk)
            cur_chunk["text"] = text
            return_chunks.append(cur_chunk)
        return return_chunks
    
    @parallelize_processing(field_to_iterate='split_chunks', result_field='final_chunks')
    def content_question_add(self, data_state:DataState, chunks):
        for chunk in chunks:
            ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/data_process/data_content_question_add_prompt.j2", chunk)
            if ans == None or ans["response"] == None:
                logging.error("content_question_add: No response from LLM")
                return None
            questions = ans["response"]["question"]
            if type(questions) != list:
                questions = [questions]
            chunk["questions"] = questions
        return chunks

            

    