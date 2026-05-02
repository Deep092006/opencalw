#!/usr/bin/env python3
"""Simple web terminal UI on localhost using Tornado + Terminado."""

import argparse
import os

import tornado.ioloop
import tornado.web
import tornado.websocket
from terminado import TermSocket
try:
  from terminado.management import TerminalManager
except ImportError:
  try:
    from terminado.management import TermManager as TerminalManager
  except ImportError:
    from terminado.management import SingleTermManager as TerminalManager


INDEX_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Terminal UI</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@4.19.0/css/xterm.css" />
    <style>
      html, body { height: 100%; width: 100%; margin: 0; background: #0b0b0b; }
      #terminal { height: 100%; width: 100%; }
    </style>
  </head>
  <body>
    <div id="terminal"></div>
    <div id="status" style="position:fixed;bottom:8px;left:12px;color:#9aa0a6;font:12px/1.4 monospace;"></div>
    <script src="https://cdn.jsdelivr.net/npm/xterm@4.19.0/lib/xterm.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.5.0/lib/xterm-addon-fit.js"></script>
    <script>
      var status = document.getElementById("status");
      if (typeof Terminal === "undefined") {
        status.textContent = "Failed to load xterm.js";
        throw new Error("xterm.js not loaded");
      }

      var term = new Terminal({
        cursorBlink: true,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
        theme: { background: "#0b0b0b" }
      });
      var fitAddon = new FitAddon.FitAddon();
      term.loadAddon(fitAddon);
      term.open(document.getElementById("terminal"));
      fitAddon.fit();

      var protocol = location.protocol === "https:" ? "wss" : "ws";
      var ws = new WebSocket(protocol + "://" + location.host + "/websocket");

      ws.onopen = function () {
        status.textContent = "Connected";
        term.focus();
        // Send initial size
        ws.send(JSON.stringify(["set_size", term.rows, term.cols]));
        // Terminado expects ["stdin", data]
        term.onData(function (data) { ws.send(JSON.stringify(["stdin", data])); });
      };

      // Terminado sends ["stdout", data] or ["disconnect", ...]
      ws.onmessage = function (event) {
        var msg = JSON.parse(event.data);
        if (msg[0] === "stdout") { term.write(msg[1]); }
        else if (msg[0] === "disconnect") { status.textContent = "Shell exited"; }
      };

      ws.onerror = function () { status.textContent = "WebSocket error"; };
      ws.onclose = function () {
        status.textContent = "Disconnected";
        term.write("\\r\\n[Disconnected]\\r\\n");
      };

      window.addEventListener("resize", function () {
        fitAddon.fit();
        ws.send(JSON.stringify(["set_size", term.rows, term.cols]));
      });
    </script>
  </body>
</html>
"""

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/html")
        self.write(INDEX_HTML)


def main() -> None:
    parser = argparse.ArgumentParser(description="Terminal UI server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=9090, help="Bind port")
    parser.add_argument("--shell", default=os.environ.get("SHELL", "/bin/bash"), help="Shell to run")
    args = parser.parse_args()

    term_manager = TerminalManager(shell_command=[args.shell])

    app = tornado.web.Application(
      [
        (r"/", IndexHandler),
        (r"/websocket", TermSocket, {"term_manager": term_manager}),
        (r"/websocket/", TermSocket, {"term_manager": term_manager}),
      ]
    )
    app.listen(args.port, address=args.host)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
