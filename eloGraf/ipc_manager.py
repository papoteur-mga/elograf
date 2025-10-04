#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inter-Process Communication (IPC) Manager for Elograf

Provides an abstraction layer for communication between Elograf instances
with multiple implementations (D-Bus, QLocalServer) selected automatically.

@author: papoteur
@license: GPL v3.0
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


# Custom metaclass that combines QObject's metaclass with ABCMeta
class QABCMeta(type(QObject), ABCMeta):
    pass


class IPCManager(QObject, metaclass=QABCMeta):
    """
    Abstract base class for inter-process communication.

    Signals:
        command_received: Emitted when a command is received from another instance
    """

    command_received = pyqtSignal(str)  # command name

    def __init__(self, app_id: str = "elograf"):
        super().__init__()
        self.app_id = app_id

    @abstractmethod
    def is_running(self) -> bool:
        """Check if another instance is already running"""
        pass

    @abstractmethod
    def start_server(self) -> bool:
        """Start server to receive commands (main instance only)"""
        pass

    @abstractmethod
    def send_command(self, command: str) -> bool:
        """Send command to running instance"""
        pass

    @abstractmethod
    def supports_global_shortcuts(self) -> bool:
        """Check if this implementation supports global keyboard shortcuts"""
        pass

    def register_global_shortcut(self, action: str, shortcut: str, callback) -> bool:
        """
        Register a global keyboard shortcut (if supported).

        Args:
            action: Action identifier (e.g., "begin", "end")
            shortcut: Keyboard shortcut (e.g., "Meta+Alt+D")
            callback: Function to call when shortcut is pressed

        Returns:
            True if shortcut was registered successfully
        """
        return False  # Default implementation does nothing

    def cleanup(self):
        """Cleanup resources before shutdown"""
        pass


def create_ipc_manager(app_id: str = "elograf") -> IPCManager:
    """
    Factory function to create the appropriate IPC manager.

    Tries to create D-Bus implementation first (if available),
    falls back to QLocalServer implementation.

    Args:
        app_id: Application identifier for IPC

    Returns:
        IPCManager instance (either IPCDBus or IPCLocalSocket)
    """
    # Try D-Bus first
    try:
        from eloGraf.ipc_dbus import IPCDBus
        logging.info("Using D-Bus for inter-process communication")
        return IPCDBus(app_id)
    except ImportError as e:
        logging.info(f"D-Bus not available ({e}), falling back to QLocalServer")
    except Exception as e:
        logging.warning(f"Failed to initialize D-Bus ({e}), falling back to QLocalServer")

    # Fallback to QLocalServer
    from eloGraf.ipc_localsocket import IPCLocalSocket
    logging.info("Using QLocalServer for inter-process communication")
    return IPCLocalSocket(app_id)
