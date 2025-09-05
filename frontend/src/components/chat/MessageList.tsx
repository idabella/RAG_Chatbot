// src/components/chat/MessageList.tsx - CORRIGÉ avec interface unifiée
import React from 'react';
import MessageItem from './MessageItem';

// Interface unifiée - doit être identique partout
interface Message {
  id: number;
  type: 'user' | 'bot' | 'system';
  content: string;
  file?: File;
  timestamp: Date;
  isGenerating?: boolean; // ← Propriété unifiée
}

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
    </div>
  );
};

export default MessageList;