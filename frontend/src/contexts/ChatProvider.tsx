// src/contexts/ChatProvider.tsx - VERSION CONNECTÉE AU BACKEND
import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { chatApiService } from '../services/chatApi';

export interface Message {
  id: number;
  type: 'user' | 'bot' | 'system';
  content: string;
  file?: File;
  timestamp: Date;
  isGenerating?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  backendConversationId?: number; // ID de la conversation côté backend
}

interface ChatContextType {
  messages: Message[];
  isTyping: boolean;
  conversations: Conversation[];
  currentChatId: string | null;
  sendMessage: (content: string, file?: File | null) => Promise<void>;
  newChat: () => void;
  deleteChat: (chatId: string) => void;
  setCurrentChatId: (chatId: string) => void;
  clearChat: () => void;
  apiStatus: { status: 'ok' | 'error' | 'checking', message: string };
  useStreaming: boolean;
  toggleStreaming: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentChatId, setCurrentChatIdState] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [messageIdCounter, setMessageIdCounter] = useState(1);
  const [apiStatus, setApiStatus] = useState<{ status: 'ok' | 'error' | 'checking', message: string }>({ 
    status: 'checking', 
    message: 'Vérification de la connexion...' 
  });
  const [useStreaming, setUseStreaming] = useState(true);

  // Obtenir les messages de la conversation courante
  const currentConversation = conversations.find(conv => conv.id === currentChatId);
  const messages = currentConversation?.messages || [];

  const generateChatId = useCallback((): string => {
    return `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  const generateTitle = useCallback((firstMessage: string): string => {
    const cleanMessage = firstMessage.trim().replace(/\n/g, ' ');
    const words = cleanMessage.split(' ').slice(0, 6);
    return words.join(' ') + (cleanMessage.split(' ').length > 6 ? '...' : '');
  }, []);

  const updateConversation = useCallback((chatId: string, updates: Partial<Conversation>) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === chatId 
          ? { ...conv, ...updates, updatedAt: new Date() }
          : conv
      )
    );
  }, []);

  // Tester la connexion au backend au démarrage
  useEffect(() => {
    const testBackendConnection = async () => {
      console.log('🔍 Test de connexion au backend...');
      setApiStatus({ status: 'checking', message: 'Connexion au backend...' });
      
      try {
        const result = await chatApiService.testConnection();
        setApiStatus(result);
        console.log('✅ Status de connexion:', result);
      } catch (error) {
        console.error('❌ Erreur de connexion:', error);
        setApiStatus({ 
          status: 'error', 
          message: 'Impossible de se connecter au backend' 
        });
      }
    };

    testBackendConnection();
  }, []);

  const newChat = useCallback(() => {
    console.log('🆕 Création d\'une nouvelle conversation');
    
    // Reset la session backend
    chatApiService.resetSession();
    
    const chatId = generateChatId();
    const newConversation: Conversation = {
      id: chatId,
      title: 'Nouvelle conversation',
      lastMessage: '',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    setConversations(prev => [newConversation, ...prev]);
    setCurrentChatIdState(chatId);
    setMessageIdCounter(1);
  }, [generateChatId]);

  const deleteChat = useCallback((chatId: string) => {
    console.log('🗑️ Suppression de la conversation:', chatId);
    
    setConversations(prev => {
      const filteredConversations = prev.filter(conv => conv.id !== chatId);
      
      if (chatId === currentChatId) {
        const newCurrentChatId = filteredConversations.length > 0 ? filteredConversations[0].id : null;
        setCurrentChatIdState(newCurrentChatId);
        
        // Si on change de conversation, mettre à jour l'ID backend
        if (newCurrentChatId) {
          const newConv = filteredConversations.find(c => c.id === newCurrentChatId);
          if (newConv?.backendConversationId) {
            chatApiService.setCurrentConversationId(newConv.backendConversationId);
          } else {
            chatApiService.resetSession();
          }
        } else {
          chatApiService.resetSession();
        }
      }
      
      return filteredConversations;
    });
  }, [currentChatId]);

  const setCurrentChatId = useCallback((chatId: string) => {
    console.log('📂 Changement de conversation active:', chatId);
    setCurrentChatIdState(chatId);
    
    // Mettre à jour l'ID de conversation côté backend
    const conversation = conversations.find(conv => conv.id === chatId);
    if (conversation?.backendConversationId) {
      chatApiService.setCurrentConversationId(conversation.backendConversationId);
    } else {
      chatApiService.resetSession();
    }
  }, [conversations]);

  const clearChat = useCallback(() => {
    if (currentChatId) {
      console.log('🧹 Nettoyage de la conversation:', currentChatId);
      updateConversation(currentChatId, {
        messages: [],
        lastMessage: '',
        title: 'Nouvelle conversation'
      });
      setMessageIdCounter(1);
      
      // Reset la session backend pour cette conversation
      chatApiService.resetSession();
    }
    setIsTyping(false);
  }, [currentChatId, updateConversation]);

  const toggleStreaming = useCallback(() => {
    setUseStreaming(prev => !prev);
    console.log('🔄 Mode streaming:', !useStreaming ? 'activé' : 'désactivé');
  }, [useStreaming]);

  const sendMessage = useCallback(async (content: string, file?: File | null) => {
    if (!content.trim() && !file) {
      console.warn('⚠️ Message vide ignoré');
      return;
    }

    // Vérifier que le backend est disponible
    if (apiStatus.status === 'error') {
      console.error('❌ Backend non disponible, impossible d\'envoyer le message');
      return;
    }

    console.log('📤 Envoi du message au backend:', content.substring(0, 50) + '...');

    let targetChatId = currentChatId;

    // Si aucune conversation n'est sélectionnée, créer une nouvelle
    if (!targetChatId) {
      targetChatId = generateChatId();
      const newConversation: Conversation = {
        id: targetChatId,
        title: generateTitle(content),
        lastMessage: content.substring(0, 50),
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      
      setConversations(prev => [newConversation, ...prev]);
      setCurrentChatIdState(targetChatId);
      console.log('🆕 Nouvelle conversation créée pour le message:', targetChatId);
    }

    // Créer le message utilisateur
    const userMessage: Message = {
      id: messageIdCounter,
      type: 'user',
      content: content,
      file: file || undefined,
      timestamp: new Date(),
    };

    // Ajouter le message utilisateur à la conversation
    const currentConv = conversations.find(conv => conv.id === targetChatId);
    const updatedMessages = [...(currentConv?.messages || []), userMessage];
    
    updateConversation(targetChatId, {
      messages: updatedMessages,
      lastMessage: content.substring(0, 50) + (content.length > 50 ? '...' : ''),
      title: currentConv?.title === 'Nouvelle conversation' ? generateTitle(content) : currentConv?.title || generateTitle(content)
    });

    // Créer un message temporaire du bot avec indicateur de génération
    const botMessageId = messageIdCounter + 1;
    const tempBotMessage: Message = {
      id: botMessageId,
      type: 'bot',
      content: '',
      timestamp: new Date(),
      isGenerating: true
    };

    // Ajouter le message temporaire pour montrer l'indicateur de frappe
    const messagesWithTemp = [...updatedMessages, tempBotMessage];
    updateConversation(targetChatId, {
      messages: messagesWithTemp
    });

    setMessageIdCounter(prev => prev + 2);
    setIsTyping(true);

    try {
      let finalBotMessage: Message;

      if (useStreaming) {
        console.log('🌊 Utilisation du mode streaming...');
        
        // Variables pour le streaming
        let streamingContent = '';
        
        const handleChunk = (chunk: string) => {
          streamingContent += chunk;
          
          // Mettre à jour le message en temps réel
          const updatedBotMessage: Message = {
            id: botMessageId,
            type: 'bot',
            content: streamingContent,
            timestamp: new Date(),
            isGenerating: true
          };

          const updatedMessagesWithStream = [...updatedMessages, updatedBotMessage];
          updateConversation(targetChatId, {
            messages: updatedMessagesWithStream
          });
        };

        // Appel API avec streaming
        finalBotMessage = await chatApiService.sendMessageStream(content, handleChunk, file);
        
      } else {
        console.log('📦 Utilisation du mode standard...');
        
        // Appel API standard
        finalBotMessage = await chatApiService.sendMessage(content, file);
      }

      console.log('✅ Réponse reçue du backend:', finalBotMessage.content.substring(0, 50) + '...');

      // Mettre à jour avec la réponse finale
      const finalMessages = [...updatedMessages, {
        ...finalBotMessage,
        isGenerating: false
      }];

      // Sauvegarder l'ID de conversation backend
      const backendConversationId = chatApiService.getCurrentConversationId();
      
      updateConversation(targetChatId, {
        messages: finalMessages,
        lastMessage: finalBotMessage.content.substring(0, 50) + (finalBotMessage.content.length > 50 ? '...' : ''),
        backendConversationId: backendConversationId || undefined
      });

    } catch (error) {
      console.error('❌ Erreur lors de l\'envoi du message:', error);
      
      const errorMessage: Message = {
        id: botMessageId,
        type: 'bot',
        content: `❌ Erreur: ${error instanceof Error ? error.message : 'Erreur inconnue'}\n\nVérifiez que le backend est démarré sur http://localhost:8000`,
        timestamp: new Date(),
        isGenerating: false
      };

      const finalMessages = [...updatedMessages, errorMessage];
      updateConversation(targetChatId, {
        messages: finalMessages,
        lastMessage: 'Erreur de connexion'
      });

      // Mettre à jour le status API en cas d'erreur
      setApiStatus({ 
        status: 'error', 
        message: error instanceof Error ? error.message : 'Erreur de connexion au backend' 
      });

    } finally {
      setIsTyping(false);
    }
  }, [
    conversations, 
    currentChatId, 
    messageIdCounter, 
    updateConversation,
    generateChatId,
    generateTitle,
    apiStatus.status,
    useStreaming
  ]);

  // Créer une première conversation si aucune n'existe
  useEffect(() => {
    if (conversations.length === 0) {
      console.log('🚀 Création de la première conversation');
      newChat();
    }
  }, [conversations.length, newChat]);

  const contextValue: ChatContextType = {
    messages,
    isTyping,
    conversations,
    currentChatId,
    sendMessage,
    newChat,
    deleteChat,
    setCurrentChatId,
    clearChat,
    apiStatus,
    useStreaming,
    toggleStreaming,
  };

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

export default ChatProvider;