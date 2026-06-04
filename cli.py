import os
import sys
import time
import json
import re
from datetime import datetime
from typing import List, Optional

# Ensure local modules are importable even without pip install
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

try:
    import readline

    SLASH_COMMANDS = [
        '/help', '/setup', '/info', '/exit',
        '/clear', '/stats', '/reset', '/save',
        '/export', '/model', '/forget', '/context',
        '/sys', '/session',
        '/regen', '/edit', '/cont',
        '/search', '/pin', '/unpin',
    ]

    def _slash_completer(text, state):
        if state == 0:
            if text.startswith('/'):
                _slash_completer.matches = [
                    c for c in SLASH_COMMANDS if c.startswith(text)
                ]
            else:
                _slash_completer.matches = []
        try:
            return _slash_completer.matches[state]
        except IndexError:
            return None

    readline.set_completer(_slash_completer)
    readline.set_completer_delims(' \t\n')
    readline.parse_and_bind('tab: complete')
except ImportError:
    pass

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.layout import Layout
from rich.prompt import Prompt
from rich import box

from config import config
from hardware_scanner import scan_hardware
from memory_engine import MemoryEngine, SemanticMemoryEngine
from utils import (
    get_logo,
    save_build,
    save_profile,
    load_profile,
)
from model import OpenSawLM
from llama_server import LlamaServer, build_server, _find_server

from plugins import get_manager, load_plugins, HookPoint

try:
    from tools import read_file, write_file, list_dir, run_command
except ImportError:
    read_file = write_file = list_dir = run_command = None

console = Console()


def generate_response(
    user_input: str,
    context: str,
    lm: OpenSawLM,
    memory: Optional[MemoryEngine] = None,
):
    prompt = (
        f"Ты {config.ai_name}, локальный ИИ-помощник пользователя "
        f"{config.user_name}. "
        f"Ты работаешь полностью на его устройстве. "
        f"У тебя есть векторная память, куда сохраняются все диалоги. "
        f"Отвечай естественно, по-русски, кратко и по делу.\n\n"
        f"У тебя есть доступ к файловой системе и терминалу.\n"
        f"  • [READ путь] — прочитать файл\n"
        f"  • [WRITE путь содержание] — записать файл\n"
        f"  • [LS путь] — список папки\n"
        f"  • [CMD команда] — выполнить в терминале (ls, cat, pwd, echo, python3, pip, grep, find и др.)\n"
        f"Используй их когда нужно. После выполнения покажи результат пользователю.\n\n"
    )

    if context:
        context_clean = context[:1200].replace('\n', ' ')
        prompt += f"Контекст из твоей памяти: {context_clean}\n\n"

    if memory:
        stats = memory.get_memory_stats()
        prompt += (
            f"У тебя {stats['documents']} документов в памяти, "
            f"словарь: {stats['vocabulary_size']} слов.\n"
            f"Если контекст уместен — используй его в ответе.\n"
        )

    prompt_tokens = lm.count_tokens(prompt, user_input)
    response = lm.chat(prompt, user_input)
    token_count = len(response.split())
    return response, token_count, prompt_tokens, prompt



# ---------------------------------------------------------------------------
# Click commands
# ---------------------------------------------------------------------------

def main_menu():
    """Interactive main menu."""
    while True:
        console.clear()
        logo = get_logo()
        console.print(f'[cyan]{logo}[/cyan]\n')

        menu_text = (
            '[bold cyan]╔════ OpenSaw — Local AI Framework ═══════╗[/bold cyan]\n'
            '[bold cyan]║[/bold cyan]                                            [bold cyan]║[/bold cyan]\n'
            '[bold cyan]║[/bold cyan]  [bold]1[/bold]  💬  Start Chat                    [bold cyan]║[/bold cyan]\n'
            '[bold cyan]║[/bold cyan]  [bold]2[/bold]  📅  Select Session               [bold cyan]║[/bold cyan]\n'
            '[bold cyan]║[/bold cyan]  [bold]3[/bold]  ⚙️   Setup (download model)      [bold cyan]║[/bold cyan]\n'
            '[bold cyan]║[/bold cyan]  [bold]4[/bold]  ℹ️   System Info                  [bold cyan]║[/bold cyan]\n'
            '[bold cyan]║[/bold cyan]  [bold]5[/bold]  ❤️   Help                         [bold cyan]║[/bold cyan]\n'
            '[bold cyan]║[/bold cyan]  [bold]6[/bold]  🚪  Exit                         [bold cyan]║[/bold cyan]\n'
            '[bold cyan]║[/bold cyan]                                            [bold cyan]║[/bold cyan]\n'
            f'[bold cyan]╚{"═" * 44}╝[/bold cyan]'
        )
        console.print(Panel(menu_text, border_style='cyan', title='[bold]🧠 Main Menu[/bold]'))

        choice = Prompt.ask(
            '[bold]Select[/bold]',
            choices=['1', '2', '3', '4', '5', '6'],
            default='1',
        )

        if choice == '1':
            _run_chat()
            continue
        elif choice == '2':
            _session_menu()
            continue
        elif choice == '3':
            setup()
            continue
        elif choice == '4':
            info()
            continue
        elif choice == '5':
            help_cmd()
            continue
        elif choice == '6':
            console.print('[dim]Goodbye.[/dim]')
            break

        if not Prompt.ask(
            '\n[dim]Press Enter to return to menu[/dim]',
            default='',
        ):
            continue


def _session_menu():
    """List and pick a session to load into chat."""
    console.clear()
    memory = MemoryEngine(workspace_dir=config.workspace_dir)
    sessions = memory.list_sessions()
    if not sessions:
        console.print('[yellow]No sessions found.[/yellow]')
        Prompt.ask('[dim]Press Enter[/dim]', default='')
        return

    console.print('[bold cyan]Available Sessions[/bold cyan]\n')
    for i, s in enumerate(sessions[-15:], 1):
        console.print(f'  [bold]{i}[/bold]  {s}')
    console.print(f'  [bold]n[/bold]  New session')
    console.print(f'  [bold]b[/bold]  Back to menu\n')

    choice = Prompt.ask('[bold]Select[/bold]', default='b')
    if choice == 'b':
        return
    if choice == 'n':
        _run_chat()
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            session_date = sessions[-15:][idx]
            console.print(f'[green]Loading session {session_date}...[/green]')
            # Override session_date and start chat
            _run_chat(override_session=session_date)
    except (ValueError, IndexError):
        pass


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """OpenSaw — Local AI Framework with neural memory and TUI chat."""
    if ctx.invoked_subcommand is None:
        main_menu()


@cli.command()
def setup():
    """Initialize framework, scan hardware, download language model."""
    console.clear()
    logo = get_logo()
    console.print(f'[cyan]{logo}[/cyan]')

    # --- Step 1: Init memory ---
    with console.status('[bold yellow]Initializing memory engine...[/bold yellow]'):
        memory = MemoryEngine(workspace_dir=config.workspace_dir)
        time.sleep(0.5)
    console.print('[green]  ✓ Memory structure created[/green]')
    console.print(f'    SOUL.md, MEMORY.md, logs in {config.workspace_dir}\n')

    # --- Step 2: Hardware scan ---
    with console.status('[bold yellow]Scanning hardware...[/bold yellow]'):
        hw = scan_hardware()
        time.sleep(0.3)

    hw_table = Table(
        title='[bold cyan]Hardware Profile[/bold cyan]',
        box=box.HEAVY,
        border_style='cyan',
    )
    hw_table.add_column('Component', style='bold yellow')
    hw_table.add_column('Value', style='green')
    hw_table.add_row('CPU Cores', str(hw.cpu_count))
    hw_table.add_row('CPU Load', f'{hw.cpu_percent}%')
    hw_table.add_row('RAM Total', f'{hw.ram_total_gb} GB')
    hw_table.add_row('RAM Available', f'{hw.ram_available_gb} GB')
    hw_table.add_row('CUDA Available', '[green]Yes[/green]' if hw.cuda_available else '[red]No[/red]')
    if hw.cuda_available:
        hw_table.add_row('CUDA Device', hw.cuda_device_name)
        hw_table.add_row('VRAM', f'{hw.vram_total_gb} GB')
    hw_table.add_row('Optimal Device', f'[bold]{hw.optimal_device}[/bold]')
    console.print(hw_table)
    print()

    # --- Step 3: Download language model ---
    resolved_name = lm.resolve_alias(config.model_name)
    is_gguf = lm.is_gguf()
    if is_gguf:
        repo, file = resolved_name.split(':', 1) if ':' in resolved_name else (resolved_name.rsplit('/', 1)[0], resolved_name.rsplit('/', 1)[1])
        model_short = file.replace('.gguf', '')
        backend_label = '[bold yellow]GGUF (llama.cpp)[/bold yellow]'
    else:
        model_short = config.model_name.split('/')[-1]
        backend_label = f'[bold]{device}[/bold]'
    device = hw.optimal_device

    card = Panel(
        f'\n'
        f'  [bold cyan]📋 Model:[/bold cyan]       [yellow]{config.model_name}[/yellow]\n'
        f'  [bold cyan]🏷️  File:[/bold cyan]        {model_short}\n'
        f'  [bold cyan]⚙️  Backend:[/bold cyan]     {backend_label}\n'
        f'  [bold cyan]🎯 Max Tokens:[/bold cyan]   {config.max_tokens}\n'
        f'  [bold cyan]🌡️  Temperature:[/bold cyan]  {config.temperature}\n'
        f'  [bold cyan]📁 Cache:[/bold cyan]        {config.datasets_cache}\n',
        title='[bold cyan]⚡ Language Model[/bold cyan]',
        border_style='bright_blue',
        padding=(1, 2),
    )
    console.print(card)
    print()

    lm = OpenSawLM(
        model_name=config.model_name,
        device=device,
        max_new_tokens=config.max_tokens,
        temperature=config.temperature,
    )

    if is_gguf:
        phases = [
            ('🌐', 'Connecting to Hugging Face Hub...', 0.3, False),
            ('📦', 'Downloading GGUF model...', 0.6, True),
            ('🔧', 'Loading model into memory...', 0.4, False),
        ]
    else:
        phases = [
            ('🌐', 'Connecting to Hugging Face Hub...', 0.4, False),
            ('📥', 'Downloading tokenizer...', 0.3, False),
            ('📦', 'Downloading model weights...', 0.6, True),
            ('🔧', 'Loading model into memory...', 0.3, False),
            ('⚡', 'Optimizing for inference...', 0.3, False),
        ]

    with console.status('') as status:
        for emoji, msg, portion, do_load in phases:
            status.update(
                f'[bold cyan]{emoji}  {msg}[/bold cyan]',
                spinner='dots',
                spinner_style='cyan',
            )
            if do_load:
                lm.load(cache_dir=config.datasets_cache)
            else:
                time.sleep(portion)

    with console.status('[bold green]✓  Model ready![/bold green]', spinner='point', spinner_style='green'):
        time.sleep(0.8)
    console.print()

    with console.status('[bold green]✓  Model ready![/bold green]', spinner='point', spinner_style='green'):
        time.sleep(0.6)

    # --- Step 4: Build record ---
    build_entry = save_build(model_short, {
        'device': device,
        'memory_docs': len(memory.documents),
    })
    console.print(f'[green]  ✓ Build #{build_entry["build_id"]} saved[/green]\n')

    console.print(
        '\n[bold green]✓ Setup complete![/bold green] '
        'Run [bold cyan]opensaw chat[/bold cyan] to start interacting.\n'
    )


def _build_cmd_table() -> str:
    lines = [
        '[bold cyan]Slash Commands:[/bold cyan]',
        '',
    ]
    for cmd, desc in [
        ('', ''),
        ('/help', 'Show this list'),
        ('/setup', 'Change user/AI name'),
        ('/regen', 'Regenerate last response'),
        ('/edit <text>', 'Edit last message & resend'),
        ('/cont', 'Continue generation'),
        ('/pin <text>', 'Pin context (always injected)'),
        ('/unpin', 'Clear pinned context'),
        ('/search <q>', 'Search memory'),
        ('/info', 'Dashboard'),
        ('/stats', 'Session statistics'),
        ('/clear', 'Clear chat panel'),
        ('/reset', 'Reset chat history'),
        ('/save', 'Save chat to file'),
        ('/export <fmt>', 'Export (md/json/txt)'),
        ('/forget', 'Erase vector memory'),
        ('/context', 'Show last context'),
        ('/model', 'Set params or switch model'),
        ('/sys', 'System info'),
        ('/session', 'Load/start sessions'),
        ('/exit', 'Quit'),
    ]:
        if cmd:
            lines.append(f'  [bold cyan]{cmd:<14}[/bold cyan]  {desc}')
    return '\n'.join(lines)


def _md_to_rich(text: str) -> str:
    """Convert Markdown formatting in AI responses to Rich markup."""
    from rich.markup import escape
    text = escape(text)
    text = re.sub(
        r'```(\w*)\n(.*?)```',
        r'[bold cyan]```\1[/bold cyan]\n[dim]\2[/dim]\n[bold cyan]```[/bold cyan]',
        text, flags=re.DOTALL,
    )
    text = re.sub(r'`([^`]+)`', r'[bright_cyan]\1[/bright_cyan]', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'[italic]\1[/italic]', text)
    text = re.sub(r'^>\s?(.*)', r'[dim]│[/dim] \1', text, flags=re.MULTILINE)
    return text


@cli.command()
def chat():
    """Start interactive TUI chat session with persistent layout."""
    _run_chat()


def _run_chat(override_session: str = ''):
    console.clear()

    # Load profile
    profile = load_profile()
    if profile:
        config.user_name = profile.get('user_name', config.user_name)
        config.ai_name = profile.get('ai_name', config.ai_name)

    # Init memory (hybrid: TF-IDF + semantic)
    memory = MemoryEngine(workspace_dir=config.workspace_dir)
    sem_memory = None
    if config.memory_mode in ('semantic', 'hybrid'):
        try:
            sem_memory = SemanticMemoryEngine(workspace_dir=config.workspace_dir)
        except Exception:
            sem_memory = None

    # Init / load language model
    device = config.device
    lm = OpenSawLM(
        model_name=config.model_name,
        device=device,
        max_new_tokens=config.max_tokens,
        temperature=config.temperature,
    )

    server = None
    if lm.is_gguf():
        server = LlamaServer(
            model_path=config.model_name,
            n_ctx=getattr(config, 'n_ctx', 4096),
        )
        if _find_server():
            with console.status('[bold yellow]Starting llama.cpp server...[/bold yellow]'):
                if server.start():
                    lm.use_server_backend(server)
                    console.print('[green]✓ llama.cpp server backend[/green]')
        else:
            console.print('[yellow]llama-server not found. Building...[/yellow]')
            if build_server():
                if server.start():
                    lm.use_server_backend(server)
                    console.print('[green]✓ llama.cpp server backend (built)[/green]')

    if server is None or not server.ready:
        try:
            with console.status('[bold yellow]Loading language model...[/bold yellow]'):
                lm.load(cache_dir=config.datasets_cache)
        except Exception as e:
            console.print(f'[red]Model load failed: {e}[/red]')
            console.print('[yellow]Run [bold]opensaw setup[/bold] first, or check model name.[/yellow]')
            Prompt.ask('[dim]Press Enter[/dim]', default='')
            return

    # ============== Plugin system ==============
    pm = get_manager()
    load_plugins()
    if pm._pending:
        console.print(f'[dim]Plugins found: {len(pm._pending)} — validating with AI…[/dim]')
        with console.status('[yellow]Validating plugins…[/yellow]'):
            validated = pm.validate_with_ai(lm)
        if validated:
            pm.activate(validated)
            for p in pm.plugins:
                console.print(f'  [green]✓ {p.name} {p.version}[/green]')
        console.print(f'[dim]Active: {len(pm.plugins)}, '
                      f'skipped: {len(pm._pending) - len(validated) if hasattr(pm._pending, "__len__") else 0}[/dim]')
    elif pm.plugins:
        for p in pm.plugins:
            console.print(f'[dim]Plugin: {p.name} {p.version}[/dim]')

    # Ensure server stops on exit
    import atexit
    if server:
        atexit.register(server.stop)

    # Allow plugins to replace the entire UI
    ui_replacement = pm.dispatch_capture(HookPoint.PRE_UI_LOOP, {
        'console': console, 'lm': lm, 'memory': memory,
        'sem_memory': sem_memory,
    })
    if ui_replacement is not None:
        return

    model_short = config.model_name.split('/')[-1]
    if lm.is_gguf():
        model_short = model_short.replace('.gguf', '')
        device_label = '[bold yellow]GGUF[/bold yellow]'
    else:
        device_label = f'[bold]{device}[/bold]'

    # ============== Persistent TUI Layout ==============
    layout = Layout()
    layout.split_column(
        Layout(name='header', size=3),
        Layout(name='body', ratio=1),
    )
    layout['body'].split_row(
        Layout(name='chat', ratio=3),
        Layout(name='thinking', ratio=2),
    )

    header_text = (
        f'[bold cyan]{config.ai_name}[/bold cyan]  |  '
        f'User: [green]{config.user_name}[/green]  |  '
        f'Model: [yellow]{model_short}[/yellow]  |  '
        f'Backend: {device_label}  |  '
        f'Mem: {len(memory.documents)} docs'
    )
    layout['header'].update(Panel(header_text, border_style='cyan'))

    chat_lines: List[str] = []
    think_lines: List[str] = [_build_cmd_table()]
    first_message = True
    msg_count = 0
    total_tok = 0
    total_gen_time = 0.0
    last_context = ''
    last_user_input = ''
    pinned_context = ''
    last_user_input = ''
    pinned_context = ''
    session_date = override_session or datetime.now().strftime('%Y-%m-%d')
    log_path = f'./workspace/memory/{session_date}.md'

    if override_session:
        msgs = memory.load_session_messages(override_session)
        for m in msgs[-20:]:
            speaker = m['speaker']
            if speaker == config.user_name or speaker == 'User':
                chat_lines.append(
                    f'[bold green]{speaker}[/bold green]: {m["text"]}'
                )
            else:
                chat_lines.append(
                    f'[bold magenta]{speaker}[/bold magenta]: {m["text"]}'
                )

    def redraw():
        console.clear()
        if first_message and not chat_lines:
            chat_body = (
                f'[cyan]{get_logo()}[/cyan]\n\n'
                f'[bold]Type a message or use /help[/bold]'
            )
        else:
            chat_body = '\n\n'.join(chat_lines[-30:])
        layout['chat'].update(Panel(
            chat_body, title='💬 Chat', border_style='cyan',
        ))
        is_cmd = think_lines and 'Slash Commands' in think_lines[0]
        layout['thinking'].update(Panel(
            '\n'.join(think_lines),
            title='[bold cyan]Slash Commands[/bold cyan]' if is_cmd else '[bold]🧠 Processing Pipeline[/bold]',
            border_style='cyan' if is_cmd else 'blue',
        ))
        console.print(layout)

    redraw()

    def _pop_last_ai_response():
        """Remove last AI response line from chat_lines (for /regen)."""
        for i in range(len(chat_lines) - 1, -1, -1):
            if f'[bold magenta]{config.ai_name}[/bold magenta]:' in chat_lines[i]:
                chat_lines.pop(i)
                break

    def _run_generation(user_input: str):
        nonlocal msg_count, total_tok, total_gen_time, last_context, think_lines, chat_lines, pinned_context

        chat_short = user_input[:30] + '…' if len(user_input) > 30 else user_input
        mem_docs = len(memory.documents)
        mem_vocab = len(memory.vocabulary)
        gen_start = time.time()

        think_lines = [
            f'[green]📥  Input[/green]       # {msg_count}  "{chat_short}"',
            f'[green]📊  Embedding[/green]  dim={config.embedding_dim}',
            f'[yellow]🔍  Memory[/yellow]       searching…',
            f'[dim]🤖  Generation[/dim]   waiting…',
            f'[dim]💬  Response[/dim]     waiting…',
            '',
            f'[dim]⚙️  {device}[/dim]',
            f'[dim]🌡️  t={config.temperature}  p=0.8  max={config.max_tokens}[/dim]',
            f'[dim]🗄️  {mem_docs} docs · {mem_vocab} vocab[/dim]',
            f'[dim]📁  {log_path}[/dim]',
        ]
        redraw()

        try:
            context_results = memory.search(user_input, top_k=3)
            if sem_memory and config.memory_mode == 'hybrid':
                sem_results = sem_memory.search(user_input, top_k=2)
                seen = set()
                for r in sem_results:
                    if r['text'] not in seen:
                        seen.add(r['text'])
                        context_results.append(r)
                context_results.sort(key=lambda x: x['score'], reverse=True)
                context_results = context_results[:3]
            context = '\n\n'.join(r['text'] for r in context_results)
            n_found = len(context_results)
            scores_str = ', '.join(f'{r["score"]:.2f}' for r in context_results) if n_found else '—'

            pm.dispatch(HookPoint.PRE_GENERATION, {
                'user_input': user_input, 'context': context,
                'n_found': n_found, 'scores_str': scores_str,
            })

            think_lines = [
                f'[green]📥  Input[/green]       # {msg_count}  "{chat_short}"',
                f'[green]📊  Embedding[/green]  dim={config.embedding_dim}',
                f'[green]🔍  Memory[/green]       {n_found} found  [dim]({scores_str})[/dim]',
                f'[yellow]🤖  Generation[/yellow]   generating…',
                f'[dim]💬  Response[/dim]     waiting…',
                '',
                f'[dim]⚙️  {device}[/dim]',
                f'[dim]🌡️  t={config.temperature}  p=0.8  max={config.max_tokens}[/dim]',
                f'[dim]🗄️  {mem_docs} docs · {mem_vocab} vocab[/dim]',
                f'[dim]📁  {log_path}[/dim]',
            ]
            redraw()

            context_used = ''
            if pinned_context:
                context_used = pinned_context + '\n\n'
            context_used += context

            response, token_count, prompt_tokens, built_prompt = generate_response(
                user_input, context_used, lm, memory,
            )
        except Exception as e:
            chat_lines.append(f'[red]Generation error: {e}[/red]')
            redraw()
            return

        gen_elapsed = time.time() - gen_start
        total_tok += token_count
        total_gen_time += gen_elapsed
        last_context = context

        pm.dispatch(HookPoint.POST_GENERATION, {
            'user_input': user_input, 'response': response,
            'token_count': token_count, 'prompt_tokens': prompt_tokens,
            'built_prompt': built_prompt, 'gen_elapsed': gen_elapsed,
        })

        tool_results = []
        for match in re.finditer(r'\[(CMD|READ|WRITE|LS)\s+(.*?)\]', response, re.DOTALL):
            tool_type = match.group(1)
            args = match.group(2).strip()
            pm.dispatch(HookPoint.PRE_TOOL, {
                'tool_type': tool_type, 'args': args,
            })
            plugin_result = pm.handle_tool(tool_type, args)
            if plugin_result is not None:
                tool_results.append(plugin_result)
            elif tool_type == 'READ':
                result = read_file(args)
                tool_results.append(f'📄 {args}:\n{result}')
            elif tool_type == 'LS':
                result = list_dir(args)
                tool_results.append(f'📁 {args}:\n{result}')
            elif tool_type == 'WRITE':
                parts = args.split(maxsplit=1)
                if len(parts) >= 2:
                    result = write_file(parts[0], parts[1])
                    tool_results.append(f'📝 {parts[0]}: {result}')
            elif tool_type == 'CMD':
                result = run_command(args)
                tool_results.append(f'⚡ $ {args}\n{result}')
            pm.dispatch(HookPoint.POST_TOOL, {
                'tool_type': tool_type, 'args': args, 'result': result,
            })
        if tool_results:
            response += '\n\n' + '\n\n'.join(tool_results)

        pm.dispatch(HookPoint.PRE_OUTPUT, {
            'response': response, 'tool_results': tool_results,
        })

        # Typing effect
        typed = ''
        spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        spinner_idx = 0
        for char in response:
            sp = spinner_frames[spinner_idx % len(spinner_frames)]
            spinner_idx += 1
            typed += char
            chat_body = '\n\n'.join(chat_lines[-28:])
            chat_body += f'\n\n[bold magenta]{config.ai_name}[/bold magenta]: {typed}'
            layout['chat'].update(Panel(
                chat_body, title='💬 Chat', border_style='cyan',
            ))
            tool_info = ''
            if tool_results:
                tool_info = f' | 🔧 {len(tool_results)} tools'
            think_lines = [
                f'[green]📥  Input[/green]       # {msg_count}  "{chat_short}"',
                f'[green]📊  Embedding[/green]  dim={config.embedding_dim}',
                f'[green]🔍  Memory[/green]       {n_found}  [dim]({scores_str})[/dim]',
                f'[green]🤖  Prompt[/green]     {prompt_tokens} tok.  {tool_info}',
                f'[green]💬  Response[/green]    {sp} {len(typed)} / {len(response)} chars',
                '',
                f'[dim]⚙️  {device}[/dim]',
                f'[dim]🌡️  t={config.temperature}  p=0.8  max={config.max_tokens}[/dim]',
                f'[dim]🗄️  {mem_docs} docs · {mem_vocab} vocab[/dim]',
                f'[dim]⏱️  gen: {gen_elapsed:.1f}s[/dim]',
                f'[dim]📁  {log_path}[/dim]',
            ]
            layout['thinking'].update(Panel(
                '\n'.join(think_lines),
                title='[bold]🧠 Processing Pipeline[/bold]',
                border_style='green',
            ))
            console.clear()
            console.print(layout)

        tool_info = ''
        if tool_results:
            tool_info = f' | 🔧 {len(tool_results)} tools'
        think_lines = [
            f'[green]📥  Input[/green]       # {msg_count}  "{chat_short}"',
            f'[green]📊  Embedding[/green]  dim={config.embedding_dim}',
            f'[green]🔍  Memory[/green]       {n_found}  [dim]({scores_str})[/dim]',
            f'[green]🤖  Prompt[/green]     {prompt_tokens} tok.{tool_info}',
            f'[green]💬  Response[/green]    ✓ {token_count} tok.',
            '',
            f'[dim]⚙️  {device}[/dim]',
            f'[dim]🌡️  t={config.temperature}  p=0.8  max={config.max_tokens}[/dim]',
            f'[dim]🗄️  {mem_docs} docs · {mem_vocab} vocab[/dim]',
            f'[dim]⏱️  gen: {gen_elapsed:.1f}s[/dim]',
            f'[dim]📁  {log_path}[/dim]',
        ]

        chat_lines.append(
            f'[bold magenta]{config.ai_name}[/bold magenta]: {_md_to_rich(response)}'
        )
        memory.log_conversation(user_input, response)
        pm.dispatch(HookPoint.POST_OUTPUT, {
            'user_input': user_input, 'response': response,
        })
        redraw()

    while True:
        try:
            raw = Prompt.ask(f'[bold green]{config.user_name}[/bold green]')
        except (EOFError, KeyboardInterrupt):
            break

        if not raw.strip():
            continue

        pm.dispatch(HookPoint.POST_INPUT, {
            'raw': raw, 'chat_lines': chat_lines,
        })

        # --- Slash commands ---
        if raw.startswith('/'):
            # Show command hint in thinking panel
            if not think_lines or not any('Slash Commands' in l for l in think_lines):
                think_lines = [_build_cmd_table()]

            cmd_line = raw[1:].strip()
            cmd_parts = cmd_line.split()
            cmd = cmd_parts[0].lower() if cmd_parts else ''
            cmd_arg = cmd_parts[1] if len(cmd_parts) > 1 else ''

            if not cmd:
                redraw()
                continue

            if cmd == 'exit':
                break

            elif cmd == 'help':
                chat_lines.append('[bold yellow]/help[/bold yellow]')
                help_text = (
                    '[dim]/help          — this list\n'
                    '/setup         — change name/ai name\n'
                    '/regen         — regenerate last AI response\n'
                    '/edit <text>   — edit last message & resend\n'
                    '/cont          — continue generation\n'
                    '/pin <text>    — pin content to context\n'
                    '/unpin         — clear pinned content\n'
                    '/search <q>    — search in memory\n'
                    '/info          — dashboard\n'
                    '/stats         — session statistics\n'
                    '/clear         — clear chat panel\n'
                    '/reset         — reset chat history\n'
                    '/save          — save chat to file\n'
                    '/export <fmt>  — export (md/json/txt)\n'
                    '/forget        — erase vector memory\n'
                    '/context       — show last retrieved context\n'
                    '/model t=0.7   — set params or switch model\n'
                    '/sys           — system info\n'
                    '/session       — session management\n'
                    '/exit          — quit[/dim]'
                )
                chat_lines.append(help_text)

            elif cmd == 'setup':
                new_user = Prompt.ask('Username', default=config.user_name)
                new_ai = Prompt.ask('AI name', default=config.ai_name)
                config.user_name = new_user
                config.ai_name = new_ai
                save_profile(new_user, new_ai)
                device_label = '[bold yellow]GGUF[/bold yellow]' if lm.is_gguf() else f'[bold]{device}[/bold]'
                header_text = (
                    f'[bold cyan]{config.ai_name}[/bold cyan]  |  '
                    f'User: [green]{config.user_name}[/green]  |  '
                    f'Model: [yellow]{model_short}[/yellow]  |  '
                    f'Backend: {device_label}  |  '
                    f'Mem: {len(memory.documents)} docs'
                )
                layout['header'].update(Panel(header_text, border_style='cyan'))
                chat_lines.append(
                    f'[bold yellow]Profile: user={new_user}, ai={new_ai}[/bold yellow]'
                )
            elif cmd == 'info':
                chat_lines.append('[bold yellow]/info[/bold yellow]')
                chat_lines.append(
                    f'[dim]Documents:[/dim] {len(memory.documents)}  |  '
                    f'[dim]Vocabulary:[/dim] {len(memory.vocabulary)}  |  '
                    f'[dim]Model:[/dim] {config.model_name.split("/")[-1]}  |  '
                    f'[dim]Device:[/dim] {device}'
                )
            elif cmd == 'stats':
                avg_time = total_gen_time / msg_count if msg_count else 0
                chat_lines.append('[bold yellow]/stats[/bold yellow]')
                chat_lines.append(
                    f'[dim]Messages:[/dim] {msg_count}\n'
                    f'[dim]Total tokens:[/dim] {total_tok}\n'
                    f'[dim]Avg gen time:[/dim] {avg_time:.1f}s\n'
                    f'[dim]Memory docs:[/dim] {len(memory.documents)}\n'
                    f'[dim]Vocabulary:[/dim] {len(memory.vocabulary)}'
                )
            elif cmd == 'clear':
                chat_lines.clear()
                chat_lines.clear()
                chat_lines.append(
                    '[dim]Chat cleared[/dim]'
                )

            elif cmd == 'reset':
                chat_lines.clear()
                chat_lines.clear()
                chat_lines.append(
                    '[dim]Chat history reset[/dim]'
                )

            elif cmd == 'save':
                save_name = cmd_arg or f'chat_{datetime.now():%H%M%S}'
                save_path = os.path.join(
                    config.workspace_dir, f'{save_name}.md'
                )
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write('\n\n'.join(chat_lines))
                chat_lines.append('[bold yellow]/save[/bold yellow]')
                chat_lines.append(
                    f'[dim]Saved to {save_path}[/dim]'
                )
            elif cmd == 'export':
                fmt = cmd_arg or 'json'
                chat_lines.append(f'[bold yellow]/export {fmt}[/bold yellow]')
                if fmt == 'txt':
                    txt_path = os.path.join(config.workspace_dir, 'chat_export.txt')
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        stripped = []
                        for l in chat_lines:
                            l_clean = l.replace('[dim]', '').replace('[/dim]', '')
                            l_clean = l_clean.replace('[bold]', '').replace('[/bold]', '')
                            stripped.append(l_clean)
                        f.write('\n'.join(stripped))
                    chat_lines.append(f'[dim]Exported to {txt_path}[/dim]')
                elif fmt == 'md':
                    md_path = os.path.join(config.workspace_dir, 'chat_export.md')
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write('\n\n'.join(chat_lines))
                    chat_lines.append(f'[dim]Exported to {md_path}[/dim]')
                else:
                    export_path = memory.export_as_json(
                        os.path.join(config.workspace_dir, 'memory_export.json')
                    )
                    chat_lines.append(f'[dim]Exported to {export_path}[/dim]')
            elif cmd == 'forget':
                memory.clear_memory()
                chat_lines.append('[bold yellow]/forget[/bold yellow]')
                chat_lines.append(
                    '[dim]Memory cleared. Rebuilding index…[/dim]'
                )
            elif cmd == 'context':
                chat_lines.append('[bold yellow]/context[/bold yellow]')
                if last_context:
                    snippet = last_context[:500].replace('\n', ' ')
                    chat_lines.append(
                        f'[dim]Last context:[/dim] {snippet}…'
                    )
                else:
                    chat_lines.append(
                        '[dim]No context retrieved yet[/dim]'
                    )
            elif cmd == 'model':
                if cmd_arg == 'list':
                    from model import AVAILABLE_MODELS as _avail, AVAILABLE_GGUF as _gguf
                    chat_lines.append('[bold yellow]/model list[/bold yellow]')
                    lines = ['[bold cyan]Transformers:[/bold cyan]']
                    for alias, hf_name in _avail.items():
                        mark = ' ← active' if hf_name == config.model_name or alias == config.model_name else ''
                        lines.append(f'  [bold]{alias}[/bold]  {hf_name}{mark}')
                    lines.append('')
                    lines.append('[bold cyan]GGUF (llama.cpp):[/bold cyan]')
                    for alias, (repo, file) in _gguf.items():
                        mark = ' ← active' if alias == config.model_name else ''
                        lines.append(f'  [bold]{alias}[/bold]  {repo}  [{file}]{mark}')
                    chat_lines.append('\n'.join(lines))
                elif cmd_arg == 'download':
                    chat_lines.append('[bold yellow]/model download[/bold yellow]')
                    download_alias = None
                    for part in cmd_parts[2:]:
                        if part in _gguf:
                            download_alias = part
                            break
                    if download_alias:
                        repo, file = _gguf[download_alias]
                        chat_lines.append(f'[dim]Downloading {repo} {file}…[/dim]')
                        try:
                            from model import OpenSawLM as _lm_cls_2
                            _lm_cls_2.download_model(repo, file, config.workspace_dir)
                            chat_lines.append(f'[dim]Downloaded {download_alias}[/dim]')
                        except Exception as exc:
                            chat_lines.append(f'[red]Failed: {exc}[/red]')
                    else:
                        aliases = ', '.join(_gguf.keys())
                        chat_lines.append(f'[dim]Usage: /model download <alias>  ({aliases})[/dim]')
                elif cmd_arg:
                    from model import OpenSawLM as _lm_cls, AVAILABLE_MODELS as _avail, AVAILABLE_GGUF as _gguf
                    new_name = _avail.get(cmd_arg, _gguf.get(cmd_arg, cmd_arg))
                    chat_lines.append(f'[bold yellow]/model {cmd_arg}[/bold yellow]')
                    try:
                        config.model_name = new_name if isinstance(new_name, str) else cmd_arg
                        with console.status(f'[yellow]Loading {new_name}...[/yellow]'):
                            lm.reload(new_name if isinstance(new_name, str) else cmd_arg)
                        model_short = str(new_name).split('/')[-1].replace('.gguf', '')
                        device_label = '[bold yellow]GGUF[/bold yellow]' if lm.is_gguf() else f'[bold]{device}[/bold]'
                        header_text = (
                            f'[bold cyan]{config.ai_name}[/bold cyan]  |  '
                            f'User: [green]{config.user_name}[/green]  |  '
                            f'Model: [yellow]{model_short}[/yellow]  |  '
                            f'Backend: {device_label}  |  '
                            f'Mem: {len(memory.documents)} docs'
                        )
                        layout['header'].update(Panel(
                            header_text, border_style='cyan'
                        ))
                        chat_lines.append(
                            f'[dim]Model switched to {model_short}[/dim]'
                        )
                    except Exception as exc:
                        chat_lines.append(
                            f'[red]Failed: {exc}[/red]'
                        )
                else:
                    for part in cmd_parts[1:]:
                        if '=' in part:
                            key, val = part.split('=', 1)
                            if key == 't':
                                config.temperature = float(val)
                            elif key == 'max':
                                config.max_tokens = int(val)
                    chat_lines.append('[bold yellow]/model[/bold yellow]')
                    chat_lines.append(
                        f'[dim]Params: t={config.temperature} '
                        f'max={config.max_tokens}[/dim]'
                    )

            elif cmd == 'sys':
                chat_lines.append('[bold yellow]/sys[/bold yellow]')
                hw = scan_hardware()
                chat_lines.append(
                    f'[dim]CPU:[/dim] {hw.cpu_count} cores '
                    f'({hw.cpu_percent}%)\n'
                    f'[dim]RAM:[/dim] {hw.ram_available_gb:.1f}/{hw.ram_total_gb} GB free\n'
                    f'[dim]CUDA:[/dim] {"Yes — " + hw.cuda_device_name if hw.cuda_available else "No"}\n'
                    f'[dim]Device:[/dim] {hw.optimal_device}\n'
                    f'[dim]Model:[/dim] {config.model_name}\n'
                    f'[dim]Workspace:[/dim] {config.workspace_dir}'
                )

            elif cmd == 'session':
                sessions = memory.list_sessions()
                chat_lines.append('[bold yellow]/session[/bold yellow]')
                if cmd_arg == 'new':
                    session_date = datetime.now().strftime('%Y-%m-%d')
                    log_path = f'./workspace/memory/{session_date}.md'
                    chat_lines.append(
                        f'[dim]New session: {session_date}[/dim]'
                    )
                elif cmd_arg:
                    if cmd_arg in sessions:
                        session_date = cmd_arg
                        log_path = f'./workspace/memory/{session_date}.md'
                        msgs = memory.load_session_messages(cmd_arg)
                        chat_lines.clear()
                        for m in msgs[-20:]:
                            speaker = m['speaker']
                            if speaker == config.user_name or speaker == 'User':
                                chat_lines.append(
                                    f'[bold green]{speaker}[/bold green]: {m["text"]}'
                                )
                            else:
                                chat_lines.append(
                                    f'[bold magenta]{speaker}[/bold magenta]: {m["text"]}'
                                )
                        chat_lines.insert(0,
                            f'[dim]--- Session {cmd_arg} loaded ---[/dim]'
                        )
                        chat_lines.append(
                            f'[dim]--- {len(msgs)} messages loaded ---[/dim]'
                        )
                    else:
                        chat_lines.append(
                            f'[red]Session not found: {cmd_arg}[/red]'
                        )
                else:
                    if sessions:
                        chat_lines.append(
                            f'[dim]Available sessions:[/dim]\n'
                            + '\n'.join(f'  • {s}' for s in sessions[-10:])
                        )
                    else:
                        chat_lines.append(
                            '[dim]No sessions found[/dim]'
                        )

            elif cmd == 'regen':
                chat_lines.append('[bold yellow]/regen[/bold yellow]')
                if not last_user_input:
                    chat_lines.append('[dim]No previous message to regenerate[/dim]')
                elif not any(f'[bold magenta]{config.ai_name}[/bold magenta]:' in l for l in chat_lines):
                    chat_lines.append('[dim]No AI response to regenerate[/dim]')
                else:
                    _pop_last_ai_response()
                    _run_generation(last_user_input)

            elif cmd == 'edit':
                if not cmd_arg:
                    chat_lines.append('[bold yellow]/edit <text>[/bold yellow]')
                    chat_lines.append('[dim]Usage: /edit new message text[/dim]')
                else:
                    chat_lines.append(f'[bold yellow]/edit[/bold yellow]')
                    for i in range(len(chat_lines) - 1, -1, -1):
                        if f'[bold green]{config.user_name}[/bold green]:' in chat_lines[i]:
                            chat_lines.pop(i)
                            break
                    if chat_lines and '[dim]────────────────[/dim]' == chat_lines[-1]:
                        chat_lines.pop()
                    chat_lines.append(f'[bold green]{config.user_name}[/bold green]: {cmd_arg}')
                    last_user_input = cmd_arg
                    _run_generation(cmd_arg)

            elif cmd == 'cont':
                chat_lines.append('[bold yellow]/cont[/bold yellow]')
                if not last_user_input:
                    chat_lines.append('[dim]No message to continue[/dim]')
                else:
                    _pop_last_ai_response()
                    # Remove the separator too if it was after the AI response
                    if chat_lines and '[dim]────────────────[/dim]' == chat_lines[-1]:
                        chat_lines.pop()
                    cont_input = last_user_input + ' (продолжи)'
                    _run_generation(cont_input)

            elif cmd == 'search':
                chat_lines.append(f'[bold yellow]/search {cmd_arg}[/bold yellow]')
                if cmd_arg:
                    results = memory.search(cmd_arg, top_k=5)
                    if results:
                        for r in results:
                            snippet = r['text'][:200].replace('\n', ' ')
                            chat_lines.append(
                                f'[dim]• [{r["score"]:.2f}][/dim] {snippet}…'
                            )
                    else:
                        chat_lines.append('[dim]Nothing found[/dim]')
                else:
                    chat_lines.append('[dim]Usage: /search <query>[/dim]')

            elif cmd == 'pin':
                if not cmd_arg:
                    chat_lines.append('[bold yellow]/pin <text>[/bold yellow]')
                    chat_lines.append('[dim]Usage: /pin text to pin[/dim]')
                else:
                    pinned_context = cmd_arg
                    chat_lines.append(f'[bold yellow]/pin[/bold yellow]')
                    chat_lines.append(f'[dim]Pinned: {cmd_arg}[/dim]')

            elif cmd == 'unpin':
                pinned_context = ''
                chat_lines.append('[bold yellow]/unpin[/bold yellow]')
                chat_lines.append('[dim]Pinned context cleared[/dim]')

            else:
                handled = pm.handle_command(cmd, cmd_arg)
                if handled:
                    chat_lines.append(f'[bold yellow]/{cmd}[/bold yellow]')
                else:
                    chat_lines.append(
                        f'[red]Unknown: /{cmd}[/red]  Try /help'
                    )
            first_message = False
            redraw()
            continue

        # --- Regular message ---
        first_message = False
        msg_count += 1
        if chat_lines:
            chat_lines.append('[dim]────────────────[/dim]')
        chat_lines.append(f'[bold green]{config.user_name}[/bold green]: {raw}')
        last_user_input = raw
        _run_generation(raw)


@cli.command()
def info():
    """Display full AI architecture dashboard."""
    console.clear()

    memory = MemoryEngine(workspace_dir=config.workspace_dir)

    # --- Layout ---
    layout = Layout()
    layout.split_column(
        Layout(name='top'),
        Layout(name='bottom'),
    )

    # Top: architecture tree
    tree = Tree(
        '[bold cyan]🧠 OpenSaw Architecture — Request Path[/bold cyan]',
        guide_style='bright_blue',
    )

    input_node = tree.add('[bold]💬 User Input[/bold]')
    input_node.add(f'Raw text → chat loop')

    vec_node = tree.add('[bold yellow]📊 Vectorization Engine[/bold yellow]')
    vec_node.add(f'Hash-based embedding (dim={config.embedding_dim})')
    vec_node.add(f'L2 normalization applied')

    mem_node = tree.add('[bold magenta]🧠 Memory Subsystem[/bold magenta]')
    mem_node.add(f'TF-IDF sparse encoding')
    mem_node.add(f'Cosine similarity search')
    mem_node.add(f'Documents indexed: [green]{len(memory.documents)}[/green]')
    mem_node.add(f'Vocabulary: [green]{len(memory.vocabulary)}[/green] terms')

    nn_node = tree.add('[bold green]🤖 Language Model (OpenSawLM)[/bold green]')
    nn_node.add(f'Model: [yellow]{config.model_name.split("/")[-1]}[/yellow]')
    nn_node.add('Qwen2.5 0.5B-Instruct (transformers)')
    nn_node.add('Full autoregressive text generation')

    gen_node = tree.add('[bold blue]💡 Output Generator[/bold blue]')
    gen_node.add('System prompt + user input → LM.generate()')
    gen_node.add('Memory context injected into system prompt')
    gen_node.add('Natural Russian response (no templates)')

    layout['top'].update(Panel(tree, border_style='cyan'))

    # Bottom: status tables
    status = Table(
        title='[bold cyan]System Parameters[/bold cyan]',
        box=box.HEAVY,
        border_style='cyan',
    )
    status.add_column('Parameter', style='bold yellow')
    status.add_column('Value', style='green')

    status.add_row('Device', f'[bold]{config.device}[/bold]')
    status.add_row('User Name', config.user_name)
    status.add_row('AI Name', config.ai_name)
    status.add_row('Workspace', config.workspace_dir)
    status.add_row('Cache', config.datasets_cache)
    status.add_row('Models Dir', config.models_dir)
    status.add_row('Embedding Dim', str(config.embedding_dim))
    status.add_row('Max Tokens', str(config.max_tokens))
    status.add_row('Temperature', str(config.temperature))

    status.add_row(
        'Latest Model',
        f'[yellow]{config.model_name.split("/")[-1]}[/yellow]'
    )
    status.add_row('Model Source', config.model_name)

    mem_stats = memory.get_memory_stats()
    status.add_row(
        'Memory Docs',
        str(mem_stats.get('documents', '?'))
    )
    status.add_row(
        'Memory Vocab',
        str(mem_stats.get('vocabulary_size', '?'))
    )

    layout['bottom'].update(
        Panel(
            Columns([status]),
            border_style='green',
            title='[bold]Configuration & Status[/bold]',
        )
    )

    console.print(layout)


@cli.command(name='help')
def help_cmd():
    """Show comprehensive framework help."""
    console.clear()
    logo = get_logo()
    console.print(f'[cyan]{logo}[/cyan]')
    print()

    # Global commands
    cmd_table = Table(
        title='[bold cyan]Global Commands[/bold cyan]',
        box=box.HEAVY,
        border_style='cyan',
        show_header=True,
        header_style='bold yellow',
    )
    cmd_table.add_column('Command', width=20)
    cmd_table.add_column('Description', width=60)

    cmd_table.add_row(
        '[bold]opensaw setup[/bold]',
        'Initialize workspace memory structure, scan hardware, download '
        'the generative language model (Qwen2.5-0.5B-Instruct), and record '
        'the build.',
    )
    cmd_table.add_row(
        '[bold]opensaw chat[/bold]',
        'Launch the interactive TUI chat. Features slash commands '
        '(/help, /setup, /info, /exit), TF-IDF vector memory retrieval, '
        'generative LM response, and per-session conversation logging.',
    )
    cmd_table.add_row(
        '[bold]opensaw info[/bold]',
        'Display a full architecture dashboard showing the request '
        'processing pipeline, memory statistics, model parameters, '
        'and current configuration values.',
    )
    cmd_table.add_row(
        '[bold]opensaw help[/bold]',
        'Show this comprehensive help page with ASCII art logo, '
        'global command reference, and chat macro documentation.',
    )
    cmd_table.add_row(
        '[bold]opensaw serve[/bold]',
        'Start the FastAPI web server with REST API and Web UI '
        'at http://127.0.0.1:8080 (optional: --host --port).',
    )

    console.print(cmd_table)
    print()

    # Slash commands
    slash_table = Table(
        title='[bold cyan]Chat Slash Commands[/bold cyan]',
        box=box.HEAVY,
        border_style='cyan',
        show_header=True,
        header_style='bold yellow',
    )
    slash_table.add_column('Command', width=12)
    slash_table.add_column('Description', width=68)

    slash_table.add_row(
        '[bold]/help[/bold]',
        'Display a table of all available chat slash commands '
        'directly inside the chat panel.',
    )
    slash_table.add_row(
        '[bold]/setup[/bold]',
        'Enter interactive chat setup mode to change the user display '
        'name and AI name on the fly. Changes persist via profile.json.',
    )
    slash_table.add_row(
        '[bold]/info[/bold]',
        'Show a live mini-dashboard with current memory index shape, '
        'model name, device, and user/AI names.',
    )
    slash_table.add_row(
        '[bold]/exit[/bold]',
        'Cleanly exit the chat session. All conversation logs are '
        'saved to the memory directory.',
    )
    slash_table.add_row(
        '[bold]/stats[/bold]',
        'Show session statistics: message count, total tokens, '
        'average generation time, memory size.',
    )
    slash_table.add_row(
        '[bold]/clear[/bold]',
        'Clear the chat panel display without affecting memory.',
    )
    slash_table.add_row(
        '[bold]/reset[/bold]',
        'Reset chat history for the current session. Memory is kept.',
    )
    slash_table.add_row(
        '[bold]/save[/bold]',
        'Save the current chat transcript to a markdown file. '
        'Optional filename: /save mylog',
    )
    slash_table.add_row(
        '[bold]/export[/bold]',
        'Export the entire vector memory index to a JSON file '
        'for external analysis.',
    )
    slash_table.add_row(
        '[bold]/forget[/bold]',
        'Erase all vector memory documents and rebuild the index '
        'from scratch.',
    )
    slash_table.add_row(
        '[bold]/context[/bold]',
        'Display the memory context retrieved for the most recent '
        'user message.',
    )
    slash_table.add_row(
        '[bold]/model[/bold]',
        'Adjust generation parameters on the fly. '
        'Usage: /model t=0.8 max=300',
    )
    slash_table.add_row(
        '[bold]/sys[/bold]',
        'Show real-time system information: CPU cores, RAM usage, '
        'CUDA availability, model name and workspace path.',
    )
    slash_table.add_row(
        '[bold]/session[/bold]',
        'List available session dates. /session YYYY-MM-DD loads '
        'that session. /session new starts a fresh session.',
    )

    console.print(slash_table)
    print()

    # Architecture panel
    arch_panel = Panel(
        '[bold cyan]Vector Memory Architecture[/bold cyan]\n\n'
        '[yellow]1. Memory Structure[/yellow]\n'
        f'  • Workspace root: [green]{config.workspace_dir}[/green]\n'
        '  • SOUL.md — cognitive profile (identity, directives, personality)\n'
        '  • MEMORY.md — long-term knowledge base\n'
        '  • ./memory/YYYY-MM-DD.md — per-session conversation logs\n\n'
        '[yellow]2. TF-IDF Vector Index[/yellow]\n'
        '  • All .md files are tokenized and indexed on startup\n'
        '  • Vocabulary built from unique word stems\n'
        '  • Term Frequency (TF) × Inverse Document Frequency (IDF)\n'
        '  • Cosine similarity for relevance scoring\n'
        '  • Top-3 most relevant passages retrieved per query\n\n'
        '[yellow]3. Language Model[/yellow]\n'
        f'  • OpenSawLM: [yellow]{config.model_name.split("/")[-1]}[/yellow] (Qwen2.5)\n'
        '  • Loaded via transformers, fully local\n'
        '  • Autoregressive text generation with configurable temperature\n'
        '  • Cached in datasets_cache directory\n\n'
        '[yellow]4. Response Pipeline[/yellow]\n'
        '  User Input → TF-IDF Memory Search → Context Assembly → '
        'System Prompt → LM.generate() → Typing Effect Output\n\n'
        '[green]All processing is 100% local — no external API calls.[/green]',
        border_style='cyan',
        title='[bold]Architecture Overview[/bold]',
    )

    console.print(arch_panel)
    print()


# Serve command (if server deps are available)
try:
    from server import start_server

    @cli.command()
    @click.option('--host', default='127.0.0.1', help='Host to bind')
    @click.option('--port', default=8080, help='Port to bind', type=int)
    def serve(host: str, port: int):
        """Start web server with REST API and Web UI."""
        start_server(host=host, port=port)
except ImportError:
    pass

if __name__ == '__main__':
    cli()
