#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Pablo Caro

ABOUTME: Tests for dialog functions including PulseAudio device discovery
ABOUTME: Validates audio device enumeration and selection
"""
from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock
from subprocess import CompletedProcess

from eloGraf.dialogs import get_pulseaudio_sources


class TestGetPulseAudioSources(unittest.TestCase):
    def test_parse_pactl_output(self):
        """Test parsing of pactl list sources output."""
        mock_output = """Source #0
	State: RUNNING
	Name: alsa_output.pci-0000_00_1b.0.analog-stereo.monitor
	Description: Monitor of Built-in Audio Analog Stereo
	Driver: PipeWire
	Sample Specification: float32le 2ch 48000Hz

Source #1
	State: SUSPENDED
	Name: alsa_input.pci-0000_00_1b.0.analog-stereo
	Description: Built-in Audio Analog Stereo
	Driver: PipeWire
	Sample Specification: float32le 2ch 48000Hz
"""

        with patch('eloGraf.dialogs.run') as mock_run:
            mock_run.return_value = CompletedProcess(
                args=['pactl', 'list', 'sources'],
                returncode=0,
                stdout=mock_output,
                stderr=''
            )

            sources = get_pulseaudio_sources()

            self.assertEqual(len(sources), 2)
            self.assertEqual(sources[0][0], "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor")
            self.assertEqual(sources[0][1], "Monitor of Built-in Audio Analog Stereo")
            self.assertEqual(sources[1][0], "alsa_input.pci-0000_00_1b.0.analog-stereo")
            self.assertEqual(sources[1][1], "Built-in Audio Analog Stereo")

    def test_pactl_not_found(self):
        """Test handling when pactl is not installed."""
        with patch('eloGraf.dialogs.run', side_effect=FileNotFoundError):
            sources = get_pulseaudio_sources()
            self.assertEqual(sources, [])

    def test_pactl_timeout(self):
        """Test handling when pactl times out."""
        with patch('eloGraf.dialogs.run', side_effect=TimeoutError):
            sources = get_pulseaudio_sources()
            self.assertEqual(sources, [])

    def test_pactl_failure(self):
        """Test handling when pactl returns error."""
        with patch('eloGraf.dialogs.run') as mock_run:
            mock_run.return_value = CompletedProcess(
                args=['pactl', 'list', 'sources'],
                returncode=1,
                stdout='',
                stderr='Connection failed'
            )

            sources = get_pulseaudio_sources()
            self.assertEqual(sources, [])

    def test_empty_output(self):
        """Test handling of empty pactl output."""
        with patch('eloGraf.dialogs.run') as mock_run:
            mock_run.return_value = CompletedProcess(
                args=['pactl', 'list', 'sources'],
                returncode=0,
                stdout='',
                stderr=''
            )

            sources = get_pulseaudio_sources()
            self.assertEqual(sources, [])


if __name__ == '__main__':
    unittest.main()
