#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-Bus implementation for IPC with global shortcuts support

Linux/Unix implementation using D-Bus for communication and
KGlobalAccel for global keyboard shortcuts.

@author: papoteur
@license: GPL v3.0
"""

import logging
from typing import Dict, Callable
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusReply
from eloGraf.ipc_manager import IPCManager


class IPCDBus(IPCManager):
    """
    IPC implementation using D-Bus.

    Provides D-Bus service registration for single instance detection
    and command communication. Also supports global keyboard shortcuts
    via KGlobalAccel on KDE.
    """

    def __init__(self, app_id: str = "elograf"):
        super().__init__(app_id)
        self.dbus_service = f"org.{app_id}.daemon"
        self.dbus_path = f"/{app_id}"
        self.registered = False
        self.shortcuts = {}  # action -> callback mapping

    def is_running(self) -> bool:
        """
        Check if another instance is running via D-Bus.

        Returns:
            True if service is already registered on D-Bus
        """
        bus = QDBusConnection.sessionBus()
        iface = QDBusInterface(
            self.dbus_service,
            self.dbus_path,
            "",
            bus
        )
        return iface.isValid()

    def start_server(self) -> bool:
        """
        Register D-Bus service to receive commands.

        Returns:
            True if service was registered successfully
        """
        if self.registered:
            return True

        bus = QDBusConnection.sessionBus()

        # Register service
        if not bus.registerService(self.dbus_service):
            error_msg = bus.lastError().message()
            logging.error(f"Failed to register D-Bus service: {error_msg}")
            return False

        # Register object with all slots exported
        if not bus.registerObject(
            self.dbus_path,
            self,
            QDBusConnection.RegisterOption.ExportAllSlots
        ):
            error_msg = bus.lastError().message()
            logging.error(f"Failed to register D-Bus object: {error_msg}")
            return False

        self.registered = True
        logging.debug(f"D-Bus service '{self.dbus_service}' registered successfully")
        return True

    def send_command(self, command: str) -> bool:
        """
        Send command to running instance via D-Bus.

        Args:
            command: Command string (e.g., "begin", "end")

        Returns:
            True if command was sent successfully
        """
        bus = QDBusConnection.sessionBus()
        iface = QDBusInterface(
            self.dbus_service,
            self.dbus_path,
            "",
            bus
        )

        if not iface.isValid():
            logging.error(f"Cannot connect to D-Bus service: {bus.lastError().message()}")
            return False

        # Call the remote method
        reply = iface.call(command)

        if reply.errorName():
            logging.error(f"D-Bus call failed: {reply.errorMessage()}")
            return False

        logging.debug(f"Command '{command}' sent via D-Bus")
        return True

    @pyqtSlot()
    def begin(self):
        """D-Bus slot for 'begin' command"""
        logging.debug("D-Bus: begin command received")
        self.command_received.emit("begin")

    @pyqtSlot()
    def end(self):
        """D-Bus slot for 'end' command"""
        logging.debug("D-Bus: end command received")
        self.command_received.emit("end")

    def supports_global_shortcuts(self) -> bool:
        """
        D-Bus implementation supports global shortcuts via KGlobalAccel.

        Returns:
            True
        """
        return True

    def register_global_shortcut(
        self,
        action: str,
        shortcut: str,
        callback: Callable
    ) -> bool:
        """
        Register global keyboard shortcut using KGlobalAccel.

        Args:
            action: Action identifier (e.g., "begin", "end")
            shortcut: Keyboard shortcut (e.g., "Meta+Alt+D")
            callback: Function to call when shortcut is pressed

        Returns:
            True if shortcut was registered successfully
        """
        bus = QDBusConnection.sessionBus()

        # Check if KGlobalAccel is available
        iface = QDBusInterface(
            "org.kde.kglobalaccel",
            "/kglobalaccel",
            "org.kde.KGlobalAccel",
            bus
        )

        if not iface.isValid():
            logging.warning("KGlobalAccel not available - cannot register global shortcuts")
            return False

        component = self.app_id
        unique_name = f"{action}_dictation"
        friendly_name = f"{action.capitalize()} dictation"

        # Register shortcut with KGlobalAccel
        reply = iface.call(
            "setShortcut",
            component,
            unique_name,
            [shortcut],
            friendly_name,
            0  # flags
        )

        if reply.errorName():
            logging.error(f"Failed to register shortcut: {reply.errorMessage()}")
            return False

        # Store callback
        self.shortcuts[unique_name] = callback

        # Connect to signal when shortcut is activated
        bus.connect(
            "org.kde.kglobalaccel",
            f"/component/{component}",
            "org.kde.kglobalaccel.Component",
            "globalShortcutPressed",
            self._on_global_shortcut
        )

        logging.info(f"Global shortcut '{shortcut}' registered for action '{action}'")
        return True

    def _on_global_shortcut(self, component: str, unique_name: str):
        """
        Handle global shortcut activation from KGlobalAccel.

        Args:
            component: Component name
            unique_name: Unique action identifier
        """
        logging.debug(f"Global shortcut activated: {component}/{unique_name}")

        if unique_name in self.shortcuts:
            callback = self.shortcuts[unique_name]
            callback()
        else:
            logging.warning(f"No callback registered for shortcut: {unique_name}")

    def cleanup(self):
        """Cleanup D-Bus resources"""
        if self.registered:
            bus = QDBusConnection.sessionBus()
            bus.unregisterObject(self.dbus_path)
            bus.unregisterService(self.dbus_service)
            logging.debug("D-Bus service unregistered")
