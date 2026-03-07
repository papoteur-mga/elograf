# ABOUTME: Dynamic UI generation from dataclass field metadata.
# ABOUTME: Creates PyQt6 widgets based on field annotations for settings dialogs.

from __future__ import annotations

import dataclasses
import importlib
import typing
from typing import Any, Callable, List, Tuple, Type, get_type_hints
from dataclasses import Field
from PyQt6.QtWidgets import (
    QWidget,
    QLineEdit,
    QCheckBox,
    QComboBox,
    QSlider,
    QPushButton,
    QLabel,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt


def _load_function_from_string(function_path: str) -> Callable:
    """Dynamically load a function from a string path.

    Args:
        function_path: Full path to function (e.g., "module.submodule.function_name")

    Returns:
        The loaded function

    Raises:
        ImportError: If module cannot be imported
        AttributeError: If function doesn't exist in module
    """
    parts = function_path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid function path: {function_path}")

    module_path, function_name = parts
    module = importlib.import_module(module_path)
    return getattr(module, function_name)


def _populate_dropdown_from_function(
    combo: QComboBox,
    function_path: str,
    kwargs: dict | None = None
) -> None:
    """Populate a QComboBox from a dynamic choices function.

    Args:
        combo: QComboBox to populate
        function_path: String path to function returning List[Tuple[value, display]]
        kwargs: Optional kwargs to pass to the function
    """
    try:
        choices_function = _load_function_from_string(function_path)
        kwargs = kwargs or {}
        choices: List[Tuple[str, str]] = choices_function(**kwargs)

        combo.clear()
        for value, display in choices:
            combo.addItem(display, value)
    except Exception as e:
        # On error, add an error item so user knows something went wrong
        combo.clear()
        combo.addItem(f"Error loading choices: {e}", "")


def create_widget_from_field(field: Field, value: Any) -> QWidget:
    """Create a QWidget from a dataclass field's metadata.

    Args:
        field: Dataclass field with metadata describing the widget
        value: Current value for the field

    Returns:
        QWidget configured according to field metadata
    """
    metadata = field.metadata
    widget_type = metadata.get("widget", "text")

    if widget_type == "text":
        widget = QLineEdit()
        widget.setText(str(value) if value is not None else "")
        if metadata.get("readonly", False):
            widget.setReadOnly(True)
        if "tooltip" in metadata:
            # Style: black text on red background as requested
            tooltip_text = metadata["tooltip"]
            styled_tooltip = f"<html><body style='color: black; background-color: #ff4444; padding: 5px;'>\n{tooltip_text}\n</body></html>"
            widget.setToolTip(styled_tooltip)
        return widget

    elif widget_type == "password":
        widget = QLineEdit()
        widget.setEchoMode(QLineEdit.EchoMode.Password)
        widget.setText(str(value) if value is not None else "")
        if "tooltip" in metadata:
            # Style: black text on red background as requested
            tooltip_text = metadata["tooltip"]
            styled_tooltip = f"<html><body style='color: black; background-color: #ff4444; padding: 5px;'>\n{tooltip_text}\n</body></html>"
            widget.setToolTip(styled_tooltip)
        return widget

    elif widget_type == "checkbox":
        widget = QCheckBox()
        widget.setChecked(bool(value))
        if "tooltip" in metadata:
            # Style: black text on red background as requested
            tooltip_text = metadata["tooltip"]
            styled_tooltip = f"<html><body style='color: black; background-color: #ff4444; padding: 5px;'>\n{tooltip_text}\n</body></html>"
            widget.setToolTip(styled_tooltip)
        return widget

    elif widget_type == "dropdown":
        choices_function = metadata.get("choices_function")
        refreshable = metadata.get("refreshable", False)
        option_descriptions = metadata.get("option_descriptions", {})

        # Create the combo box
        combo = QComboBox()

        # Populate choices
        if choices_function:
            # Use dynamic function-based choices
            choices_kwargs = metadata.get("choices_function_kwargs", {})
            _populate_dropdown_from_function(combo, choices_function, choices_kwargs)
        else:
            # Use static options from metadata
            options = metadata.get("options", [])
            for option in options:
                # Build tooltip for this option if description exists
                if option in option_descriptions:
                    desc = option_descriptions[option]
                    combo.addItem(option, desc)
                else:
                    combo.addItem(option)

        # Set current value
        if value is not None:
            # Find item by data (value) not by text
            index = combo.findData(value)
            if index >= 0:
                combo.setCurrentIndex(index)
            elif not choices_function:
                # Fallback to text matching for old-style static options
                index = combo.findText(value)
                if index >= 0:
                    combo.setCurrentIndex(index)

        if "tooltip" in metadata:
            # Style: black text on red background as requested
            tooltip_text = metadata["tooltip"]
            styled_tooltip = f"<html><body style='color: black; background-color: #ff4444; padding: 5px;'>\n{tooltip_text}\n</body></html>"
            combo.setToolTip(styled_tooltip)
        elif option_descriptions:
            # Build a dynamic tooltip showing all options with descriptions
            tooltip_parts = ["<b>Available Options:</b>", "<ul>"]
            for option in options:
                desc = option_descriptions.get(option, "")
                tooltip_parts.append(f"<li><b>{option}:</b> {desc}</li>")
            tooltip_parts.append("</ul>")
            tooltip_html = "\n".join(tooltip_parts)
            styled_tooltip = f"<html><body style='color: black; background-color: #ff4444; padding: 5px;'>\n{tooltip_html}\n</body></html>"
            combo.setToolTip(styled_tooltip)

        # If refreshable, wrap in container with refresh button
        if refreshable and choices_function:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            refresh_button = QPushButton("🔄")
            refresh_button.setMaximumWidth(40)

            # Connect refresh button to reload choices
            def on_refresh():
                current_value = combo.currentData()
                _populate_dropdown_from_function(combo, choices_function, choices_kwargs)
                # Try to restore selection
                index = combo.findData(current_value)
                if index >= 0:
                    combo.setCurrentIndex(index)

            refresh_button.clicked.connect(on_refresh)

            layout.addWidget(combo)
            layout.addWidget(refresh_button)

            # Store combo reference for reading values later
            container.combo = combo  # type: ignore

            return container
        else:
            return combo

    elif widget_type == "slider":
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        slider = QSlider(Qt.Orientation.Horizontal)
        value_range = metadata.get("range", [0, 100])
        step = metadata.get("step", 1)

        slider.setMinimum(value_range[0])
        slider.setMaximum(value_range[1])
        slider.setSingleStep(step)
        slider.setValue(int(value) if value is not None else value_range[0])

        display_label = QLabel(str(value))
        slider.valueChanged.connect(lambda v: display_label.setText(str(v)))

        layout.addWidget(slider)
        layout.addWidget(display_label)

        if "tooltip" in metadata:
            # Style: black text on red background as requested
            tooltip_text = metadata["tooltip"]
            styled_tooltip = f"<html><body style='color: black; background-color: #ff4444; padding: 5px;'>\n{tooltip_text}\n</body></html>"
            slider.setToolTip(styled_tooltip)

        # Store references for later value reading
        container.slider = slider  # type: ignore
        container.display_label = display_label  # type: ignore

        return container

    elif widget_type == "action_button":
        button = QPushButton(metadata.get("button_text", "Action"))
        callback = metadata.get("on_click")
        if callback and callable(callback):
            button.clicked.connect(callback)
        if "tooltip" in metadata:
            # Style: black text on red background as requested
            tooltip_text = metadata["tooltip"]
            styled_tooltip = f"<html><body style='color: black; background-color: #ff4444; padding: 5px;'>\n{tooltip_text}\n</body></html>"
            button.setToolTip(styled_tooltip)
        return button

    else:
        # Default to text input
        widget = QLineEdit()
        widget.setText(str(value) if value is not None else "")
        return widget


def generate_settings_tab(settings_class: Type, instance: Any | None = None) -> QWidget:
    """Generate a complete settings tab from a dataclass.

    Args:
        settings_class: Dataclass type with field metadata

    Returns:
        QWidget containing a form layout with all fields
    """
    tab = QWidget()
    layout = QVBoxLayout(tab)

    # Add help text at the top
    help_label = QLabel(
        "<i>These settings are only used when this engine is selected in the General tab.</i>"
    )
    layout.addWidget(help_label)

    # Create form layout for fields
    form_layout = QFormLayout()
    form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    # Use provided instance or fall back to defaults
    settings_instance = instance if instance is not None else settings_class()

    # Store widgets for later value reading
    widgets_map = {}

    for field in dataclasses.fields(settings_class):
        # Skip fields without metadata or explicitly hidden/internal fields
        if not field.metadata or field.metadata.get("hidden"):
            continue

        # Get current value from instance
        default_value = getattr(settings_instance, field.name, None)

        # Create widget
        widget = create_widget_from_field(field, default_value)

        # Store widget reference
        widgets_map[field.name] = widget

        # Add to form
        label_text = field.metadata.get("label", field.name)

        # For action buttons, don't create a label/field pair, just add the button
        if field.metadata.get("widget") == "action_button":
            # Add button spanning both columns
            form_layout.addRow(widget)
        else:
            if "tooltip" in field.metadata:
                # Create a container for label + info icon
                label_container = QWidget()
                label_layout = QHBoxLayout(label_container)
                label_layout.setContentsMargins(0, 0, 0, 0)
                label_layout.setSpacing(4)
                
                label = QLabel(label_text)
                
                info_icon = QLabel("ⓘ")
                info_icon.setStyleSheet("color: #3498db; font-weight: bold;")
                # Style: black text on red background as requested
                tooltip_text = field.metadata["tooltip"]
                info_icon.setToolTip(f"<html><body style='color: black; background-color: #ff4444; padding: 5px;'>\n{tooltip_text}\n</body></html>")
                
                label_layout.addWidget(label)
                label_layout.addWidget(info_icon)
                label_layout.addStretch()
                
                form_layout.addRow(label_container, widget)
            else:
                label = QLabel(label_text)
                form_layout.addRow(label, widget)

    layout.addLayout(form_layout)
    layout.addStretch()

    # Store widgets map on tab for later access
    tab.widgets_map = widgets_map  # type: ignore

    return tab


def read_settings_from_tab(tab: QWidget, settings_class: Type) -> Any:
    """Read values from a settings tab and create a dataclass instance.

    Args:
        tab: QWidget created by generate_settings_tab
        settings_class: Dataclass type to instantiate

    Returns:
        Instance of settings_class with values from widgets
    """
    widgets_map = getattr(tab, 'widgets_map', {})
    values = {}

    # Get actual type hints (resolves string annotations)
    type_hints = get_type_hints(settings_class)

    for field in dataclasses.fields(settings_class):
        if field.name not in widgets_map:
            continue

        widget = widgets_map[field.name]
        widget_type = field.metadata.get("widget", "text")

        if widget_type in ("text", "password"):
            if isinstance(widget, QLineEdit):
                text_value = widget.text()
                # Get actual type from type_hints
                field_type = type_hints.get(field.name, str)

                # Handle Optional types
                if hasattr(field_type, '__origin__'):
                    # This is a generic type like Optional[str]
                    if field_type.__origin__ is typing.Union:
                        # Get the non-None type
                        field_type = next((t for t in field_type.__args__ if t is not type(None)), str)

                if field_type == int:
                    values[field.name] = int(text_value) if text_value else 0
                elif field_type == float:
                    values[field.name] = float(text_value) if text_value else 0.0
                else:
                    values[field.name] = text_value

        elif widget_type == "checkbox":
            if isinstance(widget, QCheckBox):
                values[field.name] = widget.isChecked()

        elif widget_type == "dropdown":
            # Check if it's a refreshable container or direct combo box
            if hasattr(widget, 'combo'):
                # Refreshable container widget
                values[field.name] = widget.combo.currentData() or widget.combo.currentText()
            elif isinstance(widget, QComboBox):
                # Direct combo box - try currentData first, fallback to currentText
                values[field.name] = widget.currentData() or widget.currentText()

        elif widget_type == "slider":
            # Widget is a container with slider attribute
            if hasattr(widget, 'slider'):
                values[field.name] = widget.slider.value()

    return settings_class(**values)


def _get_widget_value(widget: QWidget, field: dataclasses.Field) -> Any:
    """Extract current value from a widget based on its type.

    Args:
        widget: The widget to extract value from
        field: The dataclass field (for type information)

    Returns:
        Current value from the widget
    """
    widget_type = field.metadata.get("widget", "text")

    if widget_type in ("text", "password"):
        if isinstance(widget, QLineEdit):
            return widget.text()

    elif widget_type == "checkbox":
        if isinstance(widget, QCheckBox):
            return widget.isChecked()

    elif widget_type == "dropdown":
        # Check if it's a refreshable container or direct combo box
        if hasattr(widget, 'combo'):
            return widget.combo.currentData() or widget.combo.currentText()
        elif isinstance(widget, QComboBox):
            return widget.currentData() or widget.currentText()

    elif widget_type == "slider":
        if hasattr(widget, 'slider'):
            return widget.slider.value()

    return None


def validate_settings_from_tab(
    tab_widget: QWidget,
    settings_class: Type
) -> dict[str, str]:
    """Validate all fields in a settings tab.

    Args:
        tab_widget: The tab widget containing the settings fields
        settings_class: The dataclass defining the settings

    Returns:
        Dictionary mapping field_name -> warning_message for any warnings found
    """
    warnings = {}

    for field in dataclasses.fields(settings_class):
        validate_func_path = field.metadata.get("validate")
        if not validate_func_path:
            continue

        try:
            # Load validator function
            validate_func = _load_function_from_string(validate_func_path)

            # Get current value from widget
            widget = getattr(tab_widget, "widgets_map", {}).get(field.name)
            if not widget:
                continue

            value = _get_widget_value(widget, field)

            # Run validation
            warning = validate_func(value)
            if warning:
                warnings[field.name] = warning

        except Exception as e:
            # Log error but don't block validation of other fields
            import logging
            logging.warning(f"Validation error for field {field.name}: {e}")

    return warnings


def apply_validation_warnings(
    tab_widget: QWidget,
    warnings: dict[str, str]
) -> None:
    """Apply visual feedback for validation warnings.

    Args:
        tab_widget: The tab containing fields with warnings
        warnings: Dictionary of field_name -> warning_message
    """
    for field_name, warning_message in warnings.items():
        widget = getattr(tab_widget, "widgets_map", {}).get(field_name)
        if not widget:
            continue

        # Get the actual input widget (handle refreshable containers)
        input_widget = widget.combo if hasattr(widget, 'combo') else widget

        # Apply red border
        input_widget.setStyleSheet("border: 2px solid red;")

        # Set tooltip with warning
        original_tooltip = input_widget.toolTip()
        warning_tooltip = f"⚠️ {warning_message}"
        if original_tooltip:
            warning_tooltip = f"{original_tooltip}\n\n{warning_tooltip}"
        input_widget.setToolTip(warning_tooltip)


def clear_validation_warnings(
    tab_widget: QWidget,
    settings_class: Type
) -> None:
    """Clear all validation warning visuals from a tab.

    Args:
        tab_widget: The tab to clear warnings from
        settings_class: The dataclass defining the settings
    """
    for field in dataclasses.fields(settings_class):
        widget = getattr(tab_widget, "widgets_map", {}).get(field.name)
        if not widget:
            continue

        input_widget = widget.combo if hasattr(widget, 'combo') else widget

        # Clear custom stylesheet
        input_widget.setStyleSheet("")

        # Restore original tooltip from metadata
        original_tooltip = field.metadata.get("tooltip", "")
        input_widget.setToolTip(original_tooltip)
