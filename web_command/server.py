import asyncio
import logging
import sys
from aiohttp import web, WSMsgType
from colors import color
from pathlib import Path
from ptyprocess import PtyProcess


logger = logging.getLogger(__name__)


class WebSocketServer(object):

    DEFAULT_BUFFER_SIZE = 10000
    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 8000
    STATIC_DIR = Path(__file__).resolve().parent / 'static'
    INDEX_PATH = STATIC_DIR / 'default.html'

    def __init__(self, loop=None, host=DEFAULT_HOST, port=DEFAULT_PORT,
                 output=None, buffer_size=DEFAULT_BUFFER_SIZE):
        self.loop = loop or asyncio.get_event_loop()
        self.host = host
        self.port = port
        self.output = output
        self.buffer_size = buffer_size
        self.clients = set()
        self.buffer = b''
        self._create_app()

    def _create_app(self):
        self.app = app = web.Application(loop=self.loop)
        app.router.add_routes([
            web.get('/', self.index_handler),
            web.get('/ws', self.websocket_handler),
        ])
        app.router.add_static(
            '/', str(self.STATIC_DIR), follow_symlinks=True)

        async def no_cache(request, response):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
            response.headers['Pragma'] = 'no-cache'
        app.on_response_prepare.append(no_cache)

        async def cleanup(app):
            logger.info('Exiting...')
        app.on_cleanup.append(cleanup)

    def run_forever(self):
        logger.info('Listening on {}:{}...'.format(self.host, self.port))
        web.run_app(self.app, host=self.host, port=self.port, print=None)

    async def on_receive(self, data):
        # Override this method to handle keystrokes from web clients.
        pass

    async def send(self, data):
        if data:
            self.buffer += data
            current_size = len(self.buffer)
            if current_size > self.buffer_size:
                self.buffer = self.buffer[current_size - self.buffer_size:-1]
            for ws in self.clients:
                await ws.send_bytes(data)
            if self.output:
                self.output.buffer.write(data)
                self.output.flush()

    async def send_alert(self, text):
        alert = color(text + '\r\n', fg='yellow', style='bold').encode()
        return await self.send(alert)

    async def index_handler(self, request):
        return web.FileResponse(self.INDEX_PATH)

    async def websocket_handler(self, request):
        remote = self._get_remote(request)
        logger.info('Client connect: {}'.format(remote))
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.clients.add(ws)

        try:
            # Catch-up client with buffer
            if self.buffer:
                await ws.send_bytes(self.buffer)

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.on_receive(msg.data)
                else:
                    logger.warning('Unknown message type: {}'.format(msg.type))
        finally:
            self.clients.remove(ws)
            logger.info('Client disconnect: {}'.format(remote))

        return ws

    def _get_remote(self, request):
        peername = request.transport.get_extra_info('peername')
        if peername is not None:
            return ':'.join(map(str, peername))
        else:
            return 'Unknown'


class WebCommandServer(WebSocketServer):

    DEFAULT_WAIT_TIME = 5  # seconds

    def __init__(self, *args, command=[], wait_time=DEFAULT_WAIT_TIME, **kwargs):
        super().__init__(*args, **kwargs)
        self.command = command
        self.wait_time = wait_time
        self.process = None
        self.app.on_startup.append(self._startup)
        self.app.on_cleanup.append(self._cleanup)

    async def _startup(self, app):
        if self.command:
            self._loop_task = self.loop.create_task(self._loop_command())
        else:
            self._loop_task = None
        self._stdin_task = self.loop.create_task(self._send_stdin_to_process())

    async def _cleanup(self, app):
        if self.process:
            logger.debug(
                'Terminate process pid={}'.format(self.process.pid))
            self.process.terminate(force=True)
            self.process = None
        if self._loop_task:
            self._loop_task.cancel()
            self._loop_task = None
        if self._stdin_task:
            self._stdin_task.cancel()
            self._stdin_task = None

    async def _loop_command(self):
        while True:
            await self._run_command()
            logger.debug('Waiting {} seconds...'.format(self.wait_time))
            await asyncio.sleep(self.wait_time)

    async def _run_command(self):
        process = PtyProcess.spawn(self.command, echo=None)
        self.process = process
        logger.debug('Start process pid={}, command={}'.format(process.pid,
                                                               self.command))
        await self.send_alert('Process started.')
        await self._send_process_output()
        await self.send_alert('Process exited.')
        logger.debug('End process pid={}, exitstatus={}'.format(
            process.pid, process.exitstatus))
        if process.exitstatus != 0:
            logger.error('ERROR: Process exited with {}'.format(
                process.exitstatus))
        self.process = None

    async def _send_process_output(self):
        process = self.process
        event = asyncio.Event()
        data = None

        # non asyncio wrapping
        def reader():
            nonlocal data
            try:
                data = process.read(1024)
            except EOFError:
                # The following is potentially blocking
                process.wait()
                data = None
            event.set()
        self.loop.add_reader(process.fd, reader)

        while True:
            await event.wait()
            event.clear()
            if data is None:
                if process.exitstatus is None:
                    logger.warning('EOF reached on pid={}'.format(process.pid))
                break
            elif data != '':
                await self.send(data)

        # non-asyncio wrapping
        self.loop.remove_reader(process.fd)

    async def _send_stdin_to_process(self):
        stdin = asyncio.StreamReader(loop=self.loop)
        protocol = asyncio.StreamReaderProtocol(stdin)
        await self.loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            data = await stdin.read(1024)
            if data:
                if self.command:
                    if self.process:
                        self.process.write(data)
                        self.process.flush()
                else:
                    data = data.replace(b'\n', b'\r\n')
                    await self.send(data)
            else:
                break
        if self.process:
            self.process.sendeof()
        logger.debug('STDIN EOF')
