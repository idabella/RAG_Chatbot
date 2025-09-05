import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  PaperAirplaneIcon, 
  PaperClipIcon, 
  MicrophoneIcon,
  PhotoIcon,
  DocumentIcon,
  XMarkIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface InputBoxProps {
  onSendMessage: (message: string, file?: File | null) => Promise<void>;
  apiBaseUrl?: string;
}

interface UploadStatus {
  status: 'idle' | 'uploading' | 'success' | 'error';
  progress: number;
  message: string;
  documentId?: number;
}

const InputBox: React.FC<InputBoxProps> = ({ 
  onSendMessage, 
  apiBaseUrl = 'http://localhost:8000/api/v1' 
}) => {
  const [message, setMessage] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    status: 'idle',
    progress: 0,
    message: ''
  });
  const [isRecording, setIsRecording] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [shouldAutoUpload, setShouldAutoUpload] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Formats acceptés par le backend
  const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.docx', '.md'];
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  // Auto-upload quand un fichier est sélectionné
  useEffect(() => {
    if (file && shouldAutoUpload && uploadStatus.status === 'idle') {
      handleFileUpload();
      setShouldAutoUpload(false);
    }
  }, [file, shouldAutoUpload, uploadStatus.status]);

  const validateFile = (file: File): { valid: boolean; error?: string } => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return {
        valid: false,
        error: `Format non supporté. Formats acceptés: ${ALLOWED_EXTENSIONS.join(', ')}`
      };
    }
    
    if (file.size > MAX_FILE_SIZE) {
      return {
        valid: false,
        error: `Fichier trop volumineux (max: ${MAX_FILE_SIZE / (1024 * 1024)}MB)`
      };
    }
    
    return { valid: true };
  };

  const uploadDocument = async (file: File): Promise<{ success: boolean; documentId?: number; error?: string }> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', 'general');
      formData.append('auto_process', 'true');
      
      const title = file.name.replace(/\.[^/.]+$/, '');
      formData.append('title', title);

      const response = await fetch(`${apiBaseUrl}/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      return { success: true, documentId: result.id };
    } catch (error) {
      console.error('Erreur upload:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Erreur inconnue' 
      };
    }
  };

  const resetForm = () => {
    setMessage('');
    setFile(null);
    setUploadStatus({ status: 'idle', progress: 0, message: '' });
    setShouldAutoUpload(false);
    setIsSending(false);
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Si il y a un fichier qui n'a pas encore été uploadé
    if (file && uploadStatus.status === 'idle') {
      await handleFileUpload();
      return;
    }
    
    // Si on a un message ou un fichier uploadé avec succès
    if (message.trim() || (file && uploadStatus.status === 'success')) {
      // Sauvegarder les valeurs avant de vider le formulaire
      const messageToSend = message.trim();
      const fileToSend = file;
      
      // Vider immédiatement le champ de texte et désactiver le bouton
      setMessage('');
      setIsSending(true);
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
      
      try {
        // Envoyer le message
        await onSendMessage(messageToSend, fileToSend);
        
        // Reset complet après succès
        resetForm();
      } catch (error) {
        console.error('Erreur lors de l\'envoi du message:', error);
        
        // En cas d'erreur, restaurer le message et réactiver le bouton
        setMessage(messageToSend);
        setIsSending(false);
        
        // Restaurer la hauteur du textarea si nécessaire
        if (textareaRef.current && messageToSend) {
          setTimeout(() => {
            if (textareaRef.current) {
              textareaRef.current.style.height = 'auto';
              textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
            }
          }, 0);
        }
      }
    }
  };

  const handleFileUpload = async () => {
    if (!file) return;

    const validation = validateFile(file);
    if (!validation.valid) {
      setUploadStatus({
        status: 'error',
        progress: 0,
        message: validation.error || 'Fichier invalide'
      });
      return;
    }

    setUploadStatus({
      status: 'uploading',
      progress: 0,
      message: 'Upload en cours...'
    });

    // Simuler le progrès d'upload
    const progressInterval = setInterval(() => {
      setUploadStatus(prev => ({
        ...prev,
        progress: Math.min(prev.progress + 10, 90)
      }));
    }, 200);

    try {
      const result = await uploadDocument(file);
      clearInterval(progressInterval);
      
      if (result.success) {
        setUploadStatus({
          status: 'success',
          progress: 100,
          message: 'Document uploadé avec succès!',
          documentId: result.documentId
        });
      } else {
        setUploadStatus({
          status: 'error',
          progress: 0,
          message: result.error || 'Erreur lors de l\'upload'
        });
      }
    } catch (error) {
      clearInterval(progressInterval);
      setUploadStatus({
        status: 'error',
        progress: 0,
        message: 'Erreur de connexion au serveur'
      });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const validation = validateFile(selectedFile);
      if (validation.valid) {
        setFile(selectedFile);
        setUploadStatus({ status: 'idle', progress: 0, message: '' });
        setShouldAutoUpload(true); // Auto-upload dès sélection
      } else {
        setUploadStatus({
          status: 'error',
          progress: 0,
          message: validation.error || 'Fichier invalide'
        });
        setFile(null);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const validation = validateFile(droppedFile);
      if (validation.valid) {
        setFile(droppedFile);
        setUploadStatus({ status: 'idle', progress: 0, message: '' });
        setShouldAutoUpload(true); // Auto-upload dès drop
      } else {
        setUploadStatus({
          status: 'error',
          progress: 0,
          message: validation.error || 'Fichier invalide'
        });
      }
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setUploadStatus({ status: 'idle', progress: 0, message: '' });
    setShouldAutoUpload(false);
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return PhotoIcon;
    if (file.type.includes('pdf') || file.type.includes('document')) return DocumentIcon;
    return DocumentIcon;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = () => {
    switch (uploadStatus.status) {
      case 'uploading':
        return <ArrowPathIcon className="w-5 h-5 animate-spin" />;
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'error':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (uploadStatus.status) {
      case 'uploading':
        return 'border-blue-500/30 bg-blue-500/10';
      case 'success':
        return 'border-green-500/30 bg-green-500/10';
      case 'error':
        return 'border-red-500/30 bg-red-500/10';
      default:
        return 'border-blue-500/30 bg-blue-500/10';
    }
  };

  const canSendMessage = () => {
    return (message.trim() || (file && uploadStatus.status === 'success')) && 
           uploadStatus.status !== 'uploading' && 
           !isSending;
  };

  const getSubmitButtonText = () => {
    if (isSending) {
      return 'Envoi...';
    }
    if (uploadStatus.status === 'uploading') {
      return 'Upload...';
    }
    if (file && uploadStatus.status === 'success' && !message.trim()) {
      return 'Envoyer fichier';
    }
    return 'Envoyer';
  };

  return (
    <div className="relative">
      <style jsx>{`
        .gradient-border {
          position: relative;
          border-radius: 1rem;
          padding: 1px;
          background: linear-gradient(135deg, 
            #667eea 0%, 
            #764ba2 25%, 
            #f093fb 50%, 
            #f5576c 75%, 
            #4facfe 100%);
          background-size: 200% 200%;
          animation: gradientShift 3s ease-in-out infinite;
        }
        
        .gradient-border::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          border-radius: 1rem;
          padding: 1px;
          background: linear-gradient(135deg, 
            rgba(102, 126, 234, 0.8) 0%, 
            rgba(118, 75, 162, 0.8) 25%, 
            rgba(240, 147, 251, 0.8) 50%, 
            rgba(245, 87, 108, 0.8) 75%, 
            rgba(79, 172, 254, 0.8) 100%);
          background-size: 200% 200%;
          animation: gradientShift 3s ease-in-out infinite reverse;
          opacity: 0;
          transition: opacity 0.3s ease;
          pointer-events: none;
        }
        
        .gradient-border.focused::before {
          opacity: 1;
        }
        
        .gradient-border.focused::after {
          content: '';
          position: absolute;
          top: -4px;
          left: -4px;
          right: -4px;
          bottom: -4px;
          border-radius: 1.25rem;
          background: linear-gradient(135deg, 
            rgba(102, 126, 234, 0.3) 0%, 
            rgba(118, 75, 162, 0.3) 25%, 
            rgba(240, 147, 251, 0.3) 50%, 
            rgba(245, 87, 108, 0.3) 75%, 
            rgba(79, 172, 254, 0.3) 100%);
          background-size: 200% 200%;
          animation: gradientShift 3s ease-in-out infinite;
          filter: blur(8px);
          z-index: -1;
          pointer-events: none;
        }
        
        @keyframes gradientShift {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }
      `}</style>

      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        onSubmit={handleSubmit}
        className="relative max-w-4xl px-4 py-3 mx-auto"
      >
        {/* Drag and Drop Overlay */}
        <AnimatePresence>
          {isDragOver && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-10 flex items-center justify-center border-2 border-blue-500 border-dashed bg-blue-500/10 rounded-2xl"
            >
              <div className="text-center">
                <CloudArrowUpIcon className="w-12 h-12 mx-auto mb-2 text-blue-500" />
                <p className="font-medium text-blue-700">
                  Déposez votre fichier ici
                </p>
                <p className="text-sm text-blue-600">
                  Formats: {ALLOWED_EXTENSIONS.join(', ')}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Gradient Border Container */}
        <div className={`gradient-border ${isFocused ? 'focused' : ''}`}>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className="relative z-10 flex items-end p-2 space-x-3 transition-all duration-200 bg-gray-800 shadow-lg rounded-2xl"
          >
            {/* File Upload Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadStatus.status === 'uploading'}
              className="flex-shrink-0 p-3 m-2 text-gray-300 transition-colors duration-200 hover:text-blue-500 hover:bg-gray-700 rounded-xl disabled:opacity-50"
              title="Joindre un fichier"
            >
              <PaperClipIcon className="w-6 h-6" />
            </motion.button>

            {/* Text Input */}
            <div className="flex-1 py-3">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={handleTextareaChange}
                onKeyPress={handleKeyPress}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder="Tapez votre message ici... (Entrée pour envoyer, Maj+Entrée pour nouvelle ligne)"
                className="w-full py-1 text-white placeholder-gray-500 bg-transparent border-none resize-none max-h-56 focus:outline-none"
                rows={2}
                disabled={uploadStatus.status === 'uploading' || isSending}
              />
            </div>

            {/* Voice Recording Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => setIsRecording(!isRecording)}
              disabled={uploadStatus.status === 'uploading'}
              className={`flex-shrink-0 p-3 transition-all duration-200 rounded-xl m-2 disabled:opacity-50 ${
                isRecording 
                  ? 'text-red-400 bg-red-900/20 animate-pulse' 
                  : 'text-gray-400 hover:text-blue-500 hover:bg-gray-700'
              }`}
              title={isRecording ? "Arrêter l'enregistrement" : "Enregistrer un message vocal"}
            >
              <MicrophoneIcon className="w-6 h-6" />
            </motion.button>

            {/* Send Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={!canSendMessage()}
              className={`flex-shrink-0 p-3 rounded-xl m-2 transition-all duration-200 ${
                canSendMessage()
                  ? 'text-white bg-gradient-to-r from-blue-500 to-blue-900 hover:from-blue-600 hover:to-purple-700 shadow-lg'
                  : 'text-white bg-gradient-to-r from-blue-500 to-purple-600 opacity-50 cursor-not-allowed'
              }`}
              title={getSubmitButtonText()}
            >
              {uploadStatus.status === 'uploading' || isSending ? (
                <ArrowPathIcon className="w-6 h-6 animate-spin" />
              ) : (
                <PaperAirplaneIcon className="w-6 h-6" />
              )}
            </motion.button>
          </div>
        </div>

        {/* File Display */}
        <AnimatePresence>
          {file && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -10 }}
              transition={{ duration: 0.3 }}
              className={`flex items-center justify-between p-4 mt-3 border rounded-xl ${getStatusColor()}`}
            >
              <div className="flex items-center space-x-3">
                {React.createElement(getFileIcon(file), { 
                  className: "h-8 w-8 text-blue-400 flex-shrink-0" 
                })}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-blue-300 truncate">{file.name}</p>
                  <p className="text-xs text-blue-400">{formatFileSize(file.size)}</p>
                  {uploadStatus.status === 'uploading' && (
                    <div className="w-full h-2 mt-1 bg-gray-700 rounded-full">
                      <div 
                        className="h-2 transition-all duration-300 bg-blue-500 rounded-full"
                        style={{ width: `${uploadStatus.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                {getStatusIcon()}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  type="button"
                  onClick={handleRemoveFile}
                  disabled={uploadStatus.status === 'uploading' || isSending}
                  className="p-1 text-blue-400 transition-colors duration-200 hover:text-red-400 disabled:opacity-50"
                  title="Supprimer le fichier"
                >
                  <XMarkIcon className="w-5 h-5" />
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Upload Status */}
        <AnimatePresence>
          {uploadStatus.message && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`flex items-center p-3 mt-3 space-x-3 border rounded-xl ${getStatusColor()}`}
            >
              {getStatusIcon()}
              <span className={`text-sm ${
                uploadStatus.status === 'success' ? 'text-green-400' : 
                uploadStatus.status === 'error' ? 'text-red-400' : 'text-blue-400'
              }`}>
                {uploadStatus.message}
              </span>
              {uploadStatus.status === 'success' && uploadStatus.documentId && (
                <span className="text-xs text-gray-400">
                  ID: {uploadStatus.documentId}
                </span>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Recording Indicator */}
        <AnimatePresence>
          {isRecording && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center p-4 mt-3 space-x-3 border border-red-500/30 bg-red-500/10 rounded-xl"
            >
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="font-medium text-red-400">Enregistrement en cours...</span>
              <div className="flex-1"></div>
              <button
                type="button"
                onClick={() => setIsRecording(false)}
                className="text-red-400 transition-colors duration-200 hover:text-red-300"
              >
                Arrêter
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept={ALLOWED_EXTENSIONS.join(',')}
          className="hidden"
        />

        {/* Help Text */}
        <div className="mt-2 text-xs text-gray-500">
          Formats supportés: {ALLOWED_EXTENSIONS.join(', ')} • Taille max: {MAX_FILE_SIZE / (1024 * 1024)}MB
        </div>
      </motion.form>
    </div>
  );
};

export default InputBox;