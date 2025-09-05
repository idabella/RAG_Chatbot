// src/components/chat/MessageItem.tsx - CORRIGÉ pour éviter le débordement
import React from 'react';
import { motion } from 'framer-motion';
import { 
  UserIcon, 
  CpuChipIcon, 
  DocumentIcon,
  PhotoIcon,
  ClipboardDocumentIcon
} from '@heroicons/react/24/outline';

interface Message {
  id: number;
  type: 'user' | 'bot' | 'system';
  content: string;
  file?: File;
  timestamp: Date;
  isGenerating?: boolean;
}

interface MessageItemProps {
  message: Message;
}

// Composant pour l'indicateur de frappe
const TypingIndicator: React.FC = () => (
  <div className="flex items-center space-x-2 text-gray-400">
    <div className="flex space-x-1">
      <motion.div
        className="w-2 h-2 bg-gray-500 rounded-full"
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 1, repeat: Infinity, delay: 0 }}
      />
      <motion.div
        className="w-2 h-2 bg-gray-500 rounded-full"
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
      />
      <motion.div
        className="w-2 h-2 bg-gray-500 rounded-full"
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
      />
    </div>
    <span className="text-sm">  </span>
  </div>
);

const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isUser = message.type === 'user';
  const isBot = message.type === 'bot';
  const isSystem = message.type === 'system';

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return PhotoIcon;
    if (file.type.includes('pdf') || file.type.includes('document')) return DocumentIcon;
    return ClipboardDocumentIcon;
  };

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Message système
  if (isSystem) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex justify-center my-6"
      >
        <div className="max-w-full px-4 py-2 text-sm text-gray-400 border rounded-full bg-gray-800/50 border-gray-700/50">
          <div className="break-words">{message.content}</div>
        </div>
      </motion.div>
    );
  }

  // Messages utilisateur et bot
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, type: "spring", stiffness: 100 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 w-full`}
    >
      <div className={`flex items-start space-x-3 max-w-[85%] min-w-0 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        
        {/* Avatar - seulement pour les messages utilisateur */}
        {isUser && (
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="flex items-center justify-center flex-shrink-0 w-8 h-8 mt-1 rounded-full shadow-lg bg-gradient-to-br from-gray-800 to-gray-900"
          >
            <UserIcon className="w-4 h-4 text-white" />
          </motion.div>
        )}

        {/* Contenu du message */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-2 min-w-0 flex-1`}>
          
          {/* Message Bubble */}
          <motion.div
            whileHover={{ scale: 1.01 }}
            className={`relative px-4 py-3 rounded-2xl shadow-lg backdrop-blur-sm min-w-0 max-w-full ${
              isUser
                ? 'bg-gradient-to-br from-gray-700 to-gray-600 text-white rounded-br-none'
                : 'bg-gray-800/80 border border-gray-700/50 text-gray-100 rounded-bl-none'
            }`}
          >
            {/* Message content or typing indicator */}
            {message.isGenerating ? (
              <TypingIndicator />
            ) : (
              <>
                {/* File attachment display */}
                {message.file && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex items-center min-w-0 p-3 mb-3 border rounded-tr-none bg-black/20 border-white/10 rounded-xl"
                  >
                    {React.createElement(getFileIcon(message.file), { 
                      className: "h-5 w-5 mr-2 flex-shrink-0" 
                    })}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{message.file.name}</p>
                      <p className="text-xs opacity-75">
                        {(message.file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </motion.div>
                )}

                {/* Message text - CORRIGÉ pour éviter le débordement */}
                <div className="min-w-0 text-sm leading-relaxed break-words whitespace-pre-wrap overflow-wrap-anywhere hyphens-auto">
                  {message.content}
                </div>

                {/* Message enhancements for bot messages */}
                {isBot && !message.isGenerating && (
                  <div className="flex items-center justify-between pt-2 mt-3 border-t border-gray-700/30">
                    <span className="text-xs text-gray-400">
                      Réponse générée
                    </span>
                    <div className="flex space-x-2">
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        className="p-1 text-gray-400 transition-colors hover:text-green-400"
                        title="Copier la réponse"
                        onClick={() => navigator.clipboard.writeText(message.content)}
                      >
                        <ClipboardDocumentIcon className="w-4 h-4" />
                      </motion.button>
                    </div>
                  </div>
                )}
              </>
            )}
          </motion.div>

          {/* Timestamp */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className={`text-xs text-gray-500 ${isUser ? 'text-right' : 'text-left'}`}
          >
            {formatTime(message.timestamp)}
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

export default MessageItem;