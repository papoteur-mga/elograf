from setuptools import setup
from distutils.command.build import build
import os, glob


class BuildQm(build):
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
    data_files=data_files,
    cmdclass={
        "build_qm": BuildQm,
    },
    package_data={"": ["translations/*.qm"]},
)
