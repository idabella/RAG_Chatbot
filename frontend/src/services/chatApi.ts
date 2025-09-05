// src/services/chatApi.ts
import { Message } from '../components/chat/ChatInterface';

// Types pour l'API
interface ChatRequest {
  message: string;
  conversation_id?: number;
  file?: File;
}

interface ChatResponse {
  message: string;
  conversation_id: number;
  message_id: number;
  sources?: any[];
  confidence?: number;
  timestamp: string;
  processing_time?: number;
  formatting?: {
    content_type: string;
    encoding: string;
    processed: boolean;
  };
}

interface ApiMessage {
  id: number;
  conversation_id: number;
  user_id: number;
  content: string;
  role: 'user' | 'assistant' | 'system';
  created_at: string;
  confidence_score?: number;
  sources?: any[];
  metadata?: any;
  token_count?: number;
  has_sources?: boolean;
  source_count?: number;
}

interface ChatHistoryResponse {
  conversation_id: number;
  messages: ApiMessage[];
  total_messages: number;
  has_more: boolean;
}

class ChatApiService {
  private baseURL: string;
  private currentConversationId: number | null = null;

  constructor(baseURL: string = 'http://localhost:8000/api/v1/chat') {
    this.baseURL = baseURL;
  }

  // Convertir un message API en message frontend
  private convertApiMessageToFrontend(apiMessage: ApiMessage): Message {
    return {
      id: apiMessage.id,
      type: apiMessage.role === 'user' ? 'user' : apiMessage.role === 'assistant' ? 'bot' : 'system',
      content: apiMessage.content,
      timestamp: new Date(apiMessage.created_at),
      isGenerating: false
    };
  }

  // Envoyer un message et recevoir une réponse
  async sendMessage(message: string, file?: File): Promise<Message> {
    try {
      const chatRequest: ChatRequest = {
        message,
        conversation_id: this.currentConversationId || undefined
      };

      const response = await fetch(`${this.baseURL}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(chatRequest)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ChatResponse = await response.json();
      
      // Mettre à jour l'ID de conversation
      if (data.conversation_id) {
        this.currentConversationId = data.conversation_id;
      }

      // Convertir la réponse en message frontend
      return {
        id: data.message_id,
        type: 'bot',
        content: data.message,
        timestamp: new Date(data.timestamp),
        isGenerating: false
      };

    } catch (error) {
      console.error('Error sending message:', error);
      throw new Error(`Erreur lors de l'envoi du message: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
    }
  }

  // Envoyer un message avec streaming
  async sendMessageStream(
    message: string, 
    onChunk: (chunk: string) => void,
    file?: File
  ): Promise<Message> {
    try {
      const chatRequest: ChatRequest = {
        message,
        conversation_id: this.currentConversationId || undefined
      };

      const response = await fetch(`${this.baseURL}/message/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/plain',
        },
        body: JSON.stringify(chatRequest)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response stream available');
      }

      let fullResponse = '';
      let messageId: number | null = null;

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;

          const chunk = new TextDecoder().decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonData = JSON.parse(line.substring(6));
                
                if (jsonData.error) {
                  throw new Error(jsonData.error);
                }
                
                if (jsonData.chunk) {
                  fullResponse += jsonData.chunk;
                  onChunk(jsonData.chunk);
                }
                
                if (jsonData.conversation_id) {
                  this.currentConversationId = jsonData.conversation_id;
                }
                
                if (jsonData.done) {
                  messageId = jsonData.message_id;
                  break;
                }
                
              } catch (parseError) {
                console.warn('Error parsing chunk:', parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      return {
        id: messageId || botMessageId,
        type: 'bot',
        content: fullResponse,
        timestamp: new Date(),
        isGenerating: false
      };

    } catch (error) {
      console.error('Error in streaming message:', error);
      throw new Error(`Erreur lors du streaming: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
    }
  }

  // Récupérer l'historique d'une conversation
  async getChatHistory(conversationId: number, limit: number = 50, offset: number = 0): Promise<Message[]> {
    try {
      const response = await fetch(`${this.baseURL}/history/${conversationId}?limit=${limit}&offset=${offset}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ChatHistoryResponse = await response.json();
      
      return data.messages.map(msg => this.convertApiMessageToFrontend(msg));

    } catch (error) {
      console.error('Error getting chat history:', error);
      throw new Error(`Erreur lors de la récupération de l'historique: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
    }
  }

  // Tester la connexion avec le backend
  async testConnection(): Promise<{ status: 'ok' | 'error', message: string }> {
    try {
      const response = await fetch(`${this.baseURL}/test`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        }
      });

      if (!response.ok) {
        return {
          status: 'error',
          message: `Erreur HTTP ${response.status}: ${response.statusText}`
        };
      }

      const data = await response.json();
      
      return {
        status: 'ok',
        message: data.message || 'Connexion au backend réussie'
      };

    } catch (error) {
      console.error('Backend connection test failed:', error);
      return {
        status: 'error',
        message: `Impossible de se connecter au backend: ${error instanceof Error ? error.message : 'Erreur inconnue'}`
      };
    }
  }

  // Getter pour l'ID de conversation courante
  getCurrentConversationId(): number | null {
    return this.currentConversationId;
  }

  // Setter pour l'ID de conversation courante
  setCurrentConversationId(id: number | null): void {
    this.currentConversationId = id;
  }

  // Reset de la session (nouvelle conversation)
  resetSession(): void {
    this.currentConversationId = null;
  }
}

// Instance globale du service
export const chatApiService = new ChatApiService();

// Hook pour utiliser le service API
export const useChatApi = () => {
  return chatApiService;
};

export default ChatApiService;