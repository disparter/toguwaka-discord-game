import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Verifica e instala dependências necessárias para os testes."""
    required_packages = [
        'discord.py',
        'python-dotenv',
        'boto3',
        'pytest',
        'pytest-cov',
        'pytest-asyncio',
        'pytest-mock'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    # Verifica e instala dependências
    check_dependencies()
    
    # Importa pytest após instalar dependências
    import pytest
    
    # Executa os testes com cobertura
    pytest.main([
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "tests/"
    ])

if __name__ == "__main__":
    main()