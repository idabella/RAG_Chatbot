// src/pages/SettingsPage.tsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CogIcon,
  KeyIcon,
  PaintBrushIcon,
  BellIcon,
  TrashIcon,
  DocumentArrowUpIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import Layout from '../components/common/Layout';
import { useChat } from '../contexts/ChatProvider';

interface SettingsData {
  apiKey: string;
  theme: 'dark' | 'light';
  notifications: boolean;
  autoSave: boolean;
  maxFileSize: number;
  language: string;
  responseLength: 'short' | 'medium' | 'long';
  temperature: number;
}

const SettingsPage: React.FC = () => {
  const { conversations, apiStatus } = useChat();
  const [showApiKey, setShowApiKey] = useState(false);
  const [settings, setSettings] = useState<SettingsData>({
    apiKey: '',
    theme: 'dark',
    notifications: true,
    autoSave: true,
    maxFileSize: 10,
    language: 'fr',
    responseLength: 'medium',
    temperature: 0.7
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Charger les paramètres au démarrage
  useEffect(() => {
    // Simuler le chargement des paramètres depuis le stockage local
    const savedSettings = {
      ...settings,
      apiKey: '' // Valeur depuis votre .env
    };
    setSettings(savedSettings);
  }, []);

  const handleInputChange = (key: keyof SettingsData, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveSettings = async () => {
    setIsSaving(true);
    try {
      // Simuler la sauvegarde des paramètres
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Ici vous pourriez sauvegarder dans localStorage ou envoyer à un serveur
      console.log('Paramètres sauvegardés:', settings);
      
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearAllData = () => {
    if (showDeleteConfirm) {
      // Logique pour supprimer toutes les données
      console.log('Suppression de toutes les données...');
      setShowDeleteConfirm(false);
      // Vous pouvez appeler une fonction du context pour nettoyer les conversations
    } else {
      setShowDeleteConfirm(true);
    }
  };

  const getApiStatusIcon = () => {
    switch (apiStatus.status) {
      case 'ok':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'checking':
        return <div className="w-5 h-5 border-2 border-blue-500 rounded-full border-t-transparent animate-spin" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
    }
  };

  return (
    <Layout>
      {/* CORRECTION: Container avec scroll approprié */}
      <div className="h-[calc(100vh-4rem)] overflow-y-auto bg-gradient-to-br from-gray-900 via-gray-950 to-gray-900">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative"
        >
          {/* CORRECTION: Padding et max-width pour le contenu */}
          <div className="max-w-6xl px-6 py-8 mx-auto">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mb-8"
            >
              <div className="flex items-center mb-2 space-x-4">
                <div className="p-3 bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl">
                  <CogIcon className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-white">Paramètres</h1>
                  <p className="text-gray-300">Configurez votre expérience FileChat</p>
                </div>
              </div>
            </motion.div>

            {/* CORRECTION: Grid responsive amélioré */}
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
              {/* Colonne principale */}
              <div className="space-y-6 xl:col-span-2">
                
                {/* Section API */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.1 }}
                  className="p-6 border bg-white/10 backdrop-blur-md rounded-2xl border-white/20"
                >
                  <div className="flex items-center mb-4 space-x-3">
                    <KeyIcon className="w-6 h-6 text-blue-400" />
                    <h2 className="text-xl font-semibold text-white">Configuration API</h2>
                    {getApiStatusIcon()}
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-300">
                        Clé API Hugging Face
                      </label>
                      <div className="relative">
                        <input
                          type={showApiKey ? "text" : "password"}
                          value={settings.apiKey}
                          onChange={(e) => handleInputChange('apiKey', e.target.value)}
                          className="w-full px-4 py-3 pr-12 text-white placeholder-gray-400 transition-colors border border-gray-600 bg-black/30 rounded-xl focus:border-blue-500 focus:outline-none"
                          placeholder="hf_..."
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiKey(!showApiKey)}
                          className="absolute text-gray-400 transition-colors -translate-y-1/2 right-3 top-1/2 hover:text-white"
                        >
                          {showApiKey ? (
                            <EyeSlashIcon className="w-5 h-5" />
                          ) : (
                            <EyeIcon className="w-5 h-5" />
                          )}
                        </button>
                      </div>
                      <div className="flex items-center mt-2 text-sm">
                        {getApiStatusIcon()}
                        <span className={`ml-2 ${
                          apiStatus.status === 'ok' ? 'text-green-400' :
                          apiStatus.status === 'error' ? 'text-red-400' : 'text-yellow-400'
                        }`}>
                          {apiStatus.message}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>

                {/* Section Personnalisation */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  className="p-6 border bg-white/10 backdrop-blur-md rounded-2xl border-white/20"
                >
                  <div className="flex items-center mb-4 space-x-3">
                    <PaintBrushIcon className="w-6 h-6 text-purple-400" />
                    <h2 className="text-xl font-semibold text-white">Personnalisation</h2>
                  </div>
                  
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-300">
                        Thème
                      </label>
                      <select
                        value={settings.theme}
                        onChange={(e) => handleInputChange('theme', e.target.value)}
                        className="w-full px-4 py-3 text-white transition-colors border border-gray-600 bg-black/30 rounded-xl focus:border-blue-500 focus:outline-none"
                      >
                        <option value="dark">Sombre</option>
                        <option value="light">Clair</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-300">
                        Langue
                      </label>
                      <select
                        value={settings.language}
                        onChange={(e) => handleInputChange('language', e.target.value)}
                        className="w-full px-4 py-3 text-white transition-colors border border-gray-600 bg-black/30 rounded-xl focus:border-blue-500 focus:outline-none"
                      >
                        <option value="fr">Français</option>
                        <option value="en">English</option>
                        <option value="es">Español</option>
                      </select>
                    </div>
                  </div>
                </motion.div>

                {/* Section IA */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.3 }}
                  className="p-6 border bg-white/10 backdrop-blur-md rounded-2xl border-white/20"
                >
                  <div className="flex items-center mb-4 space-x-3">
                    <ChatBubbleLeftRightIcon className="w-6 h-6 text-green-400" />
                    <h2 className="text-xl font-semibold text-white">Paramètres IA</h2>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-300">
                        Longueur des réponses
                      </label>
                      <select
                        value={settings.responseLength}
                        onChange={(e) => handleInputChange('responseLength', e.target.value)}
                        className="w-full px-4 py-3 text-white transition-colors border border-gray-600 bg-black/30 rounded-xl focus:border-blue-500 focus:outline-none"
                      >
                        <option value="short">Courte</option>
                        <option value="medium">Moyenne</option>
                        <option value="long">Longue</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-300">
                        Créativité (Temperature): {settings.temperature}
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="1.0"
                        step="0.1"
                        value={settings.temperature}
                        onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
                        className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
                      />
                      <div className="flex justify-between mt-1 text-xs text-gray-400">
                        <span>Précis</span>
                        <span>Créatif</span>
                      </div>
                    </div>
                  </div>
                </motion.div>

                {/* Section Fichiers */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 }}
                  className="p-6 border bg-white/10 backdrop-blur-md rounded-2xl border-white/20"
                >
                  <div className="flex items-center mb-4 space-x-3">
                    <DocumentArrowUpIcon className="w-6 h-6 text-orange-400" />
                    <h2 className="text-xl font-semibold text-white">Gestion des fichiers</h2>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-300">
                        Taille maximale des fichiers (MB)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={settings.maxFileSize}
                        onChange={(e) => handleInputChange('maxFileSize', parseInt(e.target.value))}
                        className="w-full px-4 py-3 text-white transition-colors border border-gray-600 bg-black/30 rounded-xl focus:border-blue-500 focus:outline-none"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-white">Sauvegarde automatique</h3>
                        <p className="text-sm text-gray-400">Sauvegarder automatiquement les conversations</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={settings.autoSave}
                          onChange={(e) => handleInputChange('autoSave', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Colonne sidebar */}
              <div className="space-y-6">
                
                {/* Statistiques */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  className="p-6 border bg-white/10 backdrop-blur-md rounded-2xl border-white/20"
                >
                  <h3 className="mb-4 text-lg font-semibold text-white">Statistiques</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-300">Conversations</span>
                      <span className="font-medium text-white">{conversations.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-300">Messages totaux</span>
                      <span className="font-medium text-white">
                        {conversations.reduce((acc, conv) => acc + conv.messages.length, 0)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-300">Statut API</span>
                      <span className={`font-medium ${
                        apiStatus.status === 'ok' ? 'text-green-400' :
                        apiStatus.status === 'error' ? 'text-red-400' : 'text-yellow-400'
                      }`}>
                        {apiStatus.status === 'ok' ? 'Connecté' :
                         apiStatus.status === 'error' ? 'Erreur' : 'Vérification...'}
                      </span>
                    </div>
                  </div>
                </motion.div>

                {/* Notifications */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.3 }}
                  className="p-6 border bg-white/10 backdrop-blur-md rounded-2xl border-white/20"
                >
                  <div className="flex items-center mb-4 space-x-3">
                    <BellIcon className="w-6 h-6 text-yellow-400" />
                    <h3 className="text-lg font-semibold text-white">Notifications</h3>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-white">Notifications push</p>
                      <p className="text-sm text-gray-400">Recevoir des notifications</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.notifications}
                        onChange={(e) => handleInputChange('notifications', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </motion.div>

                {/* Actions */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 }}
                  className="p-6 border bg-white/10 backdrop-blur-md rounded-2xl border-white/20"
                >
                  <h3 className="mb-4 text-lg font-semibold text-white">Actions</h3>
                  <div className="space-y-3">
                    <button
                      onClick={handleSaveSettings}
                      disabled={isSaving}
                      className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-xl font-medium transition-all duration-200 ${
                        saveStatus === 'success' 
                          ? 'bg-green-600 text-white' 
                          : saveStatus === 'error'
                          ? 'bg-red-600 text-white'
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      } ${isSaving ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {isSaving ? (
                        <div className="w-5 h-5 border-2 border-white rounded-full border-t-transparent animate-spin" />
                      ) : saveStatus === 'success' ? (
                        <CheckCircleIcon className="w-5 h-5" />
                      ) : saveStatus === 'error' ? (
                        <XCircleIcon className="w-5 h-5" />
                      ) : (
                        <CogIcon className="w-5 h-5" />
                      )}
                      <span>
                        {isSaving ? 'Sauvegarde...' :
                         saveStatus === 'success' ? 'Sauvegardé !' :
                         saveStatus === 'error' ? 'Erreur' : 'Sauvegarder'}
                      </span>
                    </button>
                    
                    <button
                      onClick={handleClearAllData}
                      className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-xl font-medium transition-all duration-200 ${
                        showDeleteConfirm 
                          ? 'bg-red-600 hover:bg-red-700 text-white' 
                          : 'bg-gray-600 hover:bg-gray-700 text-white'
                      }`}
                    >
                      <TrashIcon className="w-5 h-5" />
                      <span>{showDeleteConfirm ? 'Confirmer suppression' : 'Effacer toutes les données'}</span>
                    </button>
                    
                    {showDeleteConfirm && (
                      <button
                        onClick={() => setShowDeleteConfirm(false)}
                        className="w-full px-4 py-2 text-sm text-gray-300 transition-colors hover:text-white"
                      >
                        Annuler
                      </button>
                    )}
                  </div>
                </motion.div>
              </div>
            </div>

            {/* AJOUT: Padding en bas pour éviter que le contenu soit coupé */}
            <div className="h-8"></div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
};

export default SettingsPage;