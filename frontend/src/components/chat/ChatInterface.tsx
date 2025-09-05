// src/components/chat/ChatInterface.tsx - CONNECTÉ AU BACKEND
import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useChat } from '../../contexts/ChatProvider';
import MessageList from './MessageList';
import InputBox from './InputBox';
import ApiStatus from './ApiStatus';

// Interface Message UNIFIÉE pour tout le projet
export interface Message {
  id: number;
  type: 'user' | 'bot' | 'system';
  content: string;
  file?: File;
  timestamp: Date;
  isGenerating?: boolean;
}

const ChatInterface: React.FC = () => {
  const { messages, sendMessage, apiStatus, useStreaming } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas quand de nouveaux messages arrivent
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full max-w-6xl mx-auto">
      {/* Header avec status API */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex-shrink-0"
      >
        <div className="p-2 text-center border-b border-gray-200/10">
          <h2 className="text-lg font-semibold text-gray-100">
            Chat IA
          </h2>
          <p className="text-sm text-gray-400">
            Assistant intelligent
          </p>
        </div>
        
        {/* Status de l'API */}
        <ApiStatus />
      </motion.div>

      {/* Messages Area */}
      <div className="flex-1 px-6 py-4 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="text-center text-gray-400"
              >
                <div className="mb-4 text-6xl">🤖</div>
                <h3 className="mb-2 text-xl font-semibold">Assistant IA</h3>
                <p className="mb-4">
                  Tapez votre message pour commencer une conversation.
                </p>
                
                {/* Indicateurs de fonctionnalités */}
                <div className="flex flex-wrap justify-center gap-2 mt-6">
                  <span className="px-3 py-1 text-xs text-white bg-gray-600 rounded-full">
                    💬 Chat
                  </span>
                  <span className="px-3 py-1 text-xs text-white bg-gray-600 rounded-full">
                    📄 Documents
                  </span>
                  <span className="px-3 py-1 text-xs text-white bg-gray-600 rounded-full">
                    🔍 Analyse
                  </span>
                  <span className="px-3 py-1 text-xs text-white bg-gray-600 rounded-full">
                    📎 Fichiers
                  </span>
                </div>

                {/* Status de connexion */}
                <div className="mt-4">
                  {apiStatus.status === 'ok' && (
                    <div className="text-sm text-green-400">
                      ✅ Prêt
                    </div>
                  )}
                  {apiStatus.status === 'error' && (
                    <div className="text-sm text-red-400">
                      ❌ Service indisponible
                      <div className="mt-1 text-xs text-gray-500">
                        Réessayez plus tard
                      </div>
                    </div>
                  )}
                  {apiStatus.status === 'checking' && (
                    <div className="text-sm text-yellow-400">
                      🔄 Connexion...
                    </div>
                  )}
                </div>
              </motion.div>
            </div>
          ) : (
            <MessageList messages={messages} />
          )}
          
          {/* Référence pour l'auto-scroll */}
          <div ref={messagesEndRef} />
        </motion.div>
      </div>

      {/* Input Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="flex-shrink-0 p-6 border-t border-gray-200/10"
      >
        <InputBox 
          onSendMessage={sendMessage} 
          disabled={apiStatus.status === 'error'}
        />
        
        {/* Message d'aide si backend non disponible */}
        {apiStatus.status === 'error' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ duration: 0.3 }}
            className="p-3 mt-3 border rounded-lg bg-red-500/10 border-red-500/20"
          >
            <div className="text-sm text-red-400">
              <strong>Service indisponible</strong>
            </div>
            <div className="mt-1 text-xs text-gray-400">
              Réessayez plus tard.
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};

export default ChatInterface;