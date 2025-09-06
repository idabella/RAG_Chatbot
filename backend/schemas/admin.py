# app/schemas/admin.py

from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator


class TopUserModel(BaseModel):
    """Modèle pour les utilisateurs les plus actifs"""
    user_id: int = Field(..., description="ID de l'utilisateur")
    email: str = Field(..., description="Email de l'utilisateur")
    message_count: int = Field(..., description="Nombre de messages envoyes")


class MessagesByDayModel(BaseModel):
    """Modèle pour les messages par jour"""
    date: str = Field(..., description="Date au format YYYY-MM-DD")
    count: int = Field(..., description="Nombre de messages")


class AnalyticsResponse(BaseModel):
    """Reponse des analytics d'administration"""
    period_days: int = Field(..., description="Periode d'analyse en jours")
    total_users: int = Field(..., description="Nombre total d'utilisateurs")
    active_users: int = Field(..., description="Utilisateurs actifs")
    new_users: int = Field(..., description="Nouveaux utilisateurs")
    total_conversations: int = Field(..., description="Nombre total de conversations")
    active_conversations: int = Field(..., description="Conversations actives")
    total_messages: int = Field(..., description="Nombre total de messages")
    messages_in_period: int = Field(..., description="Messages dans la periode")
    messages_by_day: List[MessagesByDayModel] = Field(default_factory=list, description="Messages par jour")
    top_users: List[TopUserModel] = Field(default_factory=list, description="Utilisateurs les plus actifs")
    total_documents: int = Field(..., description="Nombre total de documents")
    processed_documents: int = Field(..., description="Documents traites")
    avg_response_time: float = Field(..., description="Temps de reponse moyen en secondes")
    user_satisfaction: float = Field(..., description="Satisfaction utilisateur (sur 5)")

    @validator('user_satisfaction')
    def validate_satisfaction(cls, v):
        if not 0 <= v <= 5:
            raise ValueError('La satisfaction doit être entre 0 et 5')
        return v

    @validator('avg_response_time')
    def validate_response_time(cls, v):
        if v < 0:
            raise ValueError('Le temps de reponse ne peut pas être negatif')
        return v


class ServiceStatusModel(BaseModel):
    """Modèle pour le statut d'un service"""
    name: str = Field(..., description="Nom du service")
    status: str = Field(..., description="Statut du service")
    response_time: Optional[float] = Field(None, description="Temps de reponse en ms")
    last_check: datetime = Field(..., description="Dernière verification")
    error_message: Optional[str] = Field(None, description="Message d'erreur si applicable")


class SystemStatusResponse(BaseModel):
    """Reponse du statut système"""
    status: str = Field(..., description="Statut general du système")
    timestamp: datetime = Field(..., description="Horodatage de la verification")
    uptime_seconds: int = Field(..., description="Temps de fonctionnement en secondes")
    cpu_usage: float = Field(..., description="Utilisation CPU en pourcentage")
    memory_usage: float = Field(..., description="Utilisation memoire en pourcentage")
    memory_total: int = Field(..., description="Memoire totale en bytes")
    memory_available: int = Field(..., description="Memoire disponible en bytes")
    disk_usage: float = Field(..., description="Utilisation disque en pourcentage")
    disk_total: int = Field(..., description="Espace disque total en bytes")
    disk_free: int = Field(..., description="Espace disque libre en bytes")
    database_status: str = Field(..., description="Statut de la base de donnees")
    database_response_time: float = Field(..., description="Temps de reponse DB en ms")
    services_status: List[ServiceStatusModel] = Field(default_factory=list, description="Statut des services")
    total_documents: int = Field(..., description="Nombre total de documents")
    processed_documents: int = Field(..., description="Documents traites")
    data_size_bytes: int = Field(..., description="Taille des donnees en bytes")
    active_connections: int = Field(..., description="Connexions actives")

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['healthy', 'warning', 'critical', 'maintenance']
        if v not in valid_statuses:
            raise ValueError(f'Statut doit être un de: {valid_statuses}')
        return v

    @validator('cpu_usage', 'memory_usage', 'disk_usage')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Les pourcentages doivent être entre 0 et 100')
        return v


class UserDataModel(BaseModel):
    """Modèle pour les donnees utilisateur dans l'admin"""
    id: int = Field(..., description="ID de l'utilisateur")
    email: str = Field(..., description="Email de l'utilisateur")
    role: str = Field(..., description="Rôle de l'utilisateur")
    is_active: bool = Field(..., description="Utilisateur actif ou non")
    created_at: datetime = Field(..., description="Date de creation")
    last_login: Optional[datetime] = Field(None, description="Dernière connexion")
    conversation_count: int = Field(0, description="Nombre de conversations")
    message_count: int = Field(0, description="Nombre de messages")
    total_usage_time: int = Field(0, description="Temps d'utilisation total en secondes")


class UserManagementResponse(BaseModel):
    """Reponse de la gestion des utilisateurs"""
    users: List[UserDataModel] = Field(..., description="Liste des utilisateurs")
    total: int = Field(..., description="Nombre total d'utilisateurs")
    skip: int = Field(0, description="Nombre d'elements ignores")
    limit: int = Field(50, description="Limite d'elements par page")

    @validator('skip', 'limit')
    def validate_pagination(cls, v):
        if v < 0:
            raise ValueError('Skip et limit doivent être positifs')
        return v


class AdminDashboardStats(BaseModel):
    """Statistiques du tableau de bord admin"""
    total_users: int = Field(..., description="Nombre total d'utilisateurs")
    active_users: int = Field(..., description="Utilisateurs actifs")
    inactive_users: int = Field(..., description="Utilisateurs inactifs")
    recent_users: int = Field(..., description="Utilisateurs recents")
    total_conversations: int = Field(..., description="Nombre total de conversations")
    recent_conversations: int = Field(..., description="Conversations recentes")
    total_messages: int = Field(..., description="Nombre total de messages")
    total_documents: int = Field(..., description="Nombre total de documents")
    processed_documents: int = Field(..., description="Documents traites")
    pending_documents: int = Field(..., description="Documents en attente")
    avg_messages_per_conversation: float = Field(..., description="Messages moyens par conversation")
    processing_rate: float = Field(..., description="Taux de traitement en pourcentage")

    @validator('processing_rate')
    def validate_processing_rate(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Le taux de traitement doit être entre 0 et 100')
        return v

    @validator('avg_messages_per_conversation')
    def validate_avg_messages(cls, v):
        if v < 0:
            raise ValueError('La moyenne de messages ne peut pas être negative')
        return v


# Modèles supplementaires pour l'administration

class AdminConfigModel(BaseModel):
    """Configuration d'administration"""
    maintenance_mode: bool = Field(False, description="Mode maintenance")
    registration_enabled: bool = Field(True, description="Inscription activee")
    max_upload_size: int = Field(10485760, description="Taille max upload en bytes (10MB)")
    max_conversations_per_user: int = Field(100, description="Conversations max par utilisateur")
    session_timeout: int = Field(3600, description="Timeout de session en secondes")
    rate_limit_requests: int = Field(100, description="Limite de requêtes par minute")
    auto_cleanup_days: int = Field(30, description="Nettoyage auto après X jours")


class AdminConfigResponse(BaseModel):
    """Reponse de la configuration admin"""
    config: AdminConfigModel = Field(..., description="Configuration actuelle")
    last_updated: datetime = Field(..., description="Dernière mise à jour")
    updated_by: str = Field(..., description="Utilisateur ayant fait la mise à jour")


class AdminLogEntry(BaseModel):
    """Entree de log d'administration"""
    id: int = Field(..., description="ID du log")
    timestamp: datetime = Field(..., description="Horodatage")
    level: str = Field(..., description="Niveau de log")
    category: str = Field(..., description="Categorie")
    message: str = Field(..., description="Message")
    user_id: Optional[int] = Field(None, description="ID utilisateur associe")
    ip_address: Optional[str] = Field(None, description="Adresse IP")
    user_agent: Optional[str] = Field(None, description="User Agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadonnees supplementaires")

    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in valid_levels:
            raise ValueError(f'Niveau doit être un de: {valid_levels}')
        return v


class AdminLogsResponse(BaseModel):
    """Reponse des logs d'administration"""
    logs: List[AdminLogEntry] = Field(..., description="Liste des logs")
    total: int = Field(..., description="Nombre total de logs")
    skip: int = Field(0, description="Nombre d'elements ignores")
    limit: int = Field(100, description="Limite d'elements par page")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtres appliques")


class BulkUserActionRequest(BaseModel):
    """Requête d'action en masse sur les utilisateurs"""
    user_ids: List[int] = Field(..., description="IDs des utilisateurs")
    action: str = Field(..., description="Action à effectuer")
    reason: Optional[str] = Field(None, description="Raison de l'action")

    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['activate', 'deactivate', 'delete', 'reset_password', 'change_role']
        if v not in valid_actions:
            raise ValueError(f'Action doit être une de: {valid_actions}')
        return v

    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError('Au moins un ID utilisateur est requis')
        if len(v) > 100:
            raise ValueError('Maximum 100 utilisateurs par action en masse')
        return v


class BulkUserActionResponse(BaseModel):
    """Reponse d'action en masse sur les utilisateurs"""
    success_count: int = Field(..., description="Nombre d'actions reussies")
    failure_count: int = Field(..., description="Nombre d'actions echouees")
    errors: List[str] = Field(default_factory=list, description="Messages d'erreur")
    processed_user_ids: List[int] = Field(..., description="IDs des utilisateurs traites")


class DocumentProcessingStats(BaseModel):
    """Statistiques de traitement des documents"""
    total_documents: int = Field(..., description="Total des documents")
    processing: int = Field(..., description="En cours de traitement")
    completed: int = Field(..., description="Traitement termine")
    failed: int = Field(..., description="Traitement echoue")
    avg_processing_time: float = Field(..., description="Temps moyen de traitement en secondes")
    last_processed: Optional[datetime] = Field(None, description="Dernier document traite")
    queue_size: int = Field(0, description="Taille de la file d'attente")


class ErrorSummary(BaseModel):
    """Resume des erreurs système"""
    error_type: str = Field(..., description="Type d'erreur")
    count: int = Field(..., description="Nombre d'occurrences")
    last_occurrence: datetime = Field(..., description="Dernière occurrence")
    severity: str = Field(..., description="Severite")
    
    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ['low', 'medium', 'high', 'critical']
        if v not in valid_severities:
            raise ValueError(f'Severite doit être une de: {valid_severities}')
        return v


class SystemHealthResponse(BaseModel):
    """Reponse de sante système detaillee"""
    overall_status: str = Field(..., description="Statut general")
    components: Dict[str, str] = Field(..., description="Statut par composant")
    error_summary: List[ErrorSummary] = Field(default_factory=list, description="Resume des erreurs")
    recommendations: List[str] = Field(default_factory=list, description="Recommandations")
    last_backup: Optional[datetime] = Field(None, description="Dernière sauvegarde")
    next_maintenance: Optional[datetime] = Field(None, description="Prochaine maintenance")


# Schemas de requête pour les filtres et recherches

class AnalyticsFilterRequest(BaseModel):
    """Filtres pour les analytics"""
    period_days: int = Field(30, description="Periode en jours", ge=1, le=365)
    user_id: Optional[int] = Field(None, description="Filtrer par utilisateur")
    start_date: Optional[datetime] = Field(None, description="Date de debut")
    end_date: Optional[datetime] = Field(None, description="Date de fin")


class UserSearchRequest(BaseModel):
    """Recherche d'utilisateurs"""
    search_term: Optional[str] = Field(None, description="Terme de recherche")
    role: Optional[str] = Field(None, description="Filtrer par rôle")
    is_active: Optional[bool] = Field(None, description="Filtrer par statut actif")
    created_after: Optional[datetime] = Field(None, description="Cree après cette date")
    created_before: Optional[datetime] = Field(None, description="Cree avant cette date")
    skip: int = Field(0, ge=0, description="Pagination - skip")
    limit: int = Field(50, ge=1, le=100, description="Pagination - limit")


class LogFilterRequest(BaseModel):
    """Filtres pour les logs"""
    level: Optional[str] = Field(None, description="Niveau de log")
    category: Optional[str] = Field(None, description="Categorie")
    user_id: Optional[int] = Field(None, description="ID utilisateur")
    start_date: Optional[datetime] = Field(None, description="Date de debut")
    end_date: Optional[datetime] = Field(None, description="Date de fin")
    search_term: Optional[str] = Field(None, description="Recherche dans le message")
    skip: int = Field(0, ge=0, description="Pagination - skip")
    limit: int = Field(100, ge=1, le=500, description="Pagination - limit")