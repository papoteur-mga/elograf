#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 08:15:47 2021

@author: papoteur
@license: GPL v3.0
"""

import sys
import os
import re
import shlex
import urllib.request, urllib.error
import logging
import argparse
import signal
from pathlib import Path
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem, QInputMethod
from PyQt6.QtCore import (
    QCoreApplication,
    QDir,
    QLibraryInfo,
    QLocale,
    QModelIndex,
    QSettings,
    QSize,
    Qt,
    QTranslator,
    QTimer,
    pyqtSlot,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QMenu,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSystemTrayIcon,
    QTableWidget,
    QVBoxLayout,
    QWidget,
    QTableView,
)
from subprocess import Popen, run
from zipfile import ZipFile
import eloGraf.elograf_rc  # type: ignore
import eloGraf.advanced as advanced  # type: ignore
import eloGraf.version as version  # type: ignore
from eloGraf.settings import DEFAULT_RATE, Settings
from eloGraf.model_repository import (
    MODEL_GLOBAL_PATH,
    MODEL_LIST,
    MODEL_USER_PATH,
    MODELS_URL,
    download_model_archive,
    download_model_list,
    ensure_user_model_dir,
    filter_available_models,
    get_size,
    load_model_index,
    model_list_path,
)
from eloGraf.engines.nerd.controller import (  # type: ignore
    NerdDictationController,
    NerdDictationProcessRunner,
    NerdDictationState,
)
from eloGraf.cli import build_parser, choose_ipc_command, handle_model_commands
from eloGraf.ipc_manager import create_ipc_manager, IPCManager  # type: ignore

from eloGraf.tray_icon import SystemTrayIcon
from eloGraf.pidfile import remove_pid_file, write_pid_file

# Types.
from typing import (
    Any,
    Tuple,
    List,
    Dict,
    Optional,
)






def setup_signal_handlers(tray_icon):
    """
    Setup signal handlers for graceful shutdown.

    Handles SIGTERM, SIGINT (Ctrl+C), and SIGHUP.
    Uses a flag-based approach with QTimer to check for signals.
    """
    # Flag to track if we should exit
    tray_icon._should_exit = False

    def signal_handler(signum, frame):
        """Set exit flag when signal is received"""
        sig_name = signal.Signals(signum).name
        logging.info(f"Received signal {sig_name}, will exit on next timer check...")
        tray_icon._should_exit = True

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)  # kill command
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)  # Terminal hangup

    # Timer to periodically check if we should exit
    def check_exit_flag():
        if tray_icon._should_exit:
            logging.info("Exiting due to signal...")
            tray_icon.exit()

    timer = QTimer()
    timer.timeout.connect(check_exit_flag)
    timer.start(200)  # Check every 200ms
    tray_icon._exit_timer = timer  # Keep reference to prevent garbage collection


class ColoredFormatter(logging.Formatter):
    """Logging Formatter to add colors to terminal output."""

    # ANSI escape sequences for colors
    GREY = "\x1b[38;21m"
    YELLOW = "\x1b[33;21m"
    RED = "\x1b[31;21m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"
    FORMAT = "%(message)s"

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: RESET + FORMAT + RESET,  # Standard color for INFO
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(args: argparse.Namespace) -> None:
    """Configure logging based on command-line arguments."""
    if args.loglevel is not None:
        numeric_level = getattr(logging, args.loglevel.upper(), None)
    else:
        numeric_level = logging.INFO
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % args.loglevel)
    
    # Configure root logger with custom colored formatter
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(handler)


def handle_cli_commands_and_exit_if_needed(args: argparse.Namespace, ipc: IPCManager) -> None:
    """
    Handles CLI commands, either by executing them directly or sending them to a running instance.
    Exits the application if a command is sent, if an instance is already running, or after a model command.
    """
    # Handle model commands first as they don't require a running instance
    result = handle_model_commands(args, Settings())
    if result is not None:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        sys.exit(result.code)

    command = choose_ipc_command(args)

    # If there's a command and an instance is running, send command and exit
    if command and ipc.is_running():
        if ipc.send_command(command):
            print(f"✓ Command '{command}' sent successfully")
            sys.exit(0)
        else:
            print(f"✗ Failed to send '{command}' command", file=sys.stderr)
            sys.exit(1)

    # If there's a command but no instance is running
    if command:
        if command in ("exit", "end"):
            print(f"No running instance to {command}")
            sys.exit(1)
        # For 'begin', continue to launch the app

    # If trying to launch without command and an instance is already running
    if not command and ipc.is_running():
        print("Elograf is already running", file=sys.stderr)
        print("\nAvailable commands:")
        print("  elograf --begin         : Start dictation")
        print("  elograf --end           : Stop dictation")
        print("  elograf --suspend       : Suspend dictation")
        print("  elograf --resume        : Resume dictation")
        print("  elograf --exit          : Exit application")
        print("  elograf --list-models   : List available models")
        print("  elograf --set-model M   : Set active model to M")
        print("  elograf --list-engines  : List available STT engines")
        print("  elograf --use-engine E  : Use STT engine E for this session")
        sys.exit(1)


def setup_application(app: QApplication) -> None:
    """Configure and prepare the QApplication instance."""
    app.setDesktopFileName("Elograf")
    # don't close application when closing setting window
    app.setQuitOnLastWindowClosed(False)
    LOCAL_DIR = Path(__file__).resolve().parent
    locale_name = QLocale.system().name()  # e.g., es_ES
    locale_lang = locale_name.split('_')[0]   # e.g., es

    qtTranslator = QTranslator()
    if qtTranslator.load(
        "qt_" + locale_name,
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
    ):
        app.installTranslator(qtTranslator)

    appTranslator = QTranslator()
    path = str(LOCAL_DIR / "translations")

    # Try specific locale first (e.g., elograf_es_ES.qm), then generic (elograf_es.qm)
    loaded = appTranslator.load("elograf_" + locale_name, path)
    if not loaded:
        loaded = appTranslator.load("elograf_" + locale_lang, path)

    if loaded:
        app.installTranslator(appTranslator)
    else:
        logging.warning("No translation file found for locale '%s' or language '%s'", locale_name, locale_lang)


def run_application(app: QApplication, args: argparse.Namespace, ipc: IPCManager) -> None:
    """Run the main application event loop."""
    ipc_backend = "D-Bus" if ipc.supports_global_shortcuts() else "Local Sockets"
    logging.info(f"Elograf started (using {ipc_backend})")
    logging.info("Available commands:")
    logging.info("  elograf --begin         : Start dictation")
    logging.info("  elograf --end           : Stop dictation")
    logging.info("  elograf --suspend       : Suspend dictation")
    logging.info("  elograf --resume        : Resume dictation")
    logging.info("  elograf --exit          : Exit application")
    logging.info("  elograf --list-models   : List available models")
    logging.info("  elograf --set-model M   : Set active model to M")
    logging.info("  elograf --list-engines  : List available STT engines")
    logging.info("  elograf --use-engine E  : Use STT engine E for this session")

    command = choose_ipc_command(args)
    w = QWidget()
    trayIcon = SystemTrayIcon(
        QIcon(":/icons/elograf/24/nomicro.png"),
        args.begin if command == "begin" else False,
        ipc,
        w,
        temporary_engine=args.use_engine if hasattr(args, 'use_engine') and args.use_engine else None
    )

    # Setup signal handlers for graceful shutdown
    setup_signal_handlers(trayIcon)

    # Write PID file for daemon management
    write_pid_file()

    trayIcon.show()
    exit_code = app.exec()

    # Ensure cleanup on exit
    remove_pid_file()
    trayIcon.ipc.cleanup()
    sys.exit(exit_code)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"Elograf {version.__version__}")
        sys.exit(0)

    setup_logging(args)

    app = QApplication(sys.argv)
    ipc = create_ipc_manager("elograf")

    handle_cli_commands_and_exit_if_needed(args, ipc)

    # Normal startup - create new instance
    setup_application(app)
    run_application(app, args, ipc)


if __name__ == "__main__":
    main()
