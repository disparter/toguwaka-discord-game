import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))
sys.path.insert(0, str(root_dir / "tests"))

# Configura variáveis de ambiente para testes
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"

# Importa e executa os testes
import pytest

if __name__ == "__main__":
    # Executa os testes com cobertura
    pytest.main([
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "tests/"
    ])