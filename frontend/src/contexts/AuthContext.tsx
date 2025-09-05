// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService, { User, ApiError } from '../services/authService';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (name: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  updateUser: (user: User) => void;
  clearAuth: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Fonction utilitaire pour gérer les erreurs
  const handleError = (error: any): string => {
    if (error instanceof ApiError) {
      return error.message;
    }
    if (error?.message) {
      return error.message;
    }
    return 'Une erreur inattendue s\'est produite';
  };

  // Vérification de l'authentification au chargement
  const checkAuthStatus = useCallback(async () => {
    try {
      const tokens = authService.getTokens();
      
      if (!tokens.accessToken) {
        setLoading(false);
        return;
      }

      // Vérifier la validité du token
      try {
        const tokenVerification = await authService.verifyToken();
        if (tokenVerification.valid) {
          const currentUser = authService.getCurrentUser();
          if (currentUser) {
            setUser(currentUser);
            setIsAuthenticated(true);
          } else {
            // Token valide mais pas d'utilisateur en localStorage, récupérer le profil
            const profile = await authService.getProfile();
            setUser(profile);
            setIsAuthenticated(true);
            // Sauvegarder l'utilisateur en localStorage
            localStorage.setItem('user', JSON.stringify(profile));
          }
        } else {
          // Token invalide, essayer de le rafraîchir
          const refreshSuccess = await refreshTokenInternal();
          if (!refreshSuccess) {
            clearAuth();
          }
        }
      } catch (error) {
        // Si la vérification du token échoue, essayer de rafraîchir
        const refreshSuccess = await refreshTokenInternal();
        if (!refreshSuccess) {
          clearAuth();
        }
      }
    } catch (error) {
      console.error('Erreur lors de la vérification de l\'authentification:', error);
      clearAuth();
    } finally {
      setLoading(false);
    }
  }, []);

  // Rafraîchissement du token (fonction interne)
  const refreshTokenInternal = async (): Promise<boolean> => {
    try {
      const tokens = authService.getTokens();
      
      if (!tokens.refreshToken) {
        return false;
      }

      const response = await authService.refreshToken(tokens.refreshToken);
      
      // Mettre à jour les tokens
      authService.saveTokens(response.access_token, response.refresh_token, user!);
      
      return true;
    } catch (error) {
      console.error('Erreur lors du rafraîchissement du token:', error);
      return false;
    }
  };

  // Rafraîchissement du token (fonction publique)
  const refreshToken = useCallback(async (): Promise<boolean> => {
    return refreshTokenInternal();
  }, [user]);

  // Connexion
  const login = useCallback(async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      setLoading(true);
      
      const response = await authService.login({ email, password });
      
      // Sauvegarder les tokens et l'utilisateur
      authService.saveTokens(response.access_token, response.refresh_token, response.user);
      
      setUser(response.user);
      setIsAuthenticated(true);
      
      return { success: true };
    } catch (error) {
      const errorMessage = handleError(error);
      console.error('Erreur lors de la connexion:', error);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  // Inscription
  const signup = useCallback(async (name: string, email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      setLoading(true);
      
      // Diviser le nom complet
      const nameParts = name.trim().split(' ');
      const firstName = nameParts[0];
      const lastName = nameParts.slice(1).join(' ') || '';
      
      const response = await authService.register({
        first_name: firstName,
        last_name: lastName,
        email: email.toLowerCase().trim(),
        password,
      });
      
      // Sauvegarder les tokens et l'utilisateur
      authService.saveTokens(response.access_token, response.refresh_token, response.user);
      
      setUser(response.user);
      setIsAuthenticated(true);
      
      return { success: true };
    } catch (error) {
      const errorMessage = handleError(error);
      console.error('Erreur lors de l\'inscription:', error);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  // Déconnexion
  const logout = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      
      // Appeler l'endpoint de déconnexion si l'utilisateur est authentifié
      if (isAuthenticated) {
        try {
          await authService.logout();
        } catch (error) {
          // Ignorer les erreurs de déconnexion côté serveur
          console.warn('Erreur lors de la déconnexion côté serveur:', error);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    } finally {
      clearAuth();
      setLoading(false);
    }
  }, [isAuthenticated]);

  // Nettoyage de l'authentification
  const clearAuth = useCallback((): void => {
    authService.clearTokens();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  // Mise à jour de l'utilisateur
  const updateUser = useCallback((updatedUser: User): void => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  }, []);

  // Configuration automatique du rafraîchissement des tokens
  useEffect(() => {
    let refreshInterval: NodeJS.Timeout;

    if (isAuthenticated) {
      // Rafraîchir le token toutes les 25 minutes (avant l'expiration de 30 minutes)
      refreshInterval = setInterval(async () => {
        const success = await refreshTokenInternal();
        if (!success) {
          clearAuth();
        }
      }, 25 * 60 * 1000); // 25 minutes
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [isAuthenticated]);

  // Vérification initiale de l'authentification
  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  // Gestionnaire pour les erreurs de réseau et token expiré
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'access_token' || e.key === 'refresh_token' || e.key === 'user') {
        // Les tokens ont été modifiés dans un autre onglet
        checkAuthStatus();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [checkAuthStatus]);

  // Intercepteur pour les réponses 401 (non autorisé)
  useEffect(() => {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      
      if (response.status === 401 && isAuthenticated) {
        // Token expiré, essayer de le rafraîchir
        const refreshSuccess = await refreshTokenInternal();
        if (!refreshSuccess) {
          clearAuth();
        }
      }
      
      return response;
    };
    
    return () => {
      window.fetch = originalFetch;
    };
  }, [isAuthenticated]);

  const contextValue: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    login,
    signup,
    logout,
    refreshToken,
    updateUser,
    clearAuth,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;