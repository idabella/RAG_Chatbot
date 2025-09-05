import React from 'react';
import { motion } from 'framer-motion';
import Layout from '../components/common/Layout';
import ChatInterface from '../components/chat/ChatInterface';

const ChatPage: React.FC = () => {
  return (
    <Layout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="h-[calc(100vh-4rem)] bg-gradient-to-br  from-gray-900 via-gray-950 to-gray-900"
      >
        <div className="relative h-full">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-5">
            <div className="absolute inset-0" style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%233B82F6' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
            }} />
          </div>
          
          {/* Chat Interface with enhanced styling */}
          <div className="relative z-10 h-full ">
            <ChatInterface />
          </div>
        </div>
      </motion.div>
    </Layout>
  );
};

export default ChatPage;