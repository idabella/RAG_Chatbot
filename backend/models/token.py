# backend/models/token.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

# Importez la Base déclarative de votre configuration de base de données.
# Le chemin peut varier selon la structure de votre projet.
from core.database import Base 

class RefreshToken(Base):
    """
    Modèle SQLAlchemy pour stocker les tokens de rafraîchissement (refresh tokens)
    de manière persistante dans la base de données.
    """
    __tablename__ = "refresh_tokens"

    # Utiliser BigInteger est une bonne pratique pour les clés primaires 
    # si la table peut potentiellement contenir des milliards d'enregistrements.
    # Integer est suffisant pour la plupart des applications.
    id = Column(BigInteger, primary_key=True, index=True)

    # Clé étrangère liant ce token à un utilisateur dans la table 'users'.
    # L'option 'nullable=False' garantit qu'un token ne peut pas exister sans utilisateur.
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Le token lui-même. Il doit être unique pour éviter les doublons.
    token = Column(String(512), unique=True, index=True, nullable=False)

    # La date et l'heure d'expiration du token.
    expires_at = Column(DateTime, nullable=False)
    
    # La date de création du token, avec une valeur par défaut.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Définit la relation avec le modèle User.
    # 'back_populates' doit correspondre au nom de la relation dans le modèle User.
    # Cela permet d'accéder à l'utilisateur depuis un objet token (ex: my_token.user).
    user = relationship("User", back_populates="refresh_tokens")

