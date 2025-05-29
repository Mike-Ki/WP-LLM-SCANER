from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
import re
from langgraph.graph import MessagesState, END
from .openaiPricing import get_model_estimated_price
from langchain_openai import ChatOpenAI

class AuditorAgent:

    system_prompt = '''
You are a security expert specializing in PHP code analysis, particularly focused on WordPress plugins. You will receive outputs from static analysis tools—each containing exactly one identified issue related to potential vulnerabilities.
Your task:
Carefully evaluate the reported issue to determine:
If it represents a genuine, exploitable security vulnerability or if it is a false positive.
Use the available helper tools as needed:
- Inspect source code of relevant functions to verify proper sanitization or validation.
- Perform web searches for additional context or clarification.
- Request human assistance if uncertain or stuck (invoke human_assistance).

Evaluation criteria:
- Clearly explain your reasoning and provide detailed analysis.
- Consider the presence or absence of proper validation, sanitization, escaping, or authorization checks.

Output format:
When your analysis is complete, explicitly conclude your response with the following structured format:

FINAL ANSWER: `<Number between 0 and 1>`
CERTAINTY: `<Number between 0 and 1>`

Guidelines for structured output:
- FINAL ANSWER close to 1 indicates a high likelihood of an exploitable vulnerability.
- FINAL ANSWER close to 0 indicates a likely false positive.
- CERTAINTY should reflect how confident you are in your determination (with 1 being absolutely certain and 0 representing complete uncertainty).
Important:
Only use "FINAL ANSWER" when your evaluation is fully complete and definitive.
If more work is needed, spawn a sub-task by prompting yourself:
TASK: <Describe the next analysis step”>
 '''

    def __init__(self, model_name, tool_prompt, tools, next_model=None):
        self.name = model_name
        self.model = ChatOpenAI(model=model_name)
        self.next_model = next_model
        self.tools = tools
        self.tool_prompt = tool_prompt
        self.auditor_agent = create_react_agent(model=self.model, tools=self.tools, prompt=self.system_prompt)
        self.price = get_model_estimated_price(self.name)
        self.message = []
        self.exploitable = 0.0
        self.certainty = 0.0

    @staticmethod
    def extract_final_answer(text: str, name: str):
        escaped = re.escape(name)
        pattern = rf'{escaped}:\s*([-+]?(?:\d*\.\d+|\d+))'
        text = text.replace('*', '')
        text = text.replace('\'', '')
        text = text.replace('`', '')

        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
        else:
            import pdb; pdb.set_trace()
        return None


    def node(self, state: MessagesState):
        print(f'\nCalling Agent: {self.name}')
        result = self.auditor_agent.invoke(state)
        last_message = result["messages"][-1].content
        self.message.append(last_message)
        if 'FINAL ANSWER:' in last_message.upper():
            self.exploitable = self.extract_final_answer(last_message.upper(), 'FINAL ANSWER')
            self.certainty = self.extract_final_answer(last_message.upper(), 'CERTAINTY')
            print(f'\nExtracted: FINAL ANSWER: {self.exploitable}')
            print(f'Extracted: CERTAINTY: {self.certainty}\n')
        return Command(update={"messages": result["messages"]})


    def next_node(self, state: MessagesState):
        last_message = state["messages"][-1].content
        if "FINAL ANSWER" in last_message:
            if self.next_model is None:
                goto = END
            else:
                goto = f"auditor_agent_{self.next_model}"
        else:
            goto = f"auditor_agent_{self.name}"
        return goto