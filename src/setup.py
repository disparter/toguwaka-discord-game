from setuptools import setup, find_packages

setup(
    name="tokugawa-discord-game",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "discord.py",
        "python-dotenv",
    ],
) 