// src/services/huggingFaceService.ts
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
}

interface ModelConfig {
  name: string;
  maxTokens: number;
  temperature: number;
  topP: number;
}

class HuggingFaceService {
  private baseURL = 'https://api-inference.huggingface.co/models';
  private apiKey: string;
  private models: ModelConfig[] = [
    {
      name: 'microsoft/DialoGPT-large',
      maxTokens: 150,
      temperature: 0.7,
      topP: 0.9
    },
    {
      name: 'microsoft/DialoGPT-medium',
      maxTokens: 120,
      temperature: 0.8,
      topP: 0.9
    },
    {
      name: 'gpt2',
      maxTokens: 100,
      temperature: 0.8,
      topP: 0.9
    },
    {
      name: 'google/flan-t5-base',
      maxTokens: 100,
      temperature: 0.7,
      topP: 0.95
    }
  ];
  
  private currentModelIndex = 0;
  private retryConfig: RetryConfig = {
    maxRetries: 3,
    baseDelay: 2000,
    maxDelay: 10000
  };

  constructor() {
    this.apiKey = this.getApiKey();
    
    console.log('🔍 Initialisation Hugging Face Service:');
    console.log('API Key:', this.apiKey ? '✅ TROUVÉE' : '❌ MANQUANTE');
    console.log('Modèles disponibles:', this.models.length);
  }

  private getApiKey(): string {
    try {
      // Essayer différentes sources pour la clé API
      const sources = [
        // Vite
        () => typeof import.meta !== 'undefined' && import.meta.env?.VITE_HUGGINGFACE_API_KEY,
        // Process env
        () => typeof process !== 'undefined' && process.env?.VITE_HUGGINGFACE_API_KEY,
        // Window global
        () => typeof window !== 'undefined' && (window as any).VITE_HUGGINGFACE_API_KEY,
        // Hardcoded fallback (à éviter en production)
        () => ''
      ];

      for (const getKey of sources) {
        const key = getKey();
        if (key) {
          console.log('✅ Clé API trouvée');
          return key;
        }
      }

      console.warn('⚠️ Clé API Hugging Face non trouvée');
      return '';
    } catch (error) {
      console.error('❌ Erreur lors de la récupération de la clé API:', error);
      return '';
    }
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private calculateBackoffDelay(attempt: number): number {
    const delay = this.retryConfig.baseDelay * Math.pow(2, attempt);
    const jitter = Math.random() * 1000; // Ajouter du jitter
    return Math.min(delay + jitter, this.retryConfig.maxDelay);
  }

  private buildConversationalPrompt(message: string, conversationHistory: ChatMessage[] = []): string {
    // Contexte système amélioré
    let prompt = `Tu es un assistant IA intelligent et serviable. Tu réponds de manière concise, précise et utile en français. 
Tu es amical mais professionnel. Si tu ne connais pas quelque chose, tu l'admets honnêtement.

`;
    
    // Ajouter l'historique récent (limité à 4 échanges pour éviter les tokens excessifs)
    const recentHistory = conversationHistory.slice(-8); // 4 échanges = 8 messages
    
    for (const msg of recentHistory) {
      if (msg.role === 'user') {
        prompt += `Utilisateur: ${msg.content}\n`;
      } else if (msg.role === 'assistant') {
        prompt += `Assistant: ${msg.content}\n`;
      }
    }
    
    // Ajouter le message actuel
    prompt += `Utilisateur: ${message}\nAssistant:`;
    
    return prompt;
  }

  private async makeRequest(modelConfig: ModelConfig, prompt: string, attempt: number = 0): Promise<any> {
    if (!this.apiKey) {
      throw new Error('API_KEY_MISSING');
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000); // Timeout augmenté

    try {
      console.log(`🚀 Tentative avec ${modelConfig.name} (essai ${attempt + 1})`);

      const requestBody = {
        inputs: prompt,
        parameters: {
          max_new_tokens: modelConfig.maxTokens,
          temperature: modelConfig.temperature,
          top_p: modelConfig.topP,
          repetition_penalty: 1.1,
          return_full_text: false,
          do_sample: true,
          ...(modelConfig.name.includes('gpt') && { pad_token_id: 50256 }),
          ...(modelConfig.name.includes('flan-t5') && { 
            max_length: modelConfig.maxTokens + prompt.length 
          })
        },
        options: {
          wait_for_model: true,
          use_cache: false
        }
      };

      const response = await fetch(`${this.baseURL}/${modelConfig.name}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'User-Agent': 'FileChat/1.0'
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      // Succès
      if (response.ok) {
        const data = await response.json();
        console.log(`✅ Réponse reçue de ${modelConfig.name}`);
        return { data, modelUsed: modelConfig.name };
      }

      // Gestion des erreurs spécifiques
      const errorText = await response.text().catch(() => 'Erreur inconnue');
      
      if (response.status === 503) {
        console.log(`⏱️ Modèle ${modelConfig.name} en chargement...`);
        if (attempt < this.retryConfig.maxRetries) {
          const delay = this.calculateBackoffDelay(attempt);
          console.log(`🔄 Retry dans ${delay}ms`);
          await this.sleep(delay);
          return this.makeRequest(modelConfig, prompt, attempt + 1);
        }
      }

      if (response.status === 429) {
        console.log(`⏱️ Rate limit atteint pour ${modelConfig.name}`);
        if (attempt < this.retryConfig.maxRetries) {
          const delay = this.calculateBackoffDelay(attempt);
          await this.sleep(delay);
          return this.makeRequest(modelConfig, prompt, attempt + 1);
        }
      }

      throw new Error(`HTTP_${response.status}: ${errorText}`);

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('TIMEOUT: La requête a pris trop de temps');
      }

      // Retry pour les erreurs réseau
      if (attempt < this.retryConfig.maxRetries && (
        error instanceof TypeError || 
        (error instanceof Error && error.message.includes('fetch'))
      )) {
        const delay = this.calculateBackoffDelay(attempt);
        console.log(`🌐 Retry réseau dans ${delay}ms`);
        await this.sleep(delay);
        return this.makeRequest(modelConfig, prompt, attempt + 1);
      }

      throw error;
    }
  }

  private async tryModelsSequentially(prompt: string): Promise<any> {
    let lastError: Error | null = null;

    // Essayer tous les modèles dans l'ordre
    for (let i = 0; i < this.models.length; i++) {
      const modelIndex = (this.currentModelIndex + i) % this.models.length;
      const model = this.models[modelIndex];

      try {
        const result = await this.makeRequest(model, prompt);
        // Si succès, utiliser ce modèle comme priorité pour la prochaine fois
        this.currentModelIndex = modelIndex;
        return result;
      } catch (error) {
        console.warn(`❌ Échec avec ${model.name}:`, error);
        lastError = error as Error;
        
        // Si ce n'est pas une erreur de disponibilité, passer au modèle suivant
        if (error instanceof Error && !error.message.includes('503')) {
          continue;
        }
        
        // Pour les erreurs 503, attendre un peu avant le prochain modèle
        if (i < this.models.length - 1) {
          await this.sleep(1000);
        }
      }
    }

    // Si tous les modèles ont échoué
    throw lastError || new Error('Tous les modèles sont indisponibles');
  }

  private extractResponse(generatedText: string, inputPrompt: string, modelUsed: string): string {
    try {
      let response = generatedText;
      
      // Traitement spécifique selon le modèle
      if (modelUsed.includes('flan-t5')) {
        // Flan-T5 retourne souvent des réponses plus directes
        response = response.trim();
      } else {
        // Pour DialoGPT et GPT-2
        if (response.includes(inputPrompt)) {
          response = response.replace(inputPrompt, '').trim();
        }
        
        // Nettoyer les marqueurs de conversation
        response = response
          .split('\nUtilisateur:')[0]
          .split('\nUser:')[0]
          .split('\nHuman:')[0]
          .split('Utilisateur:')[0]
          .trim();
      }
      
      // Supprimer les préfixes indésirables
      response = response.replace(/^(Assistant:|Bot:|AI:)\s*/i, '');
      
      // Gérer la longueur de la réponse
      if (response.length > 300) {
        response = response.substring(0, 300);
        const lastSentence = Math.max(
          response.lastIndexOf('.'),
          response.lastIndexOf('!'),
          response.lastIndexOf('?')
        );
        
        if (lastSentence > response.length * 0.6) {
          response = response.substring(0, lastSentence + 1);
        } else {
          response += '...';
        }
      }
      
      // Nettoyer et valider
      response = response.trim();
      
      // Vérifier la qualité de la réponse
      if (!response || response.length < 3) {
        return 'Je suis désolé, je n\'ai pas pu générer une réponse appropriée. Pouvez-vous reformuler votre question ?';
      }
      
      // Vérifier si la réponse n'est pas juste une répétition
      const words = response.split(' ');
      if (words.length < 3) {
        return 'Pouvez-vous être plus spécifique dans votre question ? Je peux vous aider avec plus de détails.';
      }
      
      return response;
      
    } catch (error) {
      console.error('❌ Erreur lors de l\'extraction:', error);
      return 'Erreur lors du traitement de la réponse. Veuillez réessayer.';
    }
  }

  async generateResponse(message: string, conversationHistory: ChatMessage[] = []): Promise<string> {
    if (!this.apiKey) {
      return '❌ Configuration manquante : Clé API Hugging Face requise. Vérifiez vos paramètres.';
    }

    if (!message.trim()) {
      return 'Pouvez-vous poser une question ? Je suis là pour vous aider ! 😊';
    }

    try {
      console.log('🤖 Génération de réponse...');
      
      const prompt = this.buildConversationalPrompt(message, conversationHistory);
      console.log('📝 Prompt généré:', prompt.substring(0, 200) + '...');
      
      const result = await this.tryModelsSequentially(prompt);
      const { data, modelUsed } = result;
      
      console.log('✅ Données reçues:', JSON.stringify(data).substring(0, 200));
      
      // Extraire le texte généré
      let generatedText = '';
      
      if (Array.isArray(data) && data.length > 0) {
        generatedText = data[0].generated_text || '';
      } else if (data && typeof data === 'object' && data.generated_text) {
        generatedText = data.generated_text;
      } else if (typeof data === 'string') {
        generatedText = data;
      }
      
      if (!generatedText) {
        console.error('❌ Pas de texte généré:', data);
        return 'Je n\'ai pas pu générer une réponse. Réessayez dans quelques instants.';
      }
      
      const finalResponse = this.extractResponse(generatedText, prompt, modelUsed);
      console.log(`🎯 Réponse finale (${modelUsed}):`, finalResponse);
      
      return finalResponse;
      
    } catch (error) {
      console.error('❌ Erreur génération:', error);
      
      // Messages d'erreur user-friendly
      if (error instanceof Error) {
        if (error.message.includes('API_KEY_MISSING')) {
          return '🔐 Clé API manquante. Configurez votre clé Hugging Face dans les paramètres.';
        } else if (error.message.includes('401')) {
          return '🔐 Clé API invalide. Vérifiez votre clé Hugging Face dans les paramètres.';
        } else if (error.message.includes('429')) {
          return '⏱️ Trop de requêtes. Attendez quelques minutes avant de réessayer.';
        } else if (error.message.includes('503')) {
          return '🔄 Tous les modèles IA sont en cours de chargement. Attendez 1-2 minutes et réessayez.';
        } else if (error.message.includes('TIMEOUT')) {
          return '⏱️ Délai d\'attente dépassé. Le service est peut-être surchargé, réessayez.';
        } else if (error.message.includes('fetch') || error instanceof TypeError) {
          return '🌐 Problème de connexion. Vérifiez votre connexion internet et réessayez.';
        }
      }
      
      return '❌ Une erreur inattendue s\'est produite. Réessayez dans quelques instants.';
    }
  }

  async checkApiStatus(): Promise<{ status: 'ok' | 'error' | 'checking', message: string }> {
    if (!this.apiKey) {
      return { status: 'error', message: 'Clé API manquante' };
    }

    try {
      console.log('🔍 Vérification du statut API...');
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      // Tester avec le modèle le plus stable
      const testModel = this.models[2]; // gpt2
      
      const response = await fetch(`${this.baseURL}/${testModel.name}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          inputs: 'Test',
          parameters: { max_new_tokens: 5, temperature: 0.7 },
          options: { wait_for_model: false }
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        return { status: 'ok', message: 'API fonctionnelle' };
      } else if (response.status === 503) {
        return { status: 'ok', message: 'API disponible (modèles en chargement)' };
      } else if (response.status === 401) {
        return { status: 'error', message: 'Clé API invalide' };
      } else if (response.status === 429) {
        return { status: 'ok', message: 'API fonctionnelle (limite de taux)' };
      } else {
        return { status: 'error', message: `Erreur API: ${response.status}` };
      }
      
    } catch (error) {
      console.error('❌ Erreur vérification API:', error);
      
      if (error instanceof Error && error.name === 'AbortError') {
        return { status: 'error', message: 'Délai d\'attente dépassé' };
      }
      return { status: 'error', message: 'Erreur de connexion' };
    }
  }

  // Méthode pour obtenir des informations sur les modèles disponibles
  getAvailableModels(): ModelConfig[] {
    return [...this.models];
  }

  // Méthode pour changer le modèle prioritaire
  setPreferredModel(modelName: string): boolean {
    const index = this.models.findIndex(m => m.name === modelName);
    if (index !== -1) {
      this.currentModelIndex = index;
      console.log(`✅ Modèle prioritaire changé vers: ${modelName}`);
      return true;
    }
    return false;
  }
}

// Export d'une instance singleton
export const huggingfaceService = new HuggingFaceService();
export default huggingfaceService;