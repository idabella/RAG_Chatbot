// services/authService.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Interfaces pour les données
export interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  login_count: number;
  conversation_count: number;
  message_count: number;
  is_new_user: boolean;
}

export interface RegisterData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthResponse {
  message: string;
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in?: number;
}

export interface ApiError {
  detail: string;
  status?: number;
}

// Classe de service pour l'authentification
class AuthService {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_BASE_URL}/api/v1/auth`;
  }

  // Méthode utilitaire pour les requêtes HTTP
  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError({
          detail: errorData.detail || `Erreur HTTP ${response.status}`,
          status: response.status,
        });
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Gestion des erreurs réseau
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new ApiError({
          detail: 'Impossible de se connecter au serveur. Vérifiez votre connexion internet.',
          status: 0,
        });
      }
      
      throw new ApiError({
        detail: 'Une erreur inattendue s\'est produite.',
        status: 500,
      });
    }
  }

  // Méthode pour inclure l'en-tête d'autorisation
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
      };
    }
    return {};
  }

  // Inscription
  async register(userData: RegisterData): Promise<AuthResponse> {
    return this.makeRequest<AuthResponse>('/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // Connexion
  async login(loginData: LoginData): Promise<AuthResponse> {
    return this.makeRequest<AuthResponse>('/login', {
      method: 'POST',
      body: JSON.stringify(loginData),
    });
  }

  // Rafraîchissement du token
  async refreshToken(refreshToken: string): Promise<{
    access_token: string;
    refresh_token: string;
    token_type: string;
  }> {
    return this.makeRequest('/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  // Déconnexion
  async logout(): Promise<{ message: string }> {
    return this.makeRequest('/logout', {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
  }

  // Changement de mot de passe
  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    return this.makeRequest('/change-password', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  }

  // Obtenir le profil utilisateur
  async getProfile(): Promise<User> {
    return this.makeRequest('/profile', {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
  }

  // Vérifier la validité du token
  async verifyToken(): Promise<{
    valid: boolean;
    user_id: number;
    email: string;
    role: string;
  }> {
    return this.makeRequest('/verify-token', {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
  }

  // Test de connexion
  async testConnection(): Promise<{
    success: boolean;
    message: string;
    timestamp: string;
  }> {
    return this.makeRequest('/test', {
      method: 'GET',
    });
  }

  // Gestion du stockage des tokens
  saveTokens(accessToken: string, refreshToken: string, user: User): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user', JSON.stringify(user));
  }

  // Récupération des tokens
  getTokens(): { accessToken: string | null; refreshToken: string | null } {
    return {
      accessToken: localStorage.getItem('access_token'),
      refreshToken: localStorage.getItem('refresh_token'),
    };
  }

  // Suppression des tokens
  clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  // Récupération de l'utilisateur depuis le localStorage
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (error) {
        console.error('Erreur lors de la lecture des données utilisateur:', error);
        this.clearTokens();
        return null;
      }
    }
    return null;
  }

  // Vérification si l'utilisateur est connecté
  isAuthenticated(): boolean {
    const { accessToken } = this.getTokens();
    return !!accessToken;
  }
}

// Classe pour les erreurs API
export class ApiError extends Error {
  status?: number;

  constructor({ detail, status }: { detail: string; status?: number }) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
  }
}

// Instance par défaut du service
export const authService = new AuthService();
export default authService;