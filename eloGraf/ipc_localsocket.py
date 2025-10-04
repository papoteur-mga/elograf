#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QLocalServer/QLocalSocket implementation for IPC

Cross-platform implementation using Qt's local sockets.
Works on Windows, Linux, and macOS.

@author: papoteur
@license: GPL v3.0
"""

import logging
from PyQt6.QtCore import QSharedMemory, QIODevice
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from eloGraf.ipc_manager import IPCManager


class IPCLocalSocket(IPCManager):
    """
    IPC implementation using QLocalServer and QLocalSocket.

    Uses QSharedMemory to detect running instances and QLocalServer
    for command communication between instances.
    """

    def __init__(self, app_id: str = "elograf"):
        super().__init__(app_id)
        self.shared_memory = QSharedMemory(app_id)
        self.server = None

    def is_running(self) -> bool:
        """
        Check if another instance is running using shared memory.

        Returns:
            True if another instance is detected
        """
        # Try to attach to existing shared memory
        if self.shared_memory.attach():
            self.shared_memory.detach()
            return True

        # Try to create new shared memory
        if self.shared_memory.create(1):
            return False  # We're the first instance

        # Creation failed - another instance exists
        return True

    def start_server(self) -> bool:
        """
        Start local server to receive commands from other instances.

        Returns:
            True if server started successfully
        """
        if self.server is not None:
            return True

        # Remove any stale server
        QLocalServer.removeServer(self.app_id)

        self.server = QLocalServer()
        if not self.server.listen(self.app_id):
            logging.error(f"Cannot start local server: {self.server.errorString()}")
            return False

        # Connect signal for new connections
        self.server.newConnection.connect(self._on_new_connection)
        logging.debug(f"Local server started on '{self.app_id}'")
        return True

    def _on_new_connection(self):
        """Handle incoming connection from another instance"""
        client_socket = self.server.nextPendingConnection()
        if not client_socket:
            return

        # Wait for data to be ready
        client_socket.readyRead.connect(
            lambda: self._on_client_data(client_socket)
        )

        # Cleanup when disconnected
        client_socket.disconnected.connect(client_socket.deleteLater)

    def _on_client_data(self, socket: QLocalSocket):
        """
        Read and process command from client.

        Args:
            socket: Client socket with data ready
        """
        data = socket.readAll().data().decode('utf-8').strip()
        logging.debug(f"Received command via QLocalSocket: {data}")

        # Emit signal for command handling
        self.command_received.emit(data)

        # Send acknowledgment
        socket.write(b"OK")
        socket.flush()
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()

    def send_command(self, command: str) -> bool:
        """
        Send command to running instance.

        Args:
            command: Command string to send (e.g., "begin", "end")

        Returns:
            True if command was sent successfully
        """
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)

        # Wait for connection (1 second timeout)
        if not socket.waitForConnected(1000):
            logging.error(f"Cannot connect to server: {socket.errorString()}")
            return False

        # Send command
        socket.write(command.encode('utf-8'))
        socket.flush()

        # Wait for response
        if socket.waitForReadyRead(1000):
            response = socket.readAll().data().decode('utf-8')
            logging.debug(f"Server response: {response}")
            socket.disconnectFromServer()
            return True
        else:
            logging.error("Timeout waiting for server response")
            socket.disconnectFromServer()
            return False

    def supports_global_shortcuts(self) -> bool:
        """
        QLocalSocket implementation does not support global shortcuts.

        Returns:
            False
        """
        return False

    def cleanup(self):
        """Cleanup resources before shutdown"""
        if self.server:
            self.server.close()
            logging.debug("Local server closed")

        if self.shared_memory.isAttached():
            self.shared_memory.detach()
            logging.debug("Shared memory detached")
