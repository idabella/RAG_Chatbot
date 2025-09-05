import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import logoBrand from '../assets/logoBrand.png'
import { 
  ArrowLeftIcon, 
  EyeIcon, 
  EyeSlashIcon,
  SparklesIcon,
  ShieldCheckIcon,
  UserIcon,
  LockClosedIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import Loading from '../components/common/Loading';

// API ConfigurationREACT_APP_API_BASE_URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_ENDPOINTS = {
  login: `${API_BASE_URL}/api/v1/auth/login`,
  register: `${API_BASE_URL}/api/v1/auth/register`,
};

// API Service
const authAPI = {
  async login(email, password) {
    try {
      const response = await fetch(API_ENDPOINTS.login, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle different error status codes
        if (response.status === 401) {
          throw new Error(data.detail || 'Email ou mot de passe incorrect');
        } else if (response.status === 400) {
          throw new Error(data.detail || 'Données invalides');
        } else if (response.status === 500) {
          throw new Error('Erreur du serveur. Veuillez réessayer plus tard.');
        } else {
          throw new Error(data.detail || `Erreur ${response.status}`);
        }
      }

      return {
        success: true,
        data: data,
        user: data.user,
        tokens: {
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          token_type: data.token_type,
          expires_in: data.expires_in
        }
      };
    } catch (error) {
      console.error('Login API Error:', error);
      return {
        success: false,
        error: error.message || 'Erreur de connexion au serveur'
      };
    }
  }
};

// Composants d'icônes Google et GitHub
const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
);

const GitHubIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
  </svg>
);

interface FormData {
  email: string;
  password: string;
}

interface Errors {
  email?: string;
  password?: string;
  general?: string;
}

const LoginPage: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Errors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  
  const { login: authContextLogin, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/chat';

  // Email validation function
  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Form validation
  const validateForm = (): boolean => {
    const newErrors: Errors = {};

    if (!formData.email.trim()) {
      newErrors.email = 'L\'adresse email est requise';
    } else if (!isValidEmail(formData.email.trim())) {
      newErrors.email = 'Format d\'email invalide';
    }

    if (!formData.password) {
      newErrors.password = 'Le mot de passe est requis';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Le mot de passe doit contenir au moins 6 caractères';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear previous errors
    setErrors({});
    
    // Validate form
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Call the API directly
      const apiResult = await authAPI.login(formData.email, formData.password);
      
      if (apiResult.success) {
        // Store tokens in localStorage/sessionStorage based on "remember me"
        const storage = rememberMe ? localStorage : sessionStorage;
        
        storage.setItem('access_token', apiResult.tokens.access_token);
        storage.setItem('refresh_token', apiResult.tokens.refresh_token);
        storage.setItem('token_type', apiResult.tokens.token_type);
        storage.setItem('user_data', JSON.stringify(apiResult.user));
        
        // If using AuthContext, update it as well
        if (authContextLogin) {
          const contextResult = await authContextLogin(formData.email, formData.password);
          if (!contextResult.success) {
            console.warn('AuthContext login failed, but API login succeeded');
          }
        }

        // Show success message (optional)
        console.log('Login successful:', apiResult.data.message);
        
        // Navigate to the intended page
        navigate(from, { replace: true });
        
      } else {
        // Handle API errors
        setErrors({ 
          general: apiResult.error || 'Erreur de connexion' 
        });
      }
    } catch (error) {
      console.error('Login error:', error);
      setErrors({ 
        general: 'Une erreur inattendue s\'est produite. Veuillez réessayer.' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear specific field error when user starts typing
    if (errors[name as keyof Errors]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    
    // Clear general error when user modifies form
    if (errors.general) {
      setErrors(prev => ({
        ...prev,
        general: ''
      }));
    }
  };

  // Handle social login (placeholder functions)
  const handleGoogleLogin = () => {
    console.log('Google login clicked - implement OAuth flow');
    // TODO: Implement Google OAuth
  };

  const handleGitHubLogin = () => {
    console.log('GitHub login clicked - implement OAuth flow');
    // TODO: Implement GitHub OAuth
  };

  const isSubmitDisabled = isLoading || authLoading || !formData.email.trim() || !formData.password;

  return (
    <div className="relative flex flex-col min-h-screen overflow-hidden bg-gradient-to-br from-gray-900 via-gray-950 to-gray-900">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        {Array.from({ length: 20 }, (_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 rounded-full bg-white/10"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -30, 0],
              opacity: [0.3, 0.8, 0.3],
            }}
            transition={{
              duration: Math.random() * 3 + 2,
              repeat: Infinity,
              ease: "easeInOut",
              delay: Math.random() * 2,
            }}
          />
        ))}
      </div>
      
      {/* Back to Home Button */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
        className="absolute z-50 top-4 left-4 sm:top-6 sm:left-6"
      >
        <Link
          to="/"
          className="flex items-center px-3 py-2 space-x-1 text-xs font-medium text-white transition-all duration-200 border shadow-lg sm:px-4 sm:py-2 sm:space-x-2 sm:text-sm hover:text-blue-200 hover:scale-105 bg-white/10 backdrop-blur-sm rounded-xl border-white/20"
        >
          <ArrowLeftIcon className="w-3 h-3 sm:w-4 sm:h-4" />
          <span className="hidden xs:inline sm:inline">Retour à l'accueil</span>
          <span className="xs:hidden sm:hidden">Retour</span>
        </Link>
      </motion.div>

      {/* Main Content */}
      <div className="relative z-10 flex items-center justify-center flex-1 p-4">
        <div className="grid items-center w-full max-w-6xl gap-12 mx-auto lg:grid-cols-2">
          {/* Left Side - Branding */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="hidden text-white lg:block"
          >
            <div className="flex items-center mb-8 space-x-3">
              <div className="flex items-center justify-center h-auto overflow-hidden w-28 rounded-xl ">
              <img 
                src={logoBrand}
                alt="FetChat Bot Logo" 
                className=""
              />
              </div>
              <div>
                <h1 
                  className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-[#e8d5ff] to-[#c084fc] text-transparent bg-clip-text font-[Poppins]"
                  style={{
                    filter: 'drop-shadow(0 0 12px rgba(192, 132, 252, 0.6)) drop-shadow(0 0 24px rgba(192, 132, 252, 0.3))'
                  }}
                >
                  FileChat
                </h1>
                <p className="text-blue-100">Intelligence Artificielle Avancée</p>
              </div>
            </div>

            <h2 className="mb-6 text-5xl font-bold leading-tight font-[poppins]">
              Bienvenue de retour !
            </h2>
            
            <p className="mb-8 text-xl leading-relaxed text-white">
              Reconnectez-vous à votre assistant IA intelligent et continuez vos conversations là où vous les avez laissées.
            </p>

            {/* Features List */}
            <div className="space-y-4">
              {[
                { icon: ShieldCheckIcon, text: 'Connexion sécurisée et chiffrée' },
                { icon: UserIcon, text: 'Accès à votre historique personnel' },
                { icon: SparklesIcon, text: 'IA personnalisée selon vos besoins' }
              ].map((feature, index) => (
                <motion.div
                  key={feature.text}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 + index * 0.1 }}
                  className="flex items-center space-x-3"
                >
                  <div className="flex items-center justify-center w-10 h-10 bg-white/20 rounded-xl">
                    <feature.icon className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-blue-100">{feature.text}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Right Side - Login Form */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="w-full max-w-md mx-auto lg:mx-0"
          >
            <div className="p-6 border shadow-2xl sm:p-8 bg-white/10 backdrop-blur-lg rounded-3xl border-white/20">
              {/* Mobile Logo - Only show on small screens */}
              <div className="flex items-center justify-center mb-6 lg:hidden">
                <div className="flex items-center space-x-3">
                  <img 
                    src={logoBrand}
                    alt="FileChat Logo" 
                    className="w-12 h-auto"
                  />
                  <h1 
                    className="text-2xl font-bold bg-gradient-to-r from-white via-[#e8d5ff] to-[#c084fc] text-transparent bg-clip-text font-[Poppins]"
                    style={{
                      filter: 'drop-shadow(0 0 8px rgba(192, 132, 252, 0.6))'
                    }}
                  >
                    FileChat
                  </h1>
                </div>
              </div>

              {/* Header */}
              <div className="mb-8 text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                  className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-400 to-purple-500 rounded-2xl"
                >
                  <LockClosedIcon className="w-8 h-8 text-white" />
                </motion.div>
                <h1 className="mb-2 text-3xl font-bold text-white">Connexion</h1>
                <p className="text-white">Accédez à votre espace FileChat</p>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-6" noValidate>
                {errors.general && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-4 text-sm text-red-100 border bg-red-800/20 border-red-200/30 rounded-xl backdrop-blur-sm"
                  >
                    <div className="flex items-center space-x-2">
                      <ExclamationTriangleIcon className="flex-shrink-0 w-4 h-4 text-red-400" />
                      <span>{errors.general}</span>
                    </div>
                  </motion.div>
                )}

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.5 }}
                >
                  <label htmlFor="email" className="block mb-2 text-sm font-medium text-white">
                    Adresse email *
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      autoComplete="email"
                      className={`w-full px-4 py-4 bg-blue-100 backdrop-blur-sm border rounded-xl text-black placeholder-purple-900 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 ${
                        errors.email ? 'border-red-400 focus:ring-red-400' : 'border-white/30'
                      }`}
                      placeholder="votre@email.com"
                      disabled={isLoading || authLoading}
                    />
                    <UserIcon className="absolute w-5 h-5 text-black transform -translate-y-1/2 right-4 top-1/2" />
                  </div>
                  {errors.email && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center mt-2 space-x-1 text-sm text-red-300"
                    >
                      <span className="w-1 h-1 bg-red-300 rounded-full"></span>
                      <span>{errors.email}</span>
                    </motion.p>
                  )}
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.6 }}
                >
                  <label htmlFor="password" className="block mb-2 text-sm font-medium text-white">
                    Mot de passe *
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      autoComplete="current-password"
                      className={`w-full px-4 py-4 bg-blue-100 backdrop-blur-sm border rounded-xl text-black placeholder-purple-900 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 pr-12 ${
                        errors.password ? 'border-red-400 focus:ring-red-400' : 'border-white/30'
                      }`}
                      placeholder="••••••••"
                      disabled={isLoading || authLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute text-black transition-colors duration-200 transform -translate-y-1/2 right-4 top-1/2 hover:text-gray-600"
                      disabled={isLoading || authLoading}
                    >
                      {showPassword ? (
                        <EyeSlashIcon className="w-5 h-5" />
                      ) : (
                        <EyeIcon className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {errors.password && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center mt-2 space-x-1 text-sm text-red-300"
                    >
                      <span className="w-1 h-1 bg-red-300 rounded-full"></span>
                      <span>{errors.password}</span>
                    </motion.p>
                  )}
                </motion.div>

                {/* Remember Me & Forgot Password */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.7 }}
                  className="flex items-center justify-between"
                >
                  <label className="flex items-center space-x-2 text-sm text-blue-200">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded bg-white/10 border-white/30 focus:ring-blue-500"
                      disabled={isLoading || authLoading}
                    />
                    <span className="text-white">Se souvenir de moi</span>
                  </label>
                  <a href="#" className="text-sm text-white transition-colors duration-200 hover:text-blue-300">
                    <span className="hidden sm:inline">Mot de passe oublié ?</span>
                    <span className="sm:hidden">Oublié ?</span>
                  </a>
                </motion.div>

                <motion.button
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.8 }}
                  whileHover={{ scale: isSubmitDisabled ? 1 : 1.02 }}
                  whileTap={{ scale: isSubmitDisabled ? 1 : 0.98 }}
                  type="submit"
                  disabled={isSubmitDisabled}
                  className={`flex items-center justify-center w-full px-6 py-4 space-x-2 font-semibold text-white transition-all duration-200 shadow-lg rounded-xl focus:outline-none focus:ring-2 focus:ring-white/50 touch-manipulation ${
                    isSubmitDisabled 
                      ? 'bg-gray-500/50 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700'
                  }`}
                >
                  {(isLoading || authLoading) ? (
                    <Loading size="sm" color="blue" />
                  ) : (
                    <>
                      <LockClosedIcon className="w-5 h-5" />
                      <span>Se Connecter</span>
                    </>
                  )}
                </motion.button>
              </form>

              {/* Footer */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.9 }}
                className="mt-8 text-center"
              >
                <p className="mb-4 text-white">
                  Pas encore de compte ?{' '}
                  <Link
                    to="/signup"
                    className="font-medium text-white underline transition-colors duration-200 hover:text-blue-300 decoration-blue-300 touch-manipulation"
                  >
                    Créer un compte
                  </Link>
                </p>
                
                {/* Social Login */}
                <div className="space-y-3">
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-white/20"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 text-blue-200 bg-transparent">Ou continuer avec</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <button 
                      onClick={handleGoogleLogin}
                      disabled={isLoading || authLoading}
                      className="flex items-center justify-center px-4 py-3 space-x-2 text-white transition-all duration-200 border bg-white/10 border-white/20 rounded-xl hover:bg-white/20 hover:scale-105 touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <GoogleIcon />
                      <span className="text-sm font-medium">Google</span>
                    </button>
                    <button 
                      onClick={handleGitHubLogin}
                      disabled={isLoading || authLoading}
                      className="flex items-center justify-center px-4 py-3 space-x-2 text-white transition-all duration-200 border bg-white/10 border-white/20 rounded-xl hover:bg-white/20 hover:scale-105 touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <GitHubIcon />
                      <span className="text-sm font-medium">GitHub</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;