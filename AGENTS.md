# Elograf - Comandos Útiles para Desarrollo

## Contexto General
- Elograf es una bandeja de sistema Qt que envuelve a `nerd-dictation` para dictado offline.
- Los iconos indican estado: micrófono tachado (inactivo), línea roja (cargando modelo), línea verde (modelo listo) y micrófono normal (dictando).
- La lógica de estados vive en `eloGraf/nerd_controller.py`: `NerdDictationController` interpreta stdout y códigos de salida, mientras que `NerdDictationProcessRunner` lanza el proceso y alimenta al controlador. La UI solo escucha estos estados.
- Por defecto se añade `--verbose=1` al comando `nerd-dictation begin` salvo que el usuario especifique otro `--verbose`, garantizando mensajes como "Loading model" y "Model loaded".

## Ejecución Local

### Ejecutar elograf con uv (método recomendado)
```bash
# Ejecutar en foreground
uv run python -m eloGraf.elograf

# Ejecutar en background
uv run python -m eloGraf.elograf > /tmp/elograf.log 2>&1 &
```


### Verificar versión
```bash
uv run python -m eloGraf.elograf --version
```

## Comandos IPC (Inter-Process Communication)

Una vez que elograf está ejecutándose, puedes enviar comandos:

```bash
# Iniciar dictado
uv run python -m eloGraf.elograf --begin

# Detener dictado
uv run python -m eloGraf.elograf --end

# Salir de elograf
uv run python -m eloGraf.elograf --exit

# Listar modelos disponibles
uv run python -m eloGraf.elograf --list-models

# Cambiar modelo
uv run python -m eloGraf.elograf --set-model MODEL_NAME
```

## Depuración

### Capturar logs
```bash
# Redirigir toda la salida a un archivo
uv run python -m eloGraf.elograf > /tmp/elograf-debug.log 2>&1 &

# Ver logs en tiempo real
tail -f /tmp/elograf-debug.log
```

### Capturas de pantalla del sistema tray

```bash
# Captura completa de pantalla
flameshot full -p /tmp/screenshot.png

# El icono de elograf aparece en el system tray (parte inferior derecha)
# Iconos posibles:
# - Micrófono tachado: Estado inactivo
# - Micrófono con línea roja: Cargando modelo
# - Micrófono con línea verde: Modelo listo
# - Micrófono normal: Dictando
```

### Verificar procesos

```bash
# Verificar si elograf está ejecutándose
ps aux | grep elograf | grep -v grep

# Verificar si nerd-dictation está ejecutándose
ps aux | grep nerd-dictation | grep -v grep

# Matar todos los procesos de elograf
pkill -f elograf

# Matar forzosamente
pkill -9 -f elograf
```

## Manejo de Señales

### Ctrl+C (SIGINT)
Elograf maneja correctamente SIGINT cuando se ejecuta en foreground:
```bash
# Ejecutar en foreground
uv run python -m eloGraf.elograf

# Presionar Ctrl+C para salir limpiamente
```

### Señales soportadas
- `SIGTERM`: Terminación normal
- `SIGINT`: Ctrl+C (interrupción)
- `SIGHUP`: Hangup (si está disponible)

## Testing del Indicador de Carga

### Test completo del ciclo de carga
```bash
# 1. Iniciar elograf en background
uv run python -m eloGraf.elograf > /tmp/elograf-test.log 2>&1 &

# 2. Capturar icono en estado inicial (micrófono tachado)
sleep 2
flameshot full -p /tmp/icon-initial.png

# 3. Iniciar dictado (debería mostrar línea roja mientras carga)
uv run python -m eloGraf.elograf --begin
sleep 1
flameshot full -p /tmp/icon-loading-red.png

# 4. Esperar a que el modelo cargue (debería mostrar línea verde)
sleep 10
flameshot full -p /tmp/icon-ready-green.png

# 5. Ver los logs
cat /tmp/elograf-test.log
```

### Pruebas Automáticas
- Dependencias de desarrollo gestionadas con `uv`; para asegurar pytest: `uv add --dev pytest` (ya reflejado en `dependency-groups.dev`).
- Ejecutar toda la suite: `uv run pytest`.
- Pruebas clave: `tests/test_nerd_controller.py` valida el controlador y runner de nerd-dictation mediante procesos simulados (no requiere entorno gráfico).

## Verificación de Configuración

### Verificar modelo de nerd-dictation
- Verificar que el modelo tenga los archivos necesarios (am/, conf/, graph/, etc.)

```bash
# Ver el modelo configurado
ls -la ~/.config/nerd-dictation/model

# Debe ser un enlace simbólico a un modelo válido, por ejemplo:
# model -> es_vosk_large
```

### Verificar D-Bus
```bash
# Elograf usa D-Bus para IPC
# Si hay problemas, verificar que D-Bus esté disponible:
dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames
```
