import re
import docker
from docker.types import Mount
from typing import Dict, Tuple, List, Iterator
import os
import hashlib
import logging

from static_analysis_tools.StaticAnalysisToolBase import StaticAnalysisToolBase


class PsalmAPI(StaticAnalysisToolBase):

    logger = logging.getLogger(__name__)

    def __init__(self, directory):
        super().__init__(directory)

        self.cache_file = os.path.join(self.cache_dir, f'psalm.{self.hash}.txt')


    def run(self) -> Iterator[str]:
        if os.path.exists(self.cache_file):
            print("Already done, skipping container run.")
            with open(self.cache_file, "r") as f:
                output = f.read()
        else:
            output = self._run_psalm()
        analysis = self._analyze_plugin(output)

        for tainted_flow in analysis:
            if not tainted_flow:
                self.logger.info(f"No vulnerabilities found in plugin {self.directory}. Exiting.")
                return
            yield f"""You are analyzing the output from Psalm, a PHP taint analysis tool, which has been run on a WordPress plugin named {os.path.basename(self.directory)}.
Psalm has reported a potential issue classified as `{tainted_flow['error']}`.
Source (taint origin):            
```
{tainted_flow['source']}
```

Sink (vulnerable endpoint):
```
{tainted_flow['sink']}
```

Here is the Psalm output for this issue:
```
{tainted_flow['flow']}
```
"""


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


    @staticmethod
    def _structure_report(taint_analysis: str) -> Tuple[str, str, str, List[str]]:
        error = taint_analysis.split('\nat')[0].strip('\nERROR: ').split()[0]
        funcs = taint_analysis.split('\n\n\n\n')[0].split('\n\n  ')[1:]

        source = funcs[0]
        sink = funcs[-1]
        return error, source, sink, funcs


    def _run_psalm(self) -> str | None:
        command = f'/composer/vendor/bin/psalm --taint-analysis --monochrome --no-cache --config=/app/{os.path.basename(self.cache_dir)}/psalm.xml --threads=1'
        self.logger.info(f"Running PSALM on `{self.directory}`: `{command}`")
        client = docker.from_env()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        psalm_path = f"{current_dir}/psalm.xml"
        container = client.containers.run(image='ghcr.io/danog/psalm:latest',
                                          command=command,
                                          stdout=True,
                                          stderr=True,
                                          stream=True,
                                          mounts = [
                                              Mount(
                                                target="/app",
                                                source= os.path.abspath(self.directory),
                                                type="bind",
                                                read_only=False
                                            ),
                                              Mount(
                                                  target=f"/app/{os.path.basename(self.cache_dir)}/psalm.xml",
                                                  source=psalm_path,
                                                  type="bind",
                                                  read_only=True
                                              )
                                          ],
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
                f.write("".join(stdout_lines))
            return "\n".join(stdout_lines)
        else:
            self.logger.error("Error")
            self.logger.error(stderr_lines)
            return None


    def _analyze_plugin(self, output) -> List[Dict]:
        analysis_results = []
        if not output:
            self.logger.error(f"No PSALM output for {self.directory}")
            return []

        tainted_flows = output.split('\n\n\n')[:-1]
        self.logger.info(f"Discovered {len(tainted_flows)} tainted flows")

        for flow_id, taint_flow in enumerate(tainted_flows):
            try:
                error, source, sink, funcs = self._structure_report(output)
                extended_code_snippets = self._extract_code_snippets(funcs[1:-1])

                analysis_results.append(
                    {'error': error, 'source': source, 'sink': sink, 'flow': taint_flow, 'output': output, 'funcs': funcs,
                     'extended_code_snippets': extended_code_snippets})
            except Exception as e:
                print(f"Error processing flow {flow_id}: {e}")

        return analysis_results
