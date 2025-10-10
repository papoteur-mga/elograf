# Elograf

**Utilitaire de reconnaissance vocale pour nerd-dictation**

Elograf est une application de bureau qui fournit une interface graphique pour lancer et configurer [nerd-dictation](https://github.com/ideasman42/nerd-dictation) pour la reconnaissance vocale. L'application s'intègre dans la barre d'icônes système et offre un contrôle facile de la dictée via une icône et un menu intuitifs.

---

## Fonctionnalités

### 🎤 Contrôle Rapide
- **Icône dans la barre système** reflétant l'état actuel (chargement, prêt, dictée, suspendu, arrêté)
- **Opération en un clic**: Cliquez pour alterner démarrage → suspension → reprise
- **Contrôles par menu**: Démarrer, suspendre/reprendre ou arrêter la dictée
- **Intégration CLI**: Contrôler la dictée depuis la ligne de commande avec `--begin`, `--end`, `--toggle`

### ⚙️ Configuration Avancée
- **Modèles multilingues**: Télécharger et gérer des modèles depuis le site alphacei
- **Stockage des modèles**: Installer dans l'espace utilisateur ou système (avec authentification polkit)
- **Modèles personnalisés**: Ajouter vos propres répertoires de modèles avec des noms uniques
- **Sélection du périphérique audio**: Choisir parmi les sources d'entrée PulseAudio disponibles
- **Simulation d'entrée**: Support pour XDOTOOL (X11) et DOTOOL (Wayland)
- **Commandes pre/post**: Exécuter des commandes personnalisées avant et après la dictée

### ⌨️ Raccourcis Clavier Globaux (KDE)
Avec PyQt6-DBus installé sur KDE, configurez des raccourcis système pour:
- Démarrer la dictée
- Arrêter la dictée
- Basculer la dictée
- Suspendre/reprendre la dictée

### 🔧 Options Flexibles
- Personnaliser le taux d'échantillonnage, le timeout, le temps d'inactivité
- Ponctuation basée sur le délai précédent
- Nombres en chiffres ou en lettres
- Majuscule en début de phrase
- Configuration de variables d'environnement

---

## Installation

### Méthode 1: Utiliser `uv` (Recommandé)

[uv](https://github.com/astral-sh/uv) est un gestionnaire de paquets et de projets Python rapide qui gère les dépendances automatiquement.

**Installation globale en tant qu'outil:**
```bash
uv tool install git+https://github.com/papoteur-mga/elograf
```

**Pour le développement:**
```bash
uv pip install .
```

### Méthode 2: Utiliser `pip`

**Installation système (en tant que root):**
```bash
pip install .
```

**Installation utilisateur:**
```bash
pip install --user .
```

> ⚠️ **Note**: Assurez-vous que `~/.local/bin` est dans votre PATH pour les installations utilisateur.

### Prérequis
- Python 3.7+
- PyQt6 (inclut le support D-Bus pour les raccourcis globaux KDE)
- ujson
- urllib

> ⚠️ **nerd-dictation** n'est pas inclus et doit être installé séparément.

---

## Utilisation

### Démarrer Elograf

Lancez au démarrage du bureau pour afficher l'icône de la barre système. Ajoutez `elograf` aux applications de démarrage automatique de votre environnement de bureau.

```bash
elograf                   # Lancer l'application avec l'icône système
elograf --version         # Afficher la version et quitter
```

### Mode Clic Direct

Activez "Active direct click on icon" dans les préférences:
- Un clic gauche démarre la dictée
- Un autre clic l'arrête
- Clic droit ouvre le menu (configurer, quitter)

### Interface en Ligne de Commande

Contrôlez une instance Elograf en cours d'exécution depuis le terminal:

```bash
elograf --begin                    # Démarrer la dictée
elograf -s                         # Démarrer la dictée (forme courte, rétro-compatible)
elograf --end                      # Arrêter la dictée
elograf --toggle                   # Basculer l'état de la dictée
elograf --exit                     # Quitter l'application
elograf --list-models              # Lister tous les modèles (● montre l'actuel)
elograf --set-model vosk-fr-fr     # Changer pour un modèle spécifique
elograf -l DEBUG                   # Définir le niveau de log (DEBUG, INFO, WARNING, ERROR)
```

> 💡 **Instance Unique**: Une seule instance d'Elograf s'exécute à la fois. Les commandes communiquent via IPC (D-Bus ou sockets locaux).

### Configuration

Le dialogue de configuration apparaît automatiquement si aucun modèle n'est défini. Accédez-y à tout moment depuis le menu de la barre:

#### Onglet Modèles
- Sélectionner parmi les modèles installés
- Télécharger de nouveaux modèles depuis alphacei
- Ajouter des répertoires de modèles personnalisés
- Stocker les modèles dans l'espace utilisateur (`~/.config/vosk-models`) ou système (`/usr/share/vosk-models`)

#### Paramètres Avancés
- **Périphérique Audio**: Sélectionner le microphone parmi les sources PulseAudio disponibles
- **Précommande**: Exécuter avant le démarrage de nerd-dictation (ex: `setxkbmap fr`)
- **Post-commande**: Exécuter après l'arrêt de nerd-dictation
- **Taux d'échantillonnage**: Taux d'échantillonnage d'enregistrement (défaut: 44100 Hz)
- **Timeout**: Arrêt automatique après silence (0 désactive)
- **Temps d'inactivité**: Compromis CPU vs réactivité (défaut: 100ms)
- **Timeout de ponctuation**: Ajouter de la ponctuation selon la durée de la pause
- **Outil d'entrée**: XDOTOOL (X11) ou DOTOOL (Wayland)
- **Disposition du clavier**: Requis pour DOTOOL (ex: 'fr', 'de', 'us')
- **Raccourcis globaux**: Raccourcis clavier système (KDE uniquement)

---

## Gestion des Signaux et du Démon

Elograf s'exécute comme un démon en premier plan avec gestion gracieuse des signaux:

```bash
# Arrêt gracieux
kill $(cat ~/.config/Elograf/elograf.pid)

# Alternative: envoyer SIGHUP
kill -HUP $(cat ~/.config/Elograf/elograf.pid)
```

**Signaux supportés:**
- `SIGTERM`: Arrêter la dictée, nettoyer les ressources, quitter
- `SIGINT` (Ctrl+C): Identique à SIGTERM
- `SIGHUP`: Arrêt gracieux

**Emplacement du fichier PID:** `~/.config/Elograf/elograf.pid`

---

## Détails Techniques

### Architecture
- **Langage**: Python 3
- **Framework GUI**: Qt6 (PyQt6)
- **Système IPC**: Couche de communication adaptative
  - D-Bus sous Linux/KDE (avec KGlobalAccel pour les raccourcis)
  - Qt Local Sockets sur les autres plateformes

### Emplacements des Fichiers
| Élément | Chemin |
|---------|--------|
| Configuration | `~/.config/Elograf/Elograf.conf` |
| Fichier PID | `~/.config/Elograf/elograf.pid` |
| Modèles utilisateur | `~/.config/vosk-models` |
| Modèles système | `/usr/share/vosk-models` |
| Traductions | `/usr/share/elograf/translations` |

### Gestion des États
L'icône de la barre système affiche l'état de la dictée en temps réel:
- 🔵 **Chargement**: Le modèle se charge
- 🟢 **Prêt**: En attente de démarrage
- 🔴 **Dictée**: Enregistrement actif
- 🟡 **Suspendu**: En pause, prêt à reprendre
- ⚫ **Arrêté**: Non actif

---

## Développement

### Exécuter les Tests
```bash
uv run pytest
```

### Structure du Projet
```
elograf/
├── eloGraf/           # Code principal de l'application
│   ├── dialogs.py     # Dialogues de configuration et de modèles
│   ├── elograf.py     # Point d'entrée de l'application
│   ├── tray_icon.py   # Interface de la barre système
│   └── ...
├── tests/             # Suite de tests
└── pyproject.toml     # Configuration du projet
```

---

## Contribuer

Les contributions sont les bienvenues! Merci de:
1. Forker le dépôt
2. Créer une branche de fonctionnalité
3. Ajouter des tests pour les nouvelles fonctionnalités
4. Soumettre une pull request

---

## Licence

Licence GPL-3.0 - Voir le fichier LICENSE pour les détails

---

## Auteurs

- **papoteur** - Auteur original
- **Pablo Caro** - Co-auteur (Sélection du périphérique PulseAudio)

---

## Liens

- [Dépôt GitHub](https://github.com/papoteur-mga/elograf)
- [nerd-dictation](https://github.com/ideasman42/nerd-dictation)
- [Modèles Vosk (alphacei)](https://alphacephei.com/vosk/models)
