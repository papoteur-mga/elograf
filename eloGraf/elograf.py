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
import eloGraf.confirm as confirm  # type: ignore
import eloGraf.custom as custom  # type: ignore
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
from eloGraf.nerd_controller import (  # type: ignore
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

def get_size(start_path=".") -> Tuple[float, str]:
    total_size: int = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    total: float = float(total_size)
    for unit in ("B", "Kb", "Mb", "Gb", "Tb"):
        if total < 1024:
            break
        total /= 1024
    return total, unit




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


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Handle --version first (no logging needed)
    if args.version:
        print(f"Elograf {version.__version__}")
        sys.exit(0)

    if args.loglevel is not None:
        numeric_level = getattr(logging, args.loglevel.upper(), None)
    else:
        numeric_level = logging.INFO
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % args.loglevel)
    logging.basicConfig(level=numeric_level, format='%(message)s')

    result = handle_model_commands(args, Settings())
    if result is not None:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        sys.exit(result.code)

    # Create minimal QApplication for IPC check
    app = QApplication(sys.argv)

    # Create IPC manager (will auto-select D-Bus or QLocalServer)
    ipc = create_ipc_manager("elograf")

    # Determine command to send
    command = choose_ipc_command(args)

    # If there's a command and instance is running, send command and exit
    if command and ipc.is_running():
        if ipc.send_command(command):
            print(f"✓ Command '{command}' sent successfully")
            return
        else:
            print(f"✗ Failed to send '{command}' command", file=sys.stderr)
            sys.exit(1)

    # If there's a command but no instance is running
    if command:
        if command == "exit":
            print("No running instance to exit")
            sys.exit(1)
        elif command == "end":
            print("No running instance to stop")
            sys.exit(1)
        # For 'begin', continue to launch the app

    # If trying to launch without command and instance already running
    if not command and ipc.is_running():
        print("Elograf is already running", file=sys.stderr)
        print("\nAvailable commands:")
        print("  elograf --begin        : Start dictation")
        print("  elograf --end          : Stop dictation")
        print("  elograf --suspend      : Suspend dictation")
        print("  elograf --resume       : Resume dictation")
        print("  elograf --exit         : Exit application")
        print("  elograf --list-models  : List available models")
        print("  elograf --set-model M  : Set active model to M")
        sys.exit(1)

    # Normal startup - create new instance
    app.setDesktopFileName("Elograf")
    # don't close application when closing setting window
    app.setQuitOnLastWindowClosed(False)
    LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
    locale = QLocale.system().name()
    qtTranslator = QTranslator()
    if qtTranslator.load(
        "qt_" + locale,
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
    ):
        app.installTranslator(qtTranslator)
    appTranslator = QTranslator()
    if appTranslator.load("elograf_" + locale, os.path.join(LOCAL_DIR, "translations")):
        app.installTranslator(appTranslator)

    # Note: We don't fork() here because Qt applications with D-Bus/system tray
    # don't work well with fork(). The application will run in the background
    # via the system tray icon.
    ipc_backend = "D-Bus" if ipc.supports_global_shortcuts() else "Local Sockets"
    logging.info(f"Elograf started (using {ipc_backend})")
    logging.info("Available commands:")
    logging.info("  elograf --begin        : Start dictation")
    logging.info("  elograf --end          : Stop dictation")
    logging.info("  elograf --suspend      : Suspend dictation")
    logging.info("  elograf --resume       : Resume dictation")
    logging.info("  elograf --exit         : Exit application")
    logging.info("  elograf --list-models  : List available models")
    logging.info("  elograf --set-model M  : Set active model to M")

    w = QWidget()
    trayIcon = SystemTrayIcon(
        QIcon(":/icons/elograf/24/nomicro.png"),
        args.begin if command == "begin" else False,
        ipc,
        w
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
    exit(exit_code)


if __name__ == "__main__":
    main()
