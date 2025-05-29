import os
import pdb
import time

import wp_plugin_loader
from langgraph.graph import StateGraph, START
from langchain_core.messages import HumanMessage
from logging_config import setup_logging

from langgraph.graph import MessagesState, END

from static_analysis_tools.psalm.psalm_api import PsalmAPI
from static_analysis_tools.semgrep.semgrep_api import SemgrepAPI

import dotenv
import ipdb
from agents import openaiPricing
from agents.auditor import AuditorAgent
from agents.exploiter import ExploiterAgent
from agents.code_interface import CodeInterface
from agents.agent_tools import GetCodeFunctionSG, human_assistance, tavily_search


def scale(vals: list[float], eps: float = 0.05) -> dict[float, float]:
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {v: eps for v in vals}
    span = hi - lo
    return {v: eps + (v - lo) * (1 - eps) / span for v in vals}


def main():
    setup_logging()
    dotenv.load_dotenv()

    wp_plugin_loader.download_plugins(amount_of_plugins=4)
    plugin_directories = wp_plugin_loader.get_plugin_directories()

    for plugin_directory in plugin_directories[1:2]:
        findings = {}
        print('-' * 132)
        print(f'Analyze `{os.path.basename(plugin_directory)}`')

        code_interface = CodeInterface(plugin_directory)

        semgrep = SemgrepAPI(plugin_directory)

        for j, tool_prompt in enumerate(semgrep.run()):
            print(f'Analyzing finding {j}')

            # Init Agents
            sorted_models = list(reversed(openaiPricing.sorted_model_prices()))[:4]

            auditor_agents = {}

            for i, (model_name, model_price) in enumerate(sorted_models):
                if i + 1 < len(sorted_models):
                    next_model_name, _ = sorted_models[i + 1]
                else:
                    next_model_name = None

                auditor_agents[model_name] = AuditorAgent(model_name,
                                             tool_prompt=tool_prompt,
                                             tools=[GetCodeFunctionSG(code_interface), tavily_search, human_assistance],
                                             next_model=next_model_name)

            # Create graph
            workflow = StateGraph(MessagesState)
            for i, (name, auditor_agent) in enumerate(auditor_agents.items()):
                # Add nodes and edges
                workflow.add_node(f"auditor_agent_{name}", auditor_agent.node)
                if i == 0:
                    workflow.add_edge(START, f"auditor_agent_{name}")

                if i == len(auditor_agents) - 1:
                    workflow.add_conditional_edges(f"auditor_agent_{name}", auditor_agent.next_node,
                                                   {f"auditor_agent_{name}": f"auditor_agent_{name}",
                                                    END: END})
                else:
                    workflow.add_conditional_edges(f"auditor_agent_{name}",  auditor_agent.next_node,
                                                   {f"auditor_agent_{name}": f"auditor_agent_{name}",
                                                   f"auditor_agent_{auditor_agent.next_model}": f"auditor_agent_{auditor_agent.next_model}"
                                                    })

            graph = workflow.compile()

            image = graph.get_graph().draw_mermaid_png(max_retries=5, retry_delay=2.0)
            with open('graph.png', 'wb') as f:
                f.write(image)

            for message_chunk, metadata in graph.stream({"messages": [HumanMessage(content=tool_prompt)]}, stream_mode="messages"):
                if message_chunk.content:
                    print(message_chunk.content, end='', flush=True)

            current_finding_scores = {}
            scaled_price_lookup = scale([auditor_agent.price for auditor_agent in auditor_agents.values()])
            scaled_exploitability_lookup = scale([auditor_agent.exploitable for auditor_agent in auditor_agents.values()])
            scaled_certainty_lookup = scale([auditor_agent.certainty for auditor_agent in auditor_agents.values()])

            for auditor_agent in auditor_agents.values():
                current_finding_scores[auditor_agent.name] = {'score': scaled_exploitability_lookup[auditor_agent.exploitable] * scaled_certainty_lookup[auditor_agent.certainty] * scaled_price_lookup[auditor_agent.price], 'auditor_agent': auditor_agent}
            findings[j] = {'score': sum([entry['score'] for entry in current_finding_scores.values()]), 'agents': current_finding_scores}
        #print(current_finding_scores)
        pairs = ((key, data['score']) for key, data in findings.items())
        sorted_list = sorted(pairs, key=lambda x: x[1], reverse=True)
        ipdb.set_trace()
        print(findings)
        # elementor {0: {'score': 0.0026250000000000006}, 1: {'score': 0.0026250000000000006}, 2: {'score': 0.0525}, 3: {'score': 0.0026250000000000006}}
        # {0: {'score': 0.0026250000000000006}, 1: {'score': 0.050124999999999996}, 2: {'score': 0.0026250000000000006}, 3: {'score': 0.0026250000000000006}, 4: {'score': 0.0026250000000000006}, 5: {'score': 0.0026250000000000006}, 6: {'score': 0.0026250000000000006}, 7: {'score': 0.0026250000000000006}, 8: {'score': 0.0026250000000000006}, 9: {'score': 0.0026250000000000006}, 10: {'score': 0.0026250000000000006}, 11: {'score': 0.0026250000000000006}, 12: {'score': 0.0026250000000000006}, 13: {'score': 0.0026250000000000006}, 14: {'score': 0.0026250000000000006}, 15: {'score': 0.0026250000000000006}, 16: {'score': 0.0026250000000000006}, 17: {'score': 0.0026250000000000006}, 18: {'score': 0.052500000000000005}, 19: {'score': 0.050124999999999996}, 20: {'score': 0.0026250000000000006}, 21: {'score': 0.0026250000000000006}, 22: {'score': 0.0026250000000000006}, 23: {'score': 0.0026250000000000006}, 24: {'score': 0.050124999999999996}, 25: {'score': 0.0026250000000000006}, 26: {'score': 0.052500000000000005}}
if __name__ == "__main__":
    main()
#$8.25
