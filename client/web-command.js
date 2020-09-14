import { Terminal } from 'xterm';
import { AttachAddon } from 'xterm-addon-attach';
import { FitAddon } from 'xterm-addon-fit';

window.attachWebCommandConsole = function(node) {

    const reconnectTimeout = 5000; // ms
    const wsRemoteHost = 'ws' + String(window.location).substring(4) + 'ws';
    const terminal = new Terminal();

    function alert(text) {
        terminal.write('\x1B[33;1m' + text + '\x1B[0m');
    }

    function connect() {
        let ws = new WebSocket(wsRemoteHost);
        ws.onerror = function(event) {
            alert('websocket error.\r\n');
        };
        ws.onopen = function() {
            alert('connected.\r\n');
        };
        ws.onclose = function() {
            alert('Disconnected.\r\n');
            attachAddon.dispose();
            window.setTimeout(function() {
                alert('Reconnecting...');
                connect();
            }, reconnectTimeout);
        };

        alert('Connecting to ' + wsRemoteHost + '...');
        const attachAddon = new AttachAddon(ws);
        terminal.loadAddon(attachAddon);
    }

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.open(node);
    fitAddon.fit();

    window.addEventListener('resize', function() {
        fitAddon.fit();
    });

    connect();
};
