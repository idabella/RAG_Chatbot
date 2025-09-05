import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import logoBrand from '../assets/logoBrand.png'
import { 
  ArrowLeftIcon, 
  EyeIcon, 
  EyeSlashIcon,
  SparklesIcon,
  UserPlusIcon,
  UserIcon,
  EnvelopeIcon,
  LockClosedIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import Loading from '../components/common/Loading';

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

// Configuration de l'API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface FormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface Errors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}

// Interface pour la réponse de l'API
interface RegisterResponse {
  message: string;
  user: {
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
  };
  access_token: string;
  refresh_token: string;
  token_type: string;
}

const SignupPage: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<Errors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const { signup, loading } = useAuth();
  const navigate = useNavigate();

  const passwordRequirements = [
    { text: 'Au moins 8 caractères', met: formData.password.length >= 8 },
    { text: 'Une lettre majuscule', met: /[A-Z]/.test(formData.password) },
    { text: 'Une lettre minuscule', met: /[a-z]/.test(formData.password) },
    { text: 'Un chiffre', met: /\d/.test(formData.password) },
  ];

  // Validation des données du formulaire
  const validateForm = (): boolean => {
    const newErrors: Errors = {};

    // Validation du nom
    if (!formData.name.trim()) {
      newErrors.name = 'Le nom est requis';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Le nom doit contenir au moins 2 caractères';
    }

    // Validation de l'email
    if (!formData.email.trim()) {
      newErrors.email = 'L\'email est requis';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Format d\'email invalide';
    }

    // Validation du mot de passe
    if (!formData.password) {
      newErrors.password = 'Le mot de passe est requis';
    } else {
      if (formData.password.length < 8) {
        newErrors.password = 'Le mot de passe doit contenir au moins 8 caractères';
      } else if (!passwordRequirements.every(req => req.met)) {
        newErrors.password = 'Le mot de passe ne respecte pas tous les critères';
      }
    }

    // Validation de la confirmation du mot de passe
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'La confirmation du mot de passe est requise';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
    }

    // Validation des conditions d'utilisation
    if (!termsAccepted) {
      newErrors.general = 'Vous devez accepter les conditions d\'utilisation';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Fonction pour appeler l'API d'inscription
  const registerUser = async (userData: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }): Promise<RegisterResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur HTTP ${response.status}`);
    }

    return response.json();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      // Diviser le nom complet en prénom et nom
      const nameParts = formData.name.trim().split(' ');
      const firstName = nameParts[0];
      const lastName = nameParts.slice(1).join(' ') || '';

      // Préparer les données pour l'API
      const registrationData = {
        first_name: firstName,
        last_name: lastName,
        email: formData.email.toLowerCase().trim(),
        password: formData.password,
      };

      // Appeler l'API d'inscription
      const response = await registerUser(registrationData);

      // Stocker les tokens dans le localStorage
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      // Si vous utilisez un contexte d'authentification, vous pouvez également l'utiliser ici
      if (signup) {
        const result = await signup(formData.name, formData.email, formData.password);
        if (!result.success) {
          console.warn('Contexte d\'authentification a échoué, mais l\'API a réussi');
        }
      }

      // Redirection vers la page de chat
      navigate('/chat', { 
        state: { 
          message: 'Compte créé avec succès ! Bienvenue sur FileChat.',
          user: response.user 
        } 
      });

    } catch (error) {
      console.error('Erreur lors de l\'inscription:', error);
      
      let errorMessage = 'Une erreur inattendue s\'est produite';
      
      if (error instanceof Error) {
        errorMessage = error.message;
      }

      // Gestion des erreurs spécifiques
      if (errorMessage.includes('existe déjà')) {
        setErrors({ email: 'Un compte avec cet email existe déjà' });
      } else if (errorMessage.includes('format') || errorMessage.includes('invalid')) {
        setErrors({ email: 'Format d\'email invalide' });
      } else if (errorMessage.includes('mot de passe') || errorMessage.includes('password')) {
        setErrors({ password: 'Le mot de passe ne respecte pas les critères requis' });
      } else {
        setErrors({ general: errorMessage });
      }

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

    // Clear error when user starts typing
    if (errors[name as keyof Errors]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Clear general error when user makes changes
    if (errors.general) {
      setErrors(prev => ({ ...prev, general: '' }));
    }
  };

  const nextStep = () => {
    // Validation de l'étape 1
    const stepOneErrors: Errors = {};
    
    if (!formData.name.trim()) {
      stepOneErrors.name = 'Le nom est requis';
    } else if (formData.name.trim().length < 2) {
      stepOneErrors.name = 'Le nom doit contenir au moins 2 caractères';
    }

    if (!formData.email.trim()) {
      stepOneErrors.email = 'L\'email est requis';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      stepOneErrors.email = 'Format d\'email invalide';
    }

    if (Object.keys(stepOneErrors).length > 0) {
      setErrors(stepOneErrors);
      return;
    }

    setCurrentStep(2);
  };

  const prevStep = () => {
    if (currentStep === 2) {
      setCurrentStep(1);
    }
  };

  return (
    <div className="relative flex items-center justify-center min-h-screen p-4 overflow-hidden bg-gradient-to-br from-gray-900 via-gray-950 to-gray-900">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        {Array.from({ length: 25 }, (_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 rounded-full bg-white/10"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -40, 0],
              opacity: [0.2, 0.8, 0.2],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: Math.random() * 4 + 3,
              repeat: Infinity,
              ease: "easeInOut",
              delay: Math.random() * 3,
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

      <div className="relative z-10 grid items-center w-full max-w-6xl gap-12 mx-auto lg:grid-cols-2">
        {/* Left Side - Branding */}
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="hidden text-white lg:block"
        >
          <div className="flex items-center pl-20 mb-8 space-x-3">
            <div className="flex items-center justify-center h-auto overflow-hidden w-28 rounded-xl ">
            <img 
              src={logoBrand}
              alt="FetChat Bot Logo" 
              className=""
            />
            </div>
            <div>
              <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-[#e8d5ff] to-[#c084fc] text-transparent bg-clip-text font-[Poppins] drop-shadow-sm" style={{textShadow: '0 0 20px rgba(192, 132, 252, 0.5), 0 0 40px rgba(192, 132, 252, 0.3)'}}>
              FileChat
              </h1>
              <p className="text-blue-200">Votre Assistant IA Personnel</p>
            </div>
          </div>

          <h2 className="mb-7 text-5xl font-bold leading-tight font-[poppins] text-center">
            <p>Rejoignez la révolution</p><p>IA !</p>
          </h2>
          
          <p className="mb-8 text-xl leading-relaxed text-blue-100">
            Créez votre compte et découvrez comment FetChat peut transformer votre façon de travailler avec les documents.
          </p>

          {/* Benefits */}
          <div className="space-y-6">
            {[
              { 
                title: 'Support 24/7 en français',
                description: 'Notre équipe est là pour vous accompagner',
                icon: '🇫🇷'
              },
              { 
                title: 'Sécurité de niveau entreprise',
                description: 'Vos données sont protégées et chiffrées',
                icon: '🔒'
              }
            ].map((benefit, index) => (
              <motion.div
                key={benefit.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.3 + index * 0.1 }}
                className="flex items-start p-4 space-x-4 border bg-white/10 rounded-xl backdrop-blur-sm border-white/20"
              >
                <span className="text-2xl">{benefit.icon}</span>
                <div>
                  <h3 className="mb-1 font-semibold text-white">{benefit.title}</h3>
                  <p className="text-sm text-white">{benefit.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Right Side - Signup Form */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="w-full max-w-md mx-auto lg:mx-0"
        >
          <div className="p-6 border shadow-2xl sm:p-8 bg-white/10 backdrop-blur-lg rounded-3xl border-white/20">
            {/* Header */}
            <div className="mb-8 text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-700 to-purple-500 rounded-2xl"
              >
                <UserPlusIcon className="w-8 h-8 text-white" />
              </motion.div>
              <h1 className="mb-2 text-2xl font-bold text-white sm:text-3xl">Créer un compte</h1>
              <p className="text-sm text-white sm:text-base">Rejoignez des milliers d'utilisateurs satisfaits</p>
              
              {/* Progress Indicator */}
              <div className="flex items-center justify-center mt-4 space-x-2">
                <div className={`w-3 h-3 rounded-full transition-all duration-300 ${
                  currentStep >= 1 ? 'bg-blue-400' : 'bg-white/30'
                }`} />
                <div className={`w-8 h-1 rounded-full transition-all duration-300 ${
                  currentStep >= 2 ? 'bg-blue-400' : 'bg-white/30'
                }`} />
                <div className={`w-3 h-3 rounded-full transition-all duration-300 ${
                  currentStep >= 2 ? 'bg-blue-400' : 'bg-white/30'
                }`} />
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {errors.general && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-4 text-sm text-red-100 border bg-red-500/20 border-red-500/30 rounded-xl backdrop-blur-sm"
                >
                  <div className="flex items-center space-x-2">
                    <XMarkIcon className="flex-shrink-0 w-4 h-4 text-red-400" />
                    <span>{errors.general}</span>
                  </div>
                </motion.div>
              )}

              {/* Step 1: Personal Info */}
              {currentStep === 1 && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-6"
                >
                  <div>
                    <label htmlFor="name" className="block mb-2 text-sm font-medium text-white">
                      Nom complet
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className={`w-full px-4 py-4 bg-blue-100 backdrop-blur-sm border rounded-xl text-black placeholder-purple-900 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 ${
                          errors.name ? 'border-red-400' : 'border-white/30'
                        }`}
                        placeholder="Votre nom complet"
                      />
                      <UserIcon className="absolute w-5 h-5 text-black transform -translate-y-1/2 right-4 top-1/2" />
                    </div>
                    {errors.name && (
                      <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center mt-2 space-x-1 text-sm text-red-300"
                      >
                        <span className="w-1 h-1 bg-red-300 rounded-full"></span>
                        <span>{errors.name}</span>
                      </motion.p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="email" className="block mb-2 text-sm font-medium text-white">
                      Adresse email
                    </label>
                    <div className="relative">
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className={`w-full px-4 py-4 bg-blue-100 backdrop-blur-sm border rounded-xl text-black placeholder-purple-900 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 ${
                          errors.email ? 'border-red-400' : 'border-white/30'
                        }`}
                        placeholder="votre@email.com"
                      />
                      <EnvelopeIcon className="absolute w-5 h-5 text-black transform -translate-y-1/2 right-4 top-1/2" />
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
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="button"
                    onClick={nextStep}
                    disabled={!formData.name || !formData.email}
                    className="flex items-center justify-center w-full px-6 py-4 space-x-2 font-semibold text-white transition-all duration-200 shadow-lg bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-white/50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span>Continuer</span>
                    <ArrowLeftIcon className="w-5 h-5 rotate-180" />
                  </motion.button>
                </motion.div>
              )}

              {/* Step 2: Password */}
              {currentStep === 2 && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-6"
                >
                  <div>
                    <label htmlFor="password" className="block mb-2 text-sm font-medium text-white">
                      Mot de passe
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        id="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        className={`w-full px-4 py-4 bg-blue-100 backdrop-blur-sm border rounded-xl text-black placeholder-purple-900 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 pr-12 ${
                          errors.password ? 'border-red-400' : 'border-white/30'
                        }`}
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute text-black transition-colors duration-200 transform -translate-y-1/2 right-4 top-1/2"
                      >
                        {showPassword ? (
                          <EyeSlashIcon className="w-5 h-5" />
                        ) : (
                          <EyeIcon className="w-5 h-5" />
                        )}
                      </button>
                    </div>

                    {/* Password Requirements */}
                    {formData.password && (
                      <div className="mt-3 space-y-2">
                        {passwordRequirements.map((req, index) => (
                          <div key={index} className="flex items-center space-x-2 text-sm">
                            {req.met ? (
                              <CheckIcon className="w-4 h-4 text-green-400" />
                            ) : (
                              <XMarkIcon className="w-4 h-4 text-red-400" />
                            )}
                            <span className={req.met ? 'text-green-300' : 'text-red-300'}>
                              {req.text}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

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
                  </div>

                  <div>
                    <label htmlFor="confirmPassword" className="block mb-2 text-sm font-medium text-white">
                      Confirmer le mot de passe
                    </label>
                    <div className="relative">
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        id="confirmPassword"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        className={`w-full px-4 py-4 backdrop-blur-sm border rounded-xl text-black placeholder-purple-950 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 pr-12 ${
                          errors.confirmPassword ? 'border-red-400' : 'border-white/30 bg-blue-100'
                        }`}
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute text-black transition-colors duration-200 transform -translate-y-1/2 right-4 top-1/2"
                      >
                        {showConfirmPassword ? (
                          <EyeSlashIcon className="w-5 h-5" />
                        ) : (
                          <EyeIcon className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                    {errors.confirmPassword && (
                      <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center mt-2 space-x-1 text-sm text-red-300"
                      >
                        <span className="w-1 h-1 bg-red-300 rounded-full"></span>
                        <span>{errors.confirmPassword}</span>
                      </motion.p>
                    )}
                  </div>

                  {/* Terms and Conditions */}
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      id="terms"
                      checked={termsAccepted}
                      onChange={(e) => setTermsAccepted(e.target.checked)}
                      className="w-4 h-4 mt-1 text-blue-600 rounded bg-white/10 border-white/30 focus:ring-blue-500"
                      required
                    />
                    <label htmlFor="terms" className="text-sm text-white">
                      J'accepte les{' '}
                      <a href="#" className="text-white underline hover:text-blue-200">
                        conditions d'utilisation
                      </a>{' '}
                      et la{' '}
                      <a href="#" className="text-white underline hover:text-blue-200">
                        politique de confidentialité
                      </a>
                    </label>
                  </div>

                  <div className="flex space-x-3">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="button"
                      onClick={prevStep}
                      className="flex items-center justify-center flex-1 px-6 py-4 space-x-2 font-semibold text-white transition-all duration-200 border bg-white/10 rounded-xl hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/50 border-white/20"
                    >
                      <ArrowLeftIcon className="w-5 h-5" />
                      <span>Retour</span>
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="submit"
                      disabled={loading || isLoading || !termsAccepted}
                      className="flex items-center justify-center flex-1 px-6 py-4 space-x-2 font-semibold text-white transition-all duration-200 shadow-lg bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-white/50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading || isLoading ? (
                        <Loading size="sm" color="blue" />
                      ) : (
                        <>
                          <UserPlusIcon className="w-5 h-5" />
                          <span>Créer mon compte</span>
                        </>
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </form>

            {/* Footer */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.9 }}
              className="mt-8 text-center"
            >
              <p className="mb-4 text-sm text-blue-200 sm:text-base">
                Déjà un compte ?{' '}
                <Link
                  to="/login"
                  className="font-medium text-white underline transition-colors duration-200 hover:text-blue-200 decoration-blue-300"
                >
                  Se connecter
                </Link>
              </p>
              
              {/* Social Signup */}
              {currentStep === 1 && (
                <div className="space-y-3">
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-white/20"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 text-blue-200 bg-transparent">Ou s'inscrire avec</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <button 
                      type="button"
                      className="flex items-center justify-center px-3 py-3 space-x-2 text-sm font-medium text-white transition-all duration-200 border sm:px-4 bg-white/10 border-white/20 rounded-xl hover:bg-white/20 hover:scale-105"
                    >
                      <GoogleIcon />
                      <span>Google</span>
                    </button>
                    <button 
                      type="button"
                      className="flex items-center justify-center px-3 py-3 space-x-2 text-sm font-medium text-white transition-all duration-200 border sm:px-4 bg-white/10 border-white/20 rounded-xl hover:bg-white/20 hover:scale-105"
                    >
                      <GitHubIcon />
                      <span>GitHub</span>
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default SignupPage;