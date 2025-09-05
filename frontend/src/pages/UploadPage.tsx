// src/pages/UploadPage.tsx - Version complète avec Layout
import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Layout from '../components/common/Layout';
import {
  CloudArrowUpIcon,
  DocumentIcon,
  PhotoIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  FolderIcon,
  TagIcon,
  InformationCircleIcon,
  DocumentTextIcon,
  TrashIcon,
  EyeIcon,
  DocumentArrowUpIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

// Types
interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'processing' | 'success' | 'error';
  progress: number;
  documentId?: number;
  error?: string;
  preview?: string;
  content?: string;
  wordCount?: number;
  pages?: number;
}

interface DocumentStats {
  total_documents: number;
  pending_processing: number;
  completed_processing: number;
  failed_processing: number;
  total_size_mb: number;
}

interface UploadPageProps {
  apiBaseUrl?: string;
}

const UploadPage: React.FC<UploadPageProps> = ({ 
  apiBaseUrl = 'http://localhost:8000/api/v1' 
}) => {
  // États principaux
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [category, setCategory] = useState('general');
  const [tags, setTags] = useState('');
  const [autoProcess, setAutoProcess] = useState(true);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<UploadedFile | null>(null);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Configuration
  const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.docx', '.md', '.doc'];
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const CATEGORIES = ['general', 'documentation', 'research', 'legal', 'technical'];

  // Types de fichiers acceptés
  const acceptedTypes = {
    'application/pdf': { icon: DocumentIcon, label: 'PDF', color: 'text-red-500' },
    'text/plain': { icon: DocumentTextIcon, label: 'TXT', color: 'text-blue-500' },
    'application/msword': { icon: DocumentIcon, label: 'DOC', color: 'text-blue-600' },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': { 
      icon: DocumentIcon, label: 'DOCX', color: 'text-blue-600' 
    }
  };

  // Charger les statistiques
  const loadStats = useCallback(async () => {
    setIsLoadingStats(true);
    try {
      const response = await fetch(`${apiBaseUrl}/documents/stats/overview`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
    } finally {
      setIsLoadingStats(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // Validation de fichier
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

  // Extraire le contenu du document
  const extractTextContent = async (file: File): Promise<{content: string, wordCount: number, pages?: number}> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        try {
          let content = '';
          let pages = undefined;
          
          if (file.type === 'text/plain' || file.name.toLowerCase().endsWith('.txt')) {
            content = e.target?.result as string;
          } else if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
            content = `Contenu extrait du PDF: ${file.name}\n\nCeci est une simulation du contenu extrait du document PDF. Dans une implémentation réelle, vous utiliseriez une bibliothèque comme pdf-parse pour extraire le texte réel du PDF.`;
            pages = Math.floor(Math.random() * 50) + 1;
          } else {
            content = `Contenu extrait du document: ${file.name}\n\nCeci est une simulation du contenu extrait du document. Dans une implémentation réelle, vous utiliseriez une bibliothèque appropriée pour extraire le texte.`;
          }
          
          const wordCount = content.trim().split(/\s+/).length;
          resolve({ content, wordCount, pages });
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Erreur lors de la lecture du fichier'));
      
      if (file.type === 'text/plain' || file.name.toLowerCase().endsWith('.txt')) {
        reader.readAsText(file, 'UTF-8');
      } else {
        reader.readAsArrayBuffer(file);
      }
    });
  };

  // Générer un aperçu pour les images
  const generatePreview = (file: File): Promise<string | undefined> => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.onerror = () => resolve(undefined);
        reader.readAsDataURL(file);
      } else {
        resolve(undefined);
      }
    });
  };

  // Simulation du processing
  const simulateProcessing = (fileId: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 25;
        
        setFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { ...f, progress: Math.min(progress, 90) }
            : f
        ));

        if (progress >= 90) {
          clearInterval(interval);
          
          setFiles(prev => prev.map(f => 
            f.id === fileId 
              ? { ...f, status: 'processing', progress: 95 }
              : f
          ));

          setTimeout(() => {
            const isSuccess = Math.random() > 0.05;
            
            setFiles(prev => prev.map(f => 
              f.id === fileId 
                ? { 
                    ...f, 
                    status: isSuccess ? 'success' : 'error',
                    progress: 100,
                    error: isSuccess ? undefined : 'Erreur lors du traitement du document'
                  }
                : f
            ));

            if (isSuccess) {
              resolve();
            } else {
              reject(new Error('Processing failed'));
            }
          }, 1500);
        }
      }, 300);
    });
  };

  // Ajouter des fichiers
  const addFiles = async (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    
    for (const file of fileArray) {
      const validation = validateFile(file);
      const preview = await generatePreview(file);
      
      let uploadFile: UploadedFile = {
        file,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        status: validation.valid ? 'pending' : 'error',
        progress: 0,
        error: validation.error,
        preview
      };

      if (validation.valid) {
        try {
          const { content, wordCount, pages } = await extractTextContent(file);
          uploadFile = { ...uploadFile, content, wordCount, pages };
        } catch (error) {
          uploadFile.error = 'Erreur lors de l\'extraction du contenu';
          uploadFile.status = 'error';
        }
      }
      
      setFiles(prev => [...prev, uploadFile]);
      
      // Auto-upload si le fichier est valide
      if (validation.valid && !uploadFile.error) {
        uploadSingleFile(uploadFile);
      }
    }
  };

  // Upload d'un fichier unique
  const uploadSingleFile = async (uploadFile: UploadedFile) => {
    try {
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'uploading', progress: 0 }
          : f
      ));

      // Simuler l'upload avec API
      await simulateProcessing(uploadFile.id);
      
      // En cas de succès, recharger les stats
      loadStats();
    } catch (error) {
      console.error('Erreur upload:', error);
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id
          ? { 
              ...f, 
              status: 'error', 
              progress: 0, 
              error: error instanceof Error ? error.message : 'Erreur inconnue' 
            }
          : f
      ));
    }
  };

  // Supprimer un fichier
  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Gestion du drag & drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!dropZoneRef.current?.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      addFiles(droppedFiles);
    }
  }, []);

  // Gestion de la sélection de fichiers
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      addFiles(selectedFiles);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Icône selon le type de fichier
  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return PhotoIcon;
    const config = acceptedTypes[file.type as keyof typeof acceptedTypes];
    return config ? config.icon : DocumentIcon;
  };

  // Couleur selon le statut
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-400';
      case 'uploading': return 'text-blue-400';
      case 'processing': return 'text-purple-400';
      case 'success': return 'text-green-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  // Formatage de la taille
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <ArrowPathIcon className="w-5 h-5 text-purple-500 animate-spin" />;
      case 'uploading':
        return <ArrowPathIcon className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <CloudArrowUpIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const retryProcessing = async (fileId: string) => {
    const file = files.find(f => f.id === fileId);
    if (!file) return;

    setFiles(prev => prev.map(f => 
      f.id === fileId 
        ? { ...f, status: 'uploading', progress: 0, error: undefined }
        : f
    ));

    try {
      await simulateProcessing(fileId);
    } catch (error) {
      console.error('Retry processing error:', error);
    }
  };

  const clearAllDocuments = () => {
    setFiles([]);
  };

  const successfulDocuments = files.filter(file => file.status === 'success');

  return (
    <Layout>
      <div className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-900 via-gray-950 to-gray-900">
        <div className="p-6">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8 text-center"
            >
              <h1 className="mb-2 text-4xl font-bold text-white">
                Upload de Documents
              </h1>
              <p className="text-gray-400">
                Ajoutez vos documents PDF, TXT, DOC pour alimenter votre chatbot RAG
              </p>
              
              {successfulDocuments.length > 0 && (
                <div className="inline-flex items-center px-4 py-2 mt-4 text-sm font-medium text-green-100 bg-green-600 rounded-full">
                  <CheckCircleIcon className="w-4 h-4 mr-2" />
                  {successfulDocuments.length} document(s) prêt(s) pour le chat
                </div>
              )}
            </motion.div>

            {/* Statistiques */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-1 gap-4 mb-8 md:grid-cols-4"
            >
              {isLoadingStats ? (
                <div className="flex justify-center col-span-4">
                  <ArrowPathIcon className="w-6 h-6 text-blue-400 animate-spin" />
                </div>
              ) : stats ? (
                <>
                  <div className="p-4 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
                    <div className="text-2xl font-bold text-blue-400">
                      {stats.total_documents}
                    </div>
                    <div className="text-sm text-gray-400">Documents totaux</div>
                  </div>
                  <div className="p-4 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
                    <div className="text-2xl font-bold text-green-400">
                      {stats.completed_processing}
                    </div>
                    <div className="text-sm text-gray-400">Traités</div>
                  </div>
                  <div className="p-4 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
                    <div className="text-2xl font-bold text-yellow-400">
                      {stats.pending_processing}
                    </div>
                    <div className="text-sm text-gray-400">En attente</div>
                  </div>
                  <div className="p-4 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
                    <div className="text-2xl font-bold text-purple-400">
                      {(stats.total_size_mb || 0).toFixed(1)} MB
                    </div>
                    <div className="text-sm text-gray-400">Taille totale</div>
                  </div>
                </>
              ) : null}
            </motion.div>

            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
              {/* Configuration */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="lg:col-span-1"
              >
                <div className="p-6 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
                  <h3 className="flex items-center mb-4 text-lg font-semibold text-white">
                    <FolderIcon className="w-5 h-5 mr-2" />
                    Configuration
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-300">
                        Catégorie
                      </label>
                      <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        className="w-full px-3 py-2 text-white bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        {CATEGORIES.map(cat => (
                          <option key={cat} value={cat}>
                            {cat.charAt(0).toUpperCase() + cat.slice(1)}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-300">
                        <TagIcon className="inline w-4 h-4 mr-1" />
                        Tags (optionnel)
                      </label>
                      <input
                        type="text"
                        value={tags}
                        onChange={(e) => setTags(e.target.value)}
                        placeholder="tag1, tag2, tag3"
                        className="w-full px-3 py-2 text-white placeholder-gray-400 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        Séparez les tags par des virgules
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="autoProcess"
                        checked={autoProcess}
                        onChange={(e) => setAutoProcess(e.target.checked)}
                        className="text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                      />
                      <label htmlFor="autoProcess" className="text-sm text-gray-300">
                        Traitement automatique
                      </label>
                    </div>

                    <div className="p-3 border rounded-lg bg-blue-900/20 border-blue-700/30">
                      <div className="flex items-start space-x-2">
                        <InformationCircleIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                        <div className="text-xs text-blue-300">
                          <p className="mb-1 font-medium">Formats supportés:</p>
                          <p>{ALLOWED_EXTENSIONS.join(', ')}</p>
                          <p className="mt-1">Taille max: {MAX_FILE_SIZE / (1024 * 1024)}MB</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Types de fichiers supportés */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="mt-6 space-y-3"
                >
                  <h4 className="text-sm font-medium text-gray-300">Types supportés</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(acceptedTypes).map(([type, config]) => (
                      <div
                        key={type}
                        className="flex items-center p-3 space-x-2 rounded-lg bg-gray-800/50"
                      >
                        <config.icon className={`w-5 h-5 ${config.color}`} />
                        <div>
                          <p className="text-xs font-medium text-white">{config.label}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              </motion.div>

              {/* Zone d'upload et liste des fichiers */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6 lg:col-span-2"
              >
                {/* Zone de drop */}
                <div
                  ref={dropZoneRef}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`relative border-2 border-dashed rounded-xl p-8 transition-all duration-300 ${
                    isDragOver
                      ? 'border-blue-500 bg-blue-500/10 scale-105'
                      : 'border-gray-600 bg-gray-800/30 hover:border-gray-500 hover:bg-gray-800/50'
                  }`}
                >
                  <motion.div
                    animate={{ y: isDragOver ? -10 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-center"
                  >
                    <DocumentArrowUpIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <h3 className="mb-2 text-lg font-medium text-white">
                      {isDragOver ? 'Relâchez pour uploader' : 'Glissez vos documents ici'}
                    </h3>
                    <p className="mb-4 text-gray-400">
                      ou cliquez pour sélectionner
                    </p>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => fileInputRef.current?.click()}
                      className="inline-flex items-center px-6 py-3 font-medium text-white transition-all duration-200 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                    >
                      <DocumentIcon className="w-5 h-5 mr-2" />
                      Choisir des fichiers
                    </motion.button>
                  </motion.div>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept={ALLOWED_EXTENSIONS.join(',')}
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>

                {/* Liste des fichiers */}
                <AnimatePresence>
                  {files.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="p-4 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-white">
                          Documents ({files.length})
                        </h3>
                        <button
                          onClick={clearAllDocuments}
                          className="flex items-center space-x-1 text-sm text-red-400 hover:text-red-300"
                        >
                          <TrashIcon className="w-4 h-4" />
                          <span>Tout supprimer</span>
                        </button>
                      </div>
                      
                      <div className="space-y-3 overflow-y-auto max-h-96">
                        {files.map((uploadFile) => (
                          <motion.div
                            key={uploadFile.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="flex items-center p-3 space-x-4 rounded-lg bg-gray-700/30"
                          >
                            {/* Aperçu ou icône */}
                            <div className="flex-shrink-0">
                              {uploadFile.preview ? (
                                <img
                                  src={uploadFile.preview}
                                  alt="Preview"
                                  className="object-cover w-10 h-10 rounded"
                                />
                              ) : (
                                <div className="flex items-center justify-center w-10 h-10 bg-gray-600 rounded">
                                  {React.createElement(getFileIcon(uploadFile.file), {
                                    className: "w-5 h-5 text-gray-400"
                                  })}
                                </div>
                              )}
                            </div>

                            {/* Informations du fichier */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2">
                                <p className="text-sm font-medium text-white truncate">
                                  {uploadFile.file.name}
                                </p>
                                {getStatusIcon(uploadFile.status)}
                              </div>
                              
                              <div className="flex items-center space-x-4 text-xs text-gray-400">
                                <span>{formatFileSize(uploadFile.file.size)}</span>
                                {uploadFile.wordCount && <span>{uploadFile.wordCount} mots</span>}
                                {uploadFile.pages && <span>{uploadFile.pages} pages</span>}
                                <span className={getStatusColor(uploadFile.status)}>
                                  {uploadFile.status === 'pending' && 'En attente'}
                                  {uploadFile.status === 'uploading' && `Upload... ${uploadFile.progress}%`}
                                  {uploadFile.status === 'processing' && 'Traitement...'}
                                  {uploadFile.status === 'success' && `Succès (ID: ${uploadFile.documentId})`}
                                  {uploadFile.status === 'error' && uploadFile.error}
                                </span>
                              </div>

                              {/* Barre de progression */}
                              {(uploadFile.status === 'uploading' || uploadFile.status === 'processing') && (
                                <div className="w-full h-1 mt-2 bg-gray-600 rounded-full">
                                  <div
                                    className="h-1 transition-all duration-300 bg-blue-500 rounded-full"
                                    style={{ width: `${uploadFile.progress}%` }}
                                  />
                                </div>
                              )}
                            </div>

                            {/* Actions */}
                            <div className="flex items-center space-x-2">
                              {uploadFile.status === 'success' && uploadFile.content && (
                                <motion.button
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                  onClick={() => setSelectedDocument(uploadFile)}
                                  className="p-2 text-blue-400 transition-colors hover:text-blue-300"
                                  title="Aperçu du contenu"
                                >
                                  <EyeIcon className="w-4 h-4" />
                                </motion.button>
                              )}
                              
                              {uploadFile.status === 'error' && (
                                <motion.button
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                  onClick={() => retryProcessing(uploadFile.id)}
                                  className="p-2 text-blue-400 transition-colors hover:text-blue-300"
                                  title="Réessayer"
                                >
                                  <ArrowPathIcon className="w-4 h-4" />
                                </motion.button>
                              )}
                              
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={() => removeFile(uploadFile.id)}
                                className="p-2 text-red-400 transition-colors hover:text-red-300"
                                title="Supprimer"
                              >
                                <XMarkIcon className="w-4 h-4" />
                              </motion.button>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                      
                      {files.length === 0 && (
                        <div className="py-8 text-center text-gray-500">
                          <DocumentIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                          <p>Aucun document uploadé</p>
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </div>
          </div>
        </div>

        {/* Modal de prévisualisation */}
        <AnimatePresence>
          {selectedDocument && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70"
              onClick={() => setSelectedDocument(null)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="w-full max-w-4xl bg-gray-800 rounded-2xl shadow-2xl max-h-[80vh] flex flex-col"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between p-6 border-b border-gray-700">
                  <div>
                    <h3 className="text-xl font-semibold text-white">
                      Aperçu: {selectedDocument.file.name}
                    </h3>
                    <div className="flex items-center mt-1 space-x-4 text-sm text-gray-400">
                      <span>{formatFileSize(selectedDocument.file.size)}</span>
                      {selectedDocument.wordCount && <span>{selectedDocument.wordCount} mots</span>}
                      {selectedDocument.pages && <span>{selectedDocument.pages} pages</span>}
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedDocument(null)}
                    className="text-gray-400 hover:text-white"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
                
                <div className="flex-1 p-6 overflow-y-auto">
                  <div className="p-4 border border-gray-600 rounded-lg bg-gray-900/50">
                    <pre className="font-mono text-sm text-gray-300 whitespace-pre-wrap">
                      {selectedDocument.content?.substring(0, 3000)}
                      {selectedDocument.content && selectedDocument.content.length > 3000 && (
                        <span className="text-gray-500">... (contenu tronqué)</span>
                      )}
                    </pre>
                  </div>
                </div>
                
                <div className="flex justify-end p-6 space-x-3 border-t border-gray-700">
                  <button
                    onClick={() => setSelectedDocument(null)}
                    className="px-4 py-2 text-gray-300 transition-colors border border-gray-600 rounded-lg hover:bg-gray-700"
                  >
                    Fermer
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Layout>
  );
};

export default UploadPage;