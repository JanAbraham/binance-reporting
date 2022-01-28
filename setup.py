from setuptools import setup, find_packages

VERSION = "0.1.0" 
NAME = "binance-reporting"
DESCRIPTION = "Binance Reporting Modules"
LONG_DESCRIPTION = "Modules which help to download user data (e.g. trading history, orders, deposits, withdrawals, snapshots) from Binance."

# Setting up
setup(
        name=NAME, 
        version=VERSION,
        author="Jan Abraham",
        author_email="jan.abraham@bluewin.ch",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=["pandas", "python-binance", "pyyaml", "python-telegram-bot", ]
            ["python-binance", "pandas", "logging", "telegram", "python-telegram-bot", "time", "sys", "os", "yaml"]
        
        keywords=['python', 'binance', 'reporting', 'crypto', 'trading', 'history'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 2",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Linux :: Linux",
            "Operating System :: Microsoft :: Windows",
        ]
)