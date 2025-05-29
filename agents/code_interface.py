from tree_sitter import Language, Parser
import tree_sitter_php as tsphp
import os
import logging


class CodeInterface():

    logger = logging.getLogger(__name__)

    def __init__(self, plugin_directory):
        self.php_language = Language(tsphp.language_php())
        self.parser = Parser(self.php_language)
        self.plugin_directory = plugin_directory
        self.all_extracted_functions = self.get_all_functions(plugin_directory)


    def get_php_files(self, base_path):
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith(".php"):
                    yield os.path.join(root, file)


    def parse_php_file(self, path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        tree = self.parser.parse(content.encode())
        return content, tree


    def extract_functions(self, tree, code, path):
        root = tree.root_node
        code_bytes = code.encode()
        functions = {}

        namespace = ""

        def find_namespace(node):
            if node.type == "namespace_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    return code_bytes[name_node.start_byte:name_node.end_byte].decode()
            for child in node.children:
                ns = find_namespace(child)
                if ns:
                    return ns
            return ""

        namespace = find_namespace(root)

        def recurse(node):
            if node.type in ("function_definition", "method_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = code_bytes[name_node.start_byte:name_node.end_byte].decode()
                    body = code_bytes[node.start_byte:node.end_byte].decode()
                    functions[(path, namespace, name)] = {
                        "start": node.start_point[0] + 1,
                        "end": node.end_point[0] + 1,
                        "code": body,
                        "node": node}
            for child in node.children:
                recurse(child)

        recurse(root)
        return functions

    def get_all_functions(self, plugin_dir):
        all_functions = {}

        for path in self.get_php_files(plugin_dir):
            content, tree = self.parse_php_file(path)
            functions = self.extract_functions(tree, content, path)
            all_functions.update(functions)

        return all_functions
