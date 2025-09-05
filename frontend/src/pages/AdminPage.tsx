import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  DocumentTextIcon, 
  UsersIcon, 
  ChartBarIcon, 
  CpuChipIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import Layout from '../components/common/Layout';

interface Stat {
  name: string;
  value: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color: string;
}

interface Document {
  id: number;
  name: string;
  size: string;
  uploadDate: string;
  status: string;
}

interface User {
  id: number;
  name: string;
  email: string;
  lastActive: string;
  documents: number;
}

interface Tab {
  id: string;
  name: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('documents');

  const stats: Stat[] = [
    { name: 'Documents Totaux', value: '156', icon: DocumentTextIcon, color: 'text-blue-600' },
    { name: 'Utilisateurs Actifs', value: '89', icon: UsersIcon, color: 'text-green-600' },
    { name: 'Conversations', value: '1,234', icon: ChartBarIcon, color: 'text-purple-600' },
    { name: 'Requêtes IA', value: '5,678', icon: CpuChipIcon, color: 'text-orange-600' }
  ];

  const documents: Document[] = [
    { id: 1, name: 'Guide Utilisateur.pdf', size: '2.4 MB', uploadDate: '2025-01-15', status: 'Traité' },
    { id: 2, name: 'Rapport Financier.docx', size: '1.8 MB', uploadDate: '2025-01-14', status: 'En cours' },
    { id: 3, name: 'Présentation.pdf', size: '5.2 MB', uploadDate: '2025-01-13', status: 'Traité' }
  ];

  const users: User[] = [
    { id: 1, name: 'Jean Dupont', email: 'jean@example.com', lastActive: '2025-01-15', documents: 12 },
    { id: 2, name: 'Marie Martin', email: 'marie@example.com', lastActive: '2025-01-14', documents: 8 },
    { id: 3, name: 'Pierre Durand', email: 'pierre@example.com', lastActive: '2025-01-13', documents: 15 }
  ];

  const tabs: Tab[] = [
    { id: 'documents', name: 'Documents', icon: DocumentTextIcon },
    { id: 'users', name: 'Utilisateurs', icon: UsersIcon },
    { id: 'analytics', name: 'Analytics', icon: ChartBarIcon },
    { id: 'monitoring', name: 'Monitoring', icon: CpuChipIcon }
  ];

  return (
    <Layout>
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Administration</h1>
          <p className="text-gray-600">Gestion du système FetChat</p>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          {stats.map((stat, index) => (
            <div
              key={stat.name}
              className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
              </div>
            </div>
          ))}
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-white rounded-xl shadow-sm border border-gray-200"
        >
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <tab.icon className="h-5 w-5" />
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Gestion des Documents</h2>
                  <button className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200">
                    <PlusIcon className="h-4 w-4" />
                    <span>Nouveau Document</span>
                  </button>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Nom</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Taille</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Date</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Statut</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {documents.map((doc) => (
                        <tr key={doc.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-gray-900">{doc.name}</td>
                          <td className="py-3 px-4 text-gray-600">{doc.size}</td>
                          <td className="py-3 px-4 text-gray-600">{doc.uploadDate}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              doc.status === 'Traité' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {doc.status}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex space-x-2">
                              <button className="text-blue-600 hover:text-blue-800">
                                <EyeIcon className="h-4 w-4" />
                              </button>
                              <button className="text-red-600 hover:text-red-800">
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Gestion des Utilisateurs</h2>
                  <button className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200">
                    <PlusIcon className="h-4 w-4" />
                    <span>Nouvel Utilisateur</span>
                  </button>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Nom</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Email</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Dernière Connexion</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Documents</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-gray-900">{user.name}</td>
                          <td className="py-3 px-4 text-gray-600">{user.email}</td>
                          <td className="py-3 px-4 text-gray-600">{user.lastActive}</td>
                          <td className="py-3 px-4 text-gray-600">{user.documents}</td>
                          <td className="py-3 px-4">
                            <div className="flex space-x-2">
                              <button className="text-blue-600 hover:text-blue-800">
                                <EyeIcon className="h-4 w-4" />
                              </button>
                              <button className="text-red-600 hover:text-red-800">
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* Analytics Tab */}
            {activeTab === 'analytics' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="text-center py-12"
              >
                <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-medium text-gray-900 mb-2">Analytics Dashboard</h3>
                <p className="text-gray-600">Les graphiques et métriques détaillées seront disponibles ici.</p>
              </motion.div>
            )}

            {/* Monitoring Tab */}
            {activeTab === 'monitoring' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="text-center py-12"
              >
                <CpuChipIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-medium text-gray-900 mb-2">System Monitoring</h3>
                <p className="text-gray-600">Surveillance en temps réel du système et des performances.</p>
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>
    </Layout>
  );
};

export default AdminPage;