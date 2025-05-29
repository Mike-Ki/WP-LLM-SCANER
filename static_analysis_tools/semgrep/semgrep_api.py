import re
import docker
from docker.types import Mount
from typing import Dict, Tuple, List, Iterator
import os
import json
import logging
from dotenv import load_dotenv

from static_analysis_tools.StaticAnalysisToolBase import StaticAnalysisToolBase

load_dotenv()

class SemgrepAPI(StaticAnalysisToolBase):

    logger = logging.getLogger(__name__)


    def __init__(self, directory):
        super().__init__(directory)
        self.cache_file = os.path.join(self.cache_dir, f'semgrep.{self.hash}.json')


    def run(self) -> Iterator[str]:
        if os.path.exists(self.cache_file):
            print("Already done, skipping container run.")
            with open(self.cache_file, "r") as f:
                report = json.load(f)
        else:
            report = self._run_semgrep()
        report = self._structure_report(report)

        for result in report:
            if not result:
                self.logger.info(f"No vulnerabilities found in plugin {self.directory}. Exiting.")
                return
            yield f"""You are analyzing the output from Semgrep, a PHP taint analysis tool, which has been run on a WordPress plugin named {os.path.basename(self.directory)}.
Semgrep has reported a potential issue classified as `{result['vulnerability_class']}`.
Source (taint origin):            
```
{result['taint_source']}
```

Sink (vulnerable endpoint):
```
{result['taint_sink']}
```

And here are the intermediate values:
```
{result['taint_intermediate_vars']}
```
"""


    def _run_semgrep(self) -> dict | None:
        command = f'semgrep scan --config "p/php" --json'
        self.logger.info(f"Running PSALM on `{self.directory}`: `{command}`")
        client = docker.from_env()
        container = client.containers.run(image='semgrep/semgrep:latest',
                                          command=command,
                                          stdout=True,
                                          stderr=True,
                                          stream=True,
                                          mounts = [
                                              Mount(
                                                target="/src",
                                                source= os.path.abspath(self.directory),
                                                type="bind",
                                                read_only=False
                                            )
                                          ],
                                          environment={"SEMGREP_APP_TOKEN": os.environ.get('SEMGREP_API_KEY')},
                                          remove=True,
                                          detach=True,
                                          )
        logs = container.attach(stdout=True, stderr=True, stream=True, demux=True)
        stdout_lines = []
        stderr_lines = []

        for stdout_chunk, stderr_chunk in logs:
            if stdout_chunk:
                line = stdout_chunk.decode().strip()
                stdout_lines.append(line)
                self.logger.info(f"[STDOUT] {line}")
            if stderr_chunk:
                line = stderr_chunk.decode().strip()
                stderr_lines.append(line)
                self.logger.error(f"[STDERR] {line}")

        if stdout_lines:
            with open(self.cache_file, "w+") as f:
                json.dump(json.loads("".join(stdout_lines)), f, indent=4, ensure_ascii=False)
            return json.loads("".join(stdout_lines))
        else:
            self.logger.error("Error")
            self.logger.error(stderr_lines)
            return None


    @staticmethod
    def _extract_code_snippets(funcs: List[str]) -> List[str]:
        taint_flow = []
        joined_funcs = '\n\n'.join(funcs)
        pattern = re.compile(r'([^\s]+) - ([^\s]+):(\d+):(\d+)')
        for match in pattern.finditer(joined_funcs):
            function_name, filepath, end, start = match.groups()
            start, end = int(start), int(end)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                snippet = ''.join(lines[start:end])
                taint_flow.append(snippet)
            except FileNotFoundError:
                taint_flow.append(f"File not found: {filepath}")

        return taint_flow


    def _structure_report(self, report) -> List[Dict]:
        tainted_flows = []
        if not report:
            self.logger.error(f"No Semgrep output for {self.directory}")
            return []
        for result in report['results']:
            result = result['extra']
            vulnerability_class = result['metadata']['vulnerability_class']
            if not 'dataflow_trace' in result:
                continue
            dataflow_trace = result['dataflow_trace']
            taint_source = dataflow_trace['taint_source'][1]
            taint_intermediate_vars = dataflow_trace['intermediate_vars']
            taint_sink = dataflow_trace['taint_sink'][1]

            tainted_flows.append({'vulnerability_class': vulnerability_class,
                                  'dataflow_trace': dataflow_trace,
                                  'taint_source': taint_source,
                                  'taint_intermediate_vars': taint_intermediate_vars,
                                  'taint_sink': taint_sink})

        self.logger.info(f"Discovered {len(tainted_flows)} tainted flows")
        return tainted_flows
