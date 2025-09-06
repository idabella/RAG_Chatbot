# backend/models/__init__.py

# Importez la Base depuis votre module de base de données
from core.database import Base

# Importez TOUS vos modèles SQLAlchemy ici.
# L'ordre n'a généralement pas d'importance dans ce fichier,
# car Python les mettra tous dans le même namespace.
from .user import User
from .token import RefreshToken
# from .document import Document  # <-- Ajoutez ici tous vos autres modèles
# from .chat_history import ChatHistory # <-- Par exemple

# Vous pouvez également définir une liste __all__ pour un import propre, mais ce n'est pas obligatoire.
__all__ = ["Base", "User", "RefreshToken"] # Ajoutez vos autres modèles à cette liste
