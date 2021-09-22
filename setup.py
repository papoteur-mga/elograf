from distutils.core import setup
from distutils.command.build import build
import os, glob


class BuildQm(build):
    os.system("pylupdate5 elograf.pro")
    for ts in glob.glob("eloGraf/translations/*.ts"):
        os.system("lrelease {0} -qm {1}".format(ts, (ts[:-2] + "qm")))


data_files = [
    (
        "share/icons/hicolor/scalable/apps/",
        ["icons/elograf/scalable/micro.svg", "icons/elograf/scalable/nomicro.svg"],
    ),
    ("share/doc/elograf/", ["README", "LICENSE"]),
    (
        "share/applications/",
        ["elograf.desktop", ],
    ),
]

setup(
    name="elograf",
    version="0.1.6",
    packages=["eloGraf"],
    scripts=["elograf"],
    package_data={"": ["translations/*.qm"]},
    license="GNU General Public License v3 (GPLv3)",
    url="https://github.com/papoteur-mga/elograf/",
    description="Utility for launching and configuring nerd-dictation for voice recognition.",
    long_description="To be launched at start of the desktop environnement to display an icon in the icons tray.",
    platforms=["Linux"],
    author="Papoteur",
    author_email="papoteur@mageia.org",
    data_files=data_files,
    cmdclass={
        "build_qm": BuildQm,
    },
)
