"""Tests for VoskLocal settings integration with Settings class."""
import pytest
from unittest.mock import MagicMock, patch


def test_settings_has_vosk_properties():
    """Settings debe tener todas las propiedades de Vosk."""
    from eloGraf.settings import Settings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        
        # Verificar que existen las propiedades
        assert hasattr(settings, 'voskModelPath')
        assert hasattr(settings, 'voskVadType')
        assert hasattr(settings, 'voskVadThreshold')
        assert hasattr(settings, 'voskSilenceTimeoutMs')
        assert hasattr(settings, 'voskSampleRate')
        assert hasattr(settings, 'voskPartialResults')
        assert hasattr(settings, 'voskTextFormatting')
        assert hasattr(settings, 'voskLocale')
        assert hasattr(settings, 'voskMaxQueueDepth')


def test_settings_vosk_defaults():
    """Verificar valores por defecto de propiedades Vosk."""
    from eloGraf.settings import Settings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        
        assert settings.voskModelPath == ""
        assert settings.voskVadType == "silero"
        assert settings.voskVadThreshold == 0.5
        assert settings.voskSilenceTimeoutMs == 500
        assert settings.voskSampleRate == 16000
        assert settings.voskPartialResults == False
        assert settings.voskTextFormatting == True
        assert settings.voskLocale == "en_US"
        assert settings.voskMaxQueueDepth == 3


def test_settings_load_vosk_config():
    """Settings.load() debe cargar configuración Vosk desde QSettings."""
    from eloGraf.settings import Settings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        
        # Configurar valores de retorno
        def mock_value(key, default, type=None):
            values = {
                "VoskModelPath": "/path/to/model",
                "VoskVadType": "webrtc",
                "VoskVadThreshold": 0.7,
                "VoskSilenceTimeoutMs": 750,
                "VoskSampleRate": 8000,
                "VoskPartialResults": True,
                "VoskTextFormatting": False,
                "VoskLocale": "es_ES",
                "VoskMaxQueueDepth": 5,
            }
            if key in values:
                val = values[key]
                if type == bool:
                    return bool(val)
                elif type == int:
                    return int(val)
                elif type == float:
                    return float(val)
                return val
            return default
        
        mock_backend.value.side_effect = mock_value
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        settings.load()
        
        assert settings.voskModelPath == "/path/to/model"
        assert settings.voskVadType == "webrtc"
        assert settings.voskVadThreshold == 0.7
        assert settings.voskSilenceTimeoutMs == 750
        assert settings.voskSampleRate == 8000
        assert settings.voskPartialResults == True
        assert settings.voskTextFormatting == False
        assert settings.voskLocale == "es_ES"
        assert settings.voskMaxQueueDepth == 5


def test_settings_write_vosk_config():
    """Settings.write() debe guardar configuración Vosk en QSettings."""
    from eloGraf.settings import Settings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        settings.voskModelPath = "/custom/model"
        settings.voskVadType = "rms"
        settings.voskVadThreshold = 0.3
        settings.voskLocale = "es_MX"
        settings.save()
        
        # Verificar que se guardaron los valores
        saved_values = {call[0][0]: call[0][1] for call in mock_backend.setValue.call_args_list}
        
        assert "VoskModelPath" in saved_values
        assert saved_values["VoskModelPath"] == "/custom/model"
        assert saved_values["VoskVadType"] == "rms"
        assert saved_values["VoskVadThreshold"] == 0.3
        assert saved_values["VoskLocale"] == "es_MX"


def test_get_engine_settings_returns_vosk_settings():
    """get_engine_settings() debe retornar VoskLocalSettings para vosk-local."""
    from eloGraf.settings import Settings
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        settings.voskModelPath = "/test/model"
        settings.voskVadType = "rms"
        settings.voskLocale = "es_ES"
        
        engine_settings = settings.get_engine_settings("vosk-local")
        
        assert isinstance(engine_settings, VoskLocalSettings)
        assert engine_settings.model_path == "/test/model"
        assert engine_settings.vad_type == "rms"
        assert engine_settings.locale == "es_ES"


def test_get_engine_settings_vosk_all_properties():
    """get_engine_settings() debe mapear todas las propiedades Vosk."""
    from eloGraf.settings import Settings
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        settings.deviceName = "hw:0,0"
        settings.voskModelPath = "/test/model"
        settings.voskVadType = "webrtc"
        settings.voskVadThreshold = 0.8
        settings.voskSilenceTimeoutMs = 600
        settings.voskSampleRate = 8000
        settings.voskPartialResults = True
        settings.voskTextFormatting = False
        settings.voskLocale = "fr_FR"
        settings.voskMaxQueueDepth = 5
        
        engine_settings = settings.get_engine_settings("vosk-local")
        
        assert engine_settings.device_name == "hw:0,0"
        assert engine_settings.model_path == "/test/model"
        assert engine_settings.vad_type == "webrtc"
        assert engine_settings.vad_threshold == 0.8
        assert engine_settings.silence_timeout_ms == 600
        assert engine_settings.sample_rate == 8000
        assert engine_settings.partial_results == True
        assert engine_settings.text_formatting == False
        assert engine_settings.locale == "fr_FR"
        assert engine_settings.max_queue_depth == 5


def test_get_engine_settings_vosk_when_current_engine():
    """get_engine_settings() debe funcionar sin argumento si sttEngine es vosk-local."""
    from eloGraf.settings import Settings
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        # Simular que STTEngine está configurado como vosk-local
        def mock_value(key, default, type=None):
            if key == "STTEngine":
                return "vosk-local"
            if key == "VoskModelPath":
                return "/default/model"
            return default
        
        mock_backend.value.side_effect = mock_value
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        settings.load()
        
        engine_settings = settings.get_engine_settings()
        
        assert isinstance(engine_settings, VoskLocalSettings)
        assert engine_settings.model_path == "/default/model"


def test_vosk_plugin_apply_to_settings():
    """VoskLocalPlugin.apply_to_settings() debe actualizar Settings."""
    from eloGraf.settings import Settings
    from eloGraf.engines.vosk_local.engine import VoskLocalPlugin
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        
        plugin = VoskLocalPlugin()
        engine_settings = VoskLocalSettings(
            engine_type="vosk-local",
            device_name="hw:1,0",
            model_path="/new/model",
            vad_type="webrtc",
            vad_threshold=0.9,
            silence_timeout_ms=700,
            sample_rate=22050,
            partial_results=True,
            text_formatting=False,
            locale="de_DE",
            max_queue_depth=7,
        )
        
        plugin.apply_to_settings(settings, engine_settings)
        
        assert settings.sttEngine == "vosk-local"
        assert settings.deviceName == "hw:1,0"
        assert settings.voskModelPath == "/new/model"
        assert settings.voskVadType == "webrtc"
        assert settings.voskVadThreshold == 0.9
        assert settings.voskSilenceTimeoutMs == 700
        assert settings.voskSampleRate == 22050
        assert settings.voskPartialResults == True
        assert settings.voskTextFormatting == False
        assert settings.voskLocale == "de_DE"
        assert settings.voskMaxQueueDepth == 7


def test_vosk_plugin_apply_preserves_other_settings():
    """apply_to_settings() no debe modificar settings de otros motores."""
    from eloGraf.settings import Settings
    from eloGraf.engines.vosk_local.engine import VoskLocalPlugin
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        settings.whisperModel = "large"
        settings.googleCloudProjectId = "my-project"
        settings.openaiApiKey = "sk-test"
        
        original_whisper = settings.whisperModel
        original_google = settings.googleCloudProjectId
        original_openai = settings.openaiApiKey
        
        plugin = VoskLocalPlugin()
        engine_settings = VoskLocalSettings(model_path="/model")
        
        plugin.apply_to_settings(settings, engine_settings)
        
        # Otros settings no deben cambiar
        assert settings.whisperModel == original_whisper
        assert settings.googleCloudProjectId == original_google
        assert settings.openaiApiKey == original_openai


def test_update_from_dataclass_vosk():
    """Settings.update_from_dataclass() debe funcionar con VoskLocalSettings."""
    from eloGraf.settings import Settings
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        
        engine_settings = VoskLocalSettings(
            model_path="/via/dataclass",
            vad_type="rms",
            locale="it_IT",
        )
        
        settings.update_from_dataclass(engine_settings)
        
        assert settings.sttEngine == "vosk-local"
        assert settings.voskModelPath == "/via/dataclass"
        assert settings.voskVadType == "rms"
        assert settings.voskLocale == "it_IT"


def test_vosk_engine_creation_via_factory():
    """El motor Vosk debe poder crearse via stt_factory con Settings."""
    from eloGraf.settings import Settings
    from eloGraf.stt_factory import create_stt_engine
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    from eloGraf.engines.vosk_local.controller import VoskLocalController
    from eloGraf.engines.vosk_local.runner import VoskLocalRunner
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings, \
         patch('vosk.Model'), \
         patch('torch.hub.load'):
        
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        settings = Settings()
        settings.voskModelPath = "/factory/model"
        settings.voskVadType = "rms"
        
        # Obtener engine settings desde Settings
        engine_settings = settings.get_engine_settings("vosk-local")
        
        # Crear motor via factory
        controller, runner = create_stt_engine("vosk-local", settings=engine_settings)
        
        assert isinstance(controller, VoskLocalController)
        assert isinstance(runner, VoskLocalRunner)


def test_vosk_roundtrip_settings():
    """Test completo: Settings -> VoskLocalSettings -> apply -> Settings."""
    from eloGraf.settings import Settings
    from eloGraf.engines.vosk_local.engine import VoskLocalPlugin
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    with patch('eloGraf.settings.QSettings') as mock_qsettings:
        mock_backend = MagicMock()
        mock_backend.value.return_value = ""
        mock_backend.beginReadArray.return_value = 0
        mock_qsettings.return_value = mock_backend
        
        # Settings inicial
        settings = Settings()
        settings.voskModelPath = "/original"
        settings.voskVadThreshold = 0.5
        
        # Obtener como engine settings
        engine_settings = settings.get_engine_settings("vosk-local")
        assert engine_settings.model_path == "/original"
        
        # Modificar engine settings
        engine_settings.model_path = "/modified"
        engine_settings.vad_threshold = 0.8
        
        # Aplicar de vuelta
        plugin = VoskLocalPlugin()
        plugin.apply_to_settings(settings, engine_settings)
        
        # Verificar que Settings se actualizó
        assert settings.voskModelPath == "/modified"
        assert settings.voskVadThreshold == 0.8


def test_vosk_available_in_engine_list():
    """Vosk debe aparecer en la lista de motores disponibles."""
    from eloGraf.stt_factory import get_available_engines
    
    engines = get_available_engines()
    
    assert "vosk-local" in engines
