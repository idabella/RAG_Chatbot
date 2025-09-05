// src/components/chat/ApiStatus.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  ClockIcon,
  WifiIcon
} from '@heroicons/react/24/outline';
import { useChat } from '../../contexts/ChatProvider';

const ApiStatus: React.FC = () => {
  const { apiStatus, useStreaming, toggleStreaming } = useChat();

  const getStatusIcon = () => {
    switch (apiStatus.status) {
      case 'ok':
        return CheckCircleIcon;
      case 'error':
        return ExclamationTriangleIcon;
      case 'checking':
        return ClockIcon;
      default:
        return WifiIcon;
    }
  };

  const getStatusColor = () => {
    switch (apiStatus.status) {
      case 'ok':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      case 'checking':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusBg = () => {
    switch (apiStatus.status) {
      case 'ok':
        return 'bg-green-400/10 border-green-400/20';
      case 'error':
        return 'bg-red-400/10 border-red-400/20';
      case 'checking':
        return 'bg-yellow-400/10 border-yellow-400/20';
      default:
        return 'bg-gray-400/10 border-gray-400/20';
    }
  };

  const StatusIcon = getStatusIcon();

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex items-center justify-between p-3 mx-6 mt-4 rounded-lg border ${getStatusBg()}`}
    >
      <div className="flex items-center space-x-3">
        <motion.div
          animate={apiStatus.status === 'checking' ? { rotate: 360 } : {}}
          transition={{ duration: 2, repeat: apiStatus.status === 'checking' ? Infinity : 0 }}
        >
          <StatusIcon className={`w-5 h-5 ${getStatusColor()}`} />
        </motion.div>
        
        <div>
          <div className={`text-sm font-medium ${getStatusColor()}`}>
            {apiStatus.status === 'ok' ? 'Connecté' : 
             apiStatus.status === 'error' ? 'Déconnecté' : 'Connexion...'}
          </div>
          <div className="text-xs text-gray-400">
            {apiStatus.message}
          </div>
        </div>
      </div>

      {/* Toggle pour le mode streaming */}
      {apiStatus.status === 'ok' && (
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-400">Streaming</span>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleStreaming}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
              useStreaming ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <motion.span
              animate={{ x: useStreaming ? 20 : 2 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              className="inline-block w-4 h-4 transform bg-white rounded-full"
            />
          </motion.button>
        </div>
      )}
    </motion.div>
  );
};

export default ApiStatus;