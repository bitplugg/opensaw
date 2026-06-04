import re
import threading

from opensawcore import config


class GenerationManager:
    def __init__(self, lm, memory, sem_memory=None):
        self.lm = lm
        self.memory = memory
        self.sem_memory = sem_memory

    def generate(self, text: str, *, on_done, on_error):
        def worker():
            try:
                response = self._do_generate(text)
                on_done(response)
            except Exception as e:
                on_error(str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _do_generate(self, user_input: str) -> str:
        context = self._search_memory(user_input)
        response = self._call_model(user_input, context)
        response = self._execute_tools(response)
        return response

    def _search_memory(self, user_input: str) -> str:
        if not self.memory:
            return ''
        try:
            results = self.memory.search(user_input, top_k=3)
            if self.sem_memory and config.memory_mode == 'hybrid':
                sem = self.sem_memory.search(user_input, top_k=2)
                seen = set()
                for r in sem:
                    if r['text'] not in seen:
                        seen.add(r['text'])
                        results.append(r)
                results.sort(key=lambda x: x['score'], reverse=True)
                results = results[:3]
            if results:
                return '\n\n'.join(r['text'] for r in results)
        except Exception:
            pass
        return ''

    def _call_model(self, user_input: str, context: str) -> str:
        from cli import generate_response
        response, _, _, _ = generate_response(
            user_input, context, self.lm, self.memory,
        )
        return response

    def _execute_tools(self, response: str) -> str:
        from opensawcore import read_file, write_file, list_dir, run_command
        tool_results = []
        for match in re.finditer(
            r'\[(CMD|READ|WRITE|LS)\s+(.*?)\]', response, re.DOTALL,
        ):
            ttype = match.group(1)
            args = match.group(2).strip()
            if ttype == 'READ' and read_file:
                tool_results.append(f'📄 {args}:\n{read_file(args)}')
            elif ttype == 'LS' and list_dir:
                tool_results.append(f'📁 {args}:\n{list_dir(args)}')
            elif ttype == 'WRITE' and write_file:
                parts = args.split(maxsplit=1)
                if len(parts) >= 2:
                    tool_results.append(f'📝 {parts[0]}: {write_file(parts[0], parts[1])}')
            elif ttype == 'CMD' and run_command:
                tool_results.append(f'⚡ $ {args}\n{run_command(args)}')
        if tool_results:
            response += '\n\n' + '\n\n'.join(tool_results)
        return response
