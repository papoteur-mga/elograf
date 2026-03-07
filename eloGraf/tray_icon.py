from __future__ import annotations

import logging
import os
from subprocess import Popen
from typing import Any, Dict, Optional, Tuple

from PyQt6.QtCore import QCoreApplication, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from eloGraf.dialogs import AdvancedUI
from eloGraf.dictation import CommandBuildError, build_dictation_command
from eloGraf.engine_manager import EngineManager
from eloGraf.ipc_manager import IPCManager
from eloGraf.stt_engine import STTController, STTProcessRunner
from eloGraf.status import DictationStatus
from eloGraf.settings import Settings
from eloGraf.pidfile import remove_pid_file
from eloGraf.state_machine import DictationStateMachine, IconState
from eloGraf.icon_factory import IconFactory

class SystemTrayIcon(QSystemTrayIcon):
    """Tray icon controller with model-aware tooltip."""

    @property
    def dictation_controller(self) -> Optional[STTController]:
        """Get current dictation controller."""
        return self._engine_manager.controller if hasattr(self, '_engine_manager') else None

    @property
    def dictation_runner(self) -> Optional[STTProcessRunner]:
        """Get current dictation runner."""
        return self._engine_manager.runner if hasattr(self, '_engine_manager') else None

    def _update_tooltip(self) -> None:
        tooltip_lines = ["EloGraf"]
        active_controller = self._engine_manager.controller

        if active_controller:
            tooltip_lines.append(active_controller.get_status_string())

        # Add device name if configured
        device_name = getattr(self.settings, 'deviceName', None)
        if device_name and device_name != "default":
            tooltip_lines.append(f"Device: {device_name}")

        self.setToolTip("\n".join(tooltip_lines))

    def __init__(self, icon: QIcon, start: bool, ipc: IPCManager, parent=None, temporary_engine: str = None) -> None:
        QSystemTrayIcon.__init__(self, icon, parent)
        self.settings = Settings()
        try:
            self.settings.load()
        except Exception as exc:
            logging.warning("Failed to load settings: %s", exc)
        self.ipc = ipc
        self.temporary_engine = temporary_engine
        if temporary_engine:
            logging.info(f"Using temporary STT engine: {temporary_engine}")
        self.direct_click_enabled = self.settings.directClick

        menu = QMenu(parent)

        self.toggleAction = menu.addAction(self.tr("Toggle dictation"))
        self.stopAction = menu.addAction(self.tr("Stop dictation"))
        self.toggleAction.triggered.connect(self.controller_toggle)
        self.stopAction.triggered.connect(self.end)
        self.toggleAction.setEnabled(True)
        self.stopAction.setEnabled(False)
        configAction = menu.addAction(self.tr("Configuration"))
        exitAction = menu.addAction(self.tr("Exit"))
        self.setContextMenu(menu)

        if self.direct_click_enabled:
            self.activated.connect(self.commute)

        self.state_machine = DictationStateMachine()
        self.state_machine.on_state = lambda state: self._apply_state(state.icon_state, state.dictating, state.suspended)
        exitAction.triggered.connect(self.exit)
        configAction.triggered.connect(self.config)
        self.nomicro = QIcon.fromTheme("microphone-sensitivity-muted")
        if self.nomicro.isNull():
            self.nomicro = QIcon(":/icons/elograf/24/nomicro.png")
        self.micro = QIcon.fromTheme("audio-input-microphone")
        if self.micro.isNull():
            self.micro = QIcon(":/icons/elograf/24/micro.png")

        self.icon_factory = IconFactory(self.micro, self.nomicro)
        self._current_icon_state = None

        self.setIcon(self.nomicro)

        # Setup engine manager
        self._engine_manager = EngineManager(
            self.settings,
            temporary_engine=temporary_engine,
            max_retries=5,
            retry_delay_ms=2000,
        )
        self._engine_manager.on_state_change = self._handle_dictation_state
        self._engine_manager.on_output = self._handle_dictation_output
        self._engine_manager.on_exit = self._handle_dictation_exit
        self._engine_manager.on_refresh_complete = self._update_action_states

        # Create initial engine
        self.dictation_timer = QTimer(self)
        self.dictation_timer.setInterval(200)
        self._engine_manager.create_engine()
        self.dictation_timer.timeout.connect(self._engine_manager.runner.poll)

        self.dictating = False
        self.suspended = False
        self._postcommand_ran = True
        self.state_machine.set_idle()
        self._update_action_states()
        self._update_tooltip()

        # Connect IPC command handler
        self.ipc.command_received.connect(self._handle_ipc_command)

        # Start IPC server
        if not self.ipc.start_server():
            logging.error("Failed to start IPC server")

        # Register global shortcuts if supported
        self._register_global_shortcuts()

        if start:
            self.dictate()
            self.dictating = True

    def _apply_state(self, icon_state: IconState, dictating: bool, suspended: bool) -> None:
        self.dictating = dictating
        self.suspended = suspended

        # Only update icon if state has changed
        if self._current_icon_state != icon_state:
            self.setIcon(self.icon_factory.get_icon(icon_state))
            self._current_icon_state = icon_state

        self._update_tooltip()
        # update toggle label
        if hasattr(self, "toggleAction"):
            if suspended:
                self.toggleAction.setText(self.tr("Resume dictation"))
            elif dictating:
                self.toggleAction.setText(self.tr("Suspend dictation"))
            else:
                self.toggleAction.setText(self.tr("Start dictation"))
        self._update_action_states()

    def _handle_dictation_state(self, status: DictationStatus) -> None:
        """Handle state changes from STT engine."""
        if status == DictationStatus.INITIALIZING:
            self.state_machine.set_loading()
        elif status == DictationStatus.LISTENING:
            self.state_machine.set_ready()
        elif status == DictationStatus.SUSPENDED:
            self.state_machine.set_suspended()
        elif status == DictationStatus.IDLE:
            self.state_machine.set_idle()
        elif status == DictationStatus.FAILED:
            logging.error("STT engine process failed")
            self.state_machine.set_idle()

    def _handle_dictation_output(self, line: str) -> None:
        logging.debug(f"STT engine: {line}")

    def _handle_dictation_exit(self, return_code: int) -> None:
        """Handle engine exit."""
        if self.dictation_timer.isActive():
            self.dictation_timer.stop()

        self.dictating = False
        self.suspended = False
        self.state_machine.set_idle()
        self._update_action_states()
        self._update_tooltip()
        self._run_postcommand_once()

        # Delegate retry logic to engine manager
        def on_fatal_error():
            logging.error("STT engine failed too many times; exiting application")
            QTimer.singleShot(0, lambda: QCoreApplication.exit(1))

        self._engine_manager.handle_exit(return_code, on_fatal_error=on_fatal_error)

    def _run_postcommand_once(self) -> None:
        if self._postcommand_ran:
            return

        if hasattr(self.settings, "postcommand") and self.settings.postcommand:
            try:
                Popen(self.settings.postcommand.split())
            except Exception as exc:
                logging.error("Failed to run postcommand: %s", exc)

        self._postcommand_ran = True

    def _update_action_states(self) -> None:
        """Update menu action states based on current dictation state."""
        state = getattr(self, "state_machine", None)
        snapshot = state.state if state else None

        if hasattr(self, "stopAction") and snapshot:
            self.stopAction.setEnabled(snapshot.dictating)

    def _register_global_shortcuts(self):
        """Register global keyboard shortcuts if IPC supports it"""
        if not self.ipc.supports_global_shortcuts():
            logging.debug("IPC does not support global shortcuts")
            return

        # Register begin shortcut
        if self.settings.beginShortcut:
            success = self.ipc.register_global_shortcut(
                "begin",
                self.settings.beginShortcut,
                self.begin
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.beginShortcut} -> begin")
            else:
                logging.warning(f"Failed to register global shortcut for 'begin'")

        # Register end shortcut
        if self.settings.endShortcut:
            success = self.ipc.register_global_shortcut(
                "end",
                self.settings.endShortcut,
                self.end
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.endShortcut} -> end")
            else:
                logging.warning(f"Failed to register global shortcut for 'end'")

        if self.settings.toggleShortcut:
            success = self.ipc.register_global_shortcut(
                "toggle",
                self.settings.toggleShortcut,
                self.controller_toggle
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.toggleShortcut} -> toggle")
            else:
                logging.warning("Failed to register global shortcut for 'toggle'")

        if self.settings.suspendShortcut:
            success = self.ipc.register_global_shortcut(
                "suspend",
                self.settings.suspendShortcut,
                self.suspend
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.suspendShortcut} -> suspend")
            else:
                logging.warning("Failed to register global shortcut for 'suspend'")

        if self.settings.resumeShortcut:
            success = self.ipc.register_global_shortcut(
                "resume",
                self.settings.resumeShortcut,
                self.resume
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.resumeShortcut} -> resume")
            else:
                logging.warning("Failed to register global shortcut for 'resume'")

    def _handle_ipc_command(self, command: str):
        """
        Handle commands received from other instances via IPC.

        Args:
            command: Command string (e.g., "begin", "end", "exit")
        """
        logging.info(f"Received IPC command: {command}")
        if command == "begin":
            self.begin()
        elif command == "end":
            self.end()
        elif command == "exit":
            self.exit()
        elif command == "suspend":
            self.suspend()
        elif command == "resume":
            self.resume()
        elif command == "toggle":
            self.controller_toggle()
        else:
            logging.warning(f"Unknown IPC command: {command}")

    def currentModel(self) -> Tuple[str, str]:
        return self.settings.current_model()

    def exit(self) -> None:
        """Clean exit: stop dictation, cleanup IPC, and exit"""
        logging.info("Exiting Elograf...")
        if self.dictating:
            self.stop_dictate()
        # Cleanup resources
        remove_pid_file()
        self.ipc.cleanup()
        QCoreApplication.exit()

    def dictate(self) -> None:
        model, location = self.currentModel()
        if model == "" or not location:
            self.show_config_dialog()
            model, location = self.currentModel()
            if not model or not location:
                logging.info("No model selected, exiting dictate.")
                self.state_machine.set_idle()
                return
        if not location:
            logging.warning("Selected model has no location configured")
            self.state_machine.set_idle()
            return
        logging.debug(f"Start dictation with model {model} located in {location}")
        if self.settings.precommand:
            parts = self.settings.precommand.split()
            if parts:
                Popen(parts)
        self._postcommand_ran = False
        try:
            cmd, env = build_dictation_command(self.settings, location)
        except CommandBuildError as exc:
            logging.warning("Failed to build STT command: %s", exc)
            self.state_machine.set_idle()
            self._postcommand_ran = True
            return
        logging.debug(
            "Starting STT engine with the command {}".format(" ".join(cmd))
        )
        # Switch icon to loading before starting the runner so an immediate
        # READY notification cannot be overwritten by our own state change.
        self.state_machine.set_loading()

        if not self.dictation_runner.start(cmd, env=env):
            self.state_machine.set_idle()
            self._postcommand_ran = True
            return

        if not self.dictation_timer.isActive():
            self.dictation_timer.start()
        self._update_tooltip()
        logging.info("Loading model, please wait...")

    def suspend(self) -> None:
        logging.debug("Suspend dictation")
        if self.suspended:
            logging.info("Dictation already suspended")
            return
        if self.dictation_runner.is_running():
            self.dictation_runner.suspend()
            self.state_machine.set_suspended()
        else:
            logging.info("No running dictation to suspend")

    def resume(self) -> None:
        logging.debug("Resume dictation")
        if not self.dictation_runner.is_running():
            logging.info("No dictation process to resume; starting a new one")
            self.state_machine.set_ready()
            self.dictate()
            return
        self.dictation_runner.resume()
        self.state_machine.set_ready()

    def stop_dictate(self) -> None:
        if self.dictation_runner.is_running():
            logging.debug("Stopping STT engine")
            self.dictation_runner.stop()
        self.state_machine.set_idle()

    def commute(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle direct click on tray icon when direct_click_enabled is True."""
        if reason != QSystemTrayIcon.ActivationReason.Trigger:
            return
        self.controller_toggle()

    def controller_toggle(self) -> None:
        action = self.state_machine.toggle()
        getattr(self, action)()

    def toggle(self) -> None:
        self.controller_toggle()

    def begin(self) -> None:
        """Start dictation"""
        logging.debug("Begin dictation")
        if self.suspended:
            self.resume()
            return
        if not self.state_machine.state.dictating:
            self.dictate()
        else:
            logging.info("Dictation already started")

    def end(self) -> None:
        """Stop dictation"""
        logging.debug("End dictation")
        if self.dictating:
            self.stop_dictate()
        self.state_machine.set_idle()

    def show_config_dialog(self) -> None:
        adv_window = AdvancedUI(self.settings)

        # General settings
        adv_window.ui.precommand.setText(self.settings.precommand)
        adv_window.ui.postcommand.setText(self.settings.postcommand)
        adv_window.ui.env.setText(self.settings.env)
        adv_window.ui.tool_cb.setCurrentText(self.settings.tool)
        adv_window.ui.keyboard_le.setText(self.settings.keyboard)
        index = adv_window.ui.deviceName.findData(self.settings.deviceName)
        if index >= 0:
            adv_window.ui.deviceName.setCurrentIndex(index)
        adv_window.ui.direct_click_cb.setChecked(self.settings.directClick)

        # Shortcuts
        adv_window.beginShortcut.setKeySequence(self.settings.beginShortcut)
        adv_window.endShortcut.setKeySequence(self.settings.endShortcut)
        adv_window.toggleShortcut.setKeySequence(self.settings.toggleShortcut)
        adv_window.suspendShortcut.setKeySequence(self.settings.suspendShortcut)
        adv_window.resumeShortcut.setKeySequence(self.settings.resumeShortcut)

        # Set STT engine and initial tab
        index = adv_window.ui.stt_engine_cb.findData(self.settings.sttEngine)
        if index >= 0:
            adv_window.ui.stt_engine_cb.setCurrentIndex(index)
            adv_window._on_stt_engine_changed(index)

        # Custom handling for dialog result with validation
        while True:
            if not adv_window.exec():
                return  # User clicked Cancel

            # User clicked OK - run validation
            from eloGraf.ui_generator import (
                validate_settings_from_tab,
                apply_validation_warnings,
                clear_validation_warnings
            )

            # Get current engine
            engine_data = adv_window.ui.stt_engine_cb.currentData()
            current_engine = engine_data if engine_data else "nerd-dictation"

            # Validate General tab
            from eloGraf.validators import validate_command_exists

            general_warnings = {}
            precommand_value = adv_window.ui.precommand.text()
            precommand_warning = validate_command_exists(precommand_value)
            if precommand_warning:
                general_warnings['precommand'] = precommand_warning

            postcommand_value = adv_window.ui.postcommand.text()
            postcommand_warning = validate_command_exists(postcommand_value)
            if postcommand_warning:
                general_warnings['postcommand'] = postcommand_warning

            # Validate current engine tab
            engine_tab = adv_window.engine_tabs.get(current_engine)
            engine_class = adv_window.engine_settings_classes.get(current_engine)

            engine_warnings = {}
            if engine_tab and engine_class:
                engine_warnings = validate_settings_from_tab(engine_tab, engine_class)

            # If no warnings, save and exit
            if not general_warnings and not engine_warnings:
                break

            # Show warnings visually
            if general_warnings:
                # Apply warnings to General tab fields
                for field_name, warning_message in general_warnings.items():
                    if field_name == 'precommand':
                        widget = adv_window.ui.precommand
                    elif field_name == 'postcommand':
                        widget = adv_window.ui.postcommand
                    else:
                        continue

                    widget.setStyleSheet("border: 2px solid red;")
                    original_tooltip = widget.toolTip()
                    warning_tooltip = f"⚠️ {warning_message}"
                    if original_tooltip:
                        warning_tooltip = f"{original_tooltip}\n\n{warning_tooltip}"
                    widget.setToolTip(warning_tooltip)

                # Add warning icon to General tab
                general_tab_index = adv_window.ui.tabWidget.indexOf(adv_window.ui.general_tab)
                if general_tab_index >= 0:
                    tab_text = adv_window.ui.tabWidget.tabText(general_tab_index)
                    if not tab_text.startswith("⚠️ "):
                        adv_window.ui.tabWidget.setTabText(general_tab_index, f"⚠️ {tab_text}")

            if engine_warnings:
                apply_validation_warnings(engine_tab, engine_warnings)
                adv_window.add_tab_warning_icon(engine_tab, True)

            # Ask user if they want to save anyway
            if adv_window.show_validation_warnings_dialog(
                general_warnings, engine_warnings, current_engine
            ):
                # User chose "Save Anyway" - clear warnings and proceed
                if general_warnings:
                    # Clear General tab warnings
                    for field_name in general_warnings.keys():
                        if field_name == 'precommand':
                            widget = adv_window.ui.precommand
                        elif field_name == 'postcommand':
                            widget = adv_window.ui.postcommand
                        else:
                            continue

                        widget.setStyleSheet("")
                        widget.setToolTip("")  # Clear tooltip

                    # Remove warning icon from General tab
                    general_tab_index = adv_window.ui.tabWidget.indexOf(adv_window.ui.general_tab)
                    if general_tab_index >= 0:
                        tab_text = adv_window.ui.tabWidget.tabText(general_tab_index)
                        if tab_text.startswith("⚠️ "):
                            adv_window.ui.tabWidget.setTabText(general_tab_index, tab_text[3:])

                if engine_warnings:
                    clear_validation_warnings(engine_tab, engine_class)
                    adv_window.add_tab_warning_icon(engine_tab, False)
                break

            # User chose "Cancel" - warnings stay visible, loop back to show dialog again

        # Save settings (only reached if validation passed or user clicked "Save Anyway")
        if True:  # Keep indentation consistent
            # General settings
            self.settings.precommand = adv_window.ui.precommand.text()
            self.settings.postcommand = adv_window.ui.postcommand.text()
            self.settings.env = adv_window.ui.env.text()
            self.settings.tool = adv_window.ui.tool_cb.currentText()
            self.settings.keyboard = adv_window.ui.keyboard_le.text()

            # Save device name - log for debugging
            current_data = adv_window.ui.deviceName.currentData()
            current_text = adv_window.ui.deviceName.currentText()
            logging.info(f"Saving device - currentData: {current_data}, currentText: {current_text}")
            device_data = current_data or current_text
            self.settings.deviceName = device_data if device_data else "default"
            logging.info(f"Final deviceName to save: {self.settings.deviceName}")

            self.settings.directClick = adv_window.ui.direct_click_cb.isChecked()

            # Shortcuts
            self.settings.beginShortcut = adv_window.beginShortcut.keySequence().toString()
            self.settings.endShortcut = adv_window.endShortcut.keySequence().toString()
            self.settings.toggleShortcut = adv_window.toggleShortcut.keySequence().toString()
            self.settings.suspendShortcut = adv_window.suspendShortcut.keySequence().toString()
            self.settings.resumeShortcut = adv_window.resumeShortcut.keySequence().toString()

            # STT Engine
            engine_data = adv_window.ui.stt_engine_cb.currentData()
            self.settings.sttEngine = engine_data if engine_data else "nerd-dictation"

            # Engine-specific settings from dynamic tabs
            from eloGraf.engine_settings_registry import get_all_engine_ids

            selected_engine = self.settings.sttEngine

            for engine_id in get_all_engine_ids():
                engine_settings = adv_window.get_engine_settings_dataclass(engine_id)
                if engine_settings is None:
                    continue
                try:
                    self.settings.update_from_dataclass(engine_settings)
                    self.settings.sttEngine = selected_engine
                except Exception as exc:  # pragma: no cover - defensive
                    logging.debug("Failed to update settings for %s: %s", engine_id, exc)

            self.settings.save()
            self.settings.load()

            # Update direct click connection if setting changed
            old_direct_click = self.direct_click_enabled
            self.direct_click_enabled = self.settings.directClick
            if old_direct_click != self.direct_click_enabled:
                try:
                    self.activated.disconnect(self.commute)
                except (TypeError, RuntimeError):
                    pass
                if self.direct_click_enabled:
                    self.activated.connect(self.commute)

            # Refresh engine with new settings
            self._engine_manager.refresh_engine(
                stop_callback=self.stop_dictate,
                poll_timer=self.dictation_timer
            )
            self._update_tooltip()

    def config(self) -> None:
        self.show_config_dialog()

    def setModel(self, model: str) -> None:
        self.settings.setValue("Model/name", model)
        if self.dictating:
            logging.debug("Reload dictate process")
            self.stop_dictate()
            self.dictate()
