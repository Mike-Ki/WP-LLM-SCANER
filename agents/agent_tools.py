from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from langchain_core.tools import tool
from langgraph.types import interrupt
from typing import Type
import difflib
import os
from langchain_tavily import TavilySearch
from dotenv import load_dotenv


class GetCodeFunctionInput(BaseModel):
    namespace_q: str = Field(..., description="The namespace of the file you want the code from.")
    func_name_q: str = Field(..., description="The name of the function you want the code from.")


class GetCodeFunctionTool(BaseTool):
    name: str = "get_code_snippet"
    description: str = "Returns the code of a function based on approximate namespace and function name."
    args_schema: Type[BaseModel] = GetCodeFunctionInput
    _code_interface: any = PrivateAttr()

    def __init__(self, code_interface, **kwargs):
        super().__init__(**kwargs)
        self._code_interface = code_interface

    def _run(self, namespace_q: str, func_name_q: str) -> str:
        print(f'Queried: namespace={namespace_q}, func={func_name_q}')

        best_score = 0
        best_key = None

        for (path, namespace, func_name) in self._code_interface.all_extracted_functions.keys():
            func_score = difflib.SequenceMatcher(None, func_name, func_name_q).ratio()
            ns_score = difflib.SequenceMatcher(None, namespace, namespace_q).ratio()
            combined_score = (func_score + ns_score) / 2

            if combined_score > best_score:
                best_score = combined_score
                best_key = (path, namespace, func_name)

        if best_key:
            output = self._code_interface.all_extracted_functions[best_key]["code"]
            print(f'Got {best_key}')
        else:
            output = f"No code found for namespace '{namespace_q}' and func_name '{func_name_q}'."

        return output

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented")


class GetCodeFunctionSGInput(BaseModel):
    path_q: str = Field(..., description="The path of the file you want the code from.")
    start_line_q: int = Field(..., description="The start line of the code you want")
    end_line_q: int = Field(..., description="The end line of the code you want")
    content_q: str = Field(..., description="One code snippet that should be found in the function")


class GetCodeFunctionSG(BaseTool):
    name: str = "get_code_snippet"
    description: str = "Returns the code of the function that best matches the given file path and specified start and end lines."
    args_schema: Type[BaseModel] = GetCodeFunctionSGInput
    _code_interface: any = PrivateAttr()

    def __init__(self, code_interface, **kwargs):
        super().__init__(**kwargs)
        self._code_interface = code_interface

    def _run(self, path_q: str, start_line_q: int, end_line_q, content_q: str) -> str:
        content_q = content_q.encode().decode('unicode_escape')
        path_q = os.path.abspath(os.path.join(self._code_interface.plugin_directory, path_q))

        print(f'Queried: path={path_q}, start_line={start_line_q}, end_line={end_line_q}, content={content_q}')

        candidates = {}
        for key, func_data in self._code_interface.all_extracted_functions.items():
            code = func_data["code"]
            if content_q in code:
                candidates[key] = func_data

        best_score = float('inf')
        best_key = None

        for key, func_data in candidates.items():
            path = os.path.abspath(key[0])
            start = func_data["start"]
            end = func_data["end"]

            start_dist = abs(start - start_line_q)
            end_dist = abs(end - end_line_q)
            total_dist = start_dist + end_dist

            path_score = difflib.SequenceMatcher(None, os.path.abspath(path), os.path.abspath(path_q)).ratio()
            #the smaller, the better
            final_score = total_dist - (10000 * path_score)

            if final_score < best_score:
                best_score = final_score
                best_key = key

        if best_key is not None:
            output = self._code_interface.all_extracted_functions[best_key]["code"]
            print(f'Got {best_key}')
        else:
            output = f"No function found for path '{path_q}' and lines {start_line_q}-{end_line_q}."
        return output

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented")


@tool
def human_assistance(query: str) -> str:
    """If you require additional information about specific source code, need confirmation if something seems suspicious, or seek guidance on how to proceed, you may request assistance from a human expert."""
    #question = interrupt({"query": query})
    print('-'*32)
    print(f'LLM asks human:\n{query}')
    response = input()
    return response


load_dotenv()
tavily_search = TavilySearch(max_results=2)
