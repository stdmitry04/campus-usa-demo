// src/hooks/useRAGMessaging.ts - simplified single-call approach
import { useState, useCallback } from 'react';
import { useRAGProfile } from './useRAGProfile';
import { useRAGDocuments } from './useRAGDocuments';
import { Conversation } from '@/types/';
import apiClient from '@/lib/api';
import { useAuth } from "@/context/AuthContext";

export const useRAGMessaging = () => {
  const { profile, isEmbedded: profileEmbedded, embeddingStatus: profileStatus, embeddingError: profileError } = useRAGProfile();
  const { documents, embeddedCount, embeddingCount, errorCount, allDocumentsEmbedded } = useRAGDocuments();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<Error | string | null>(null);
  const { user } = useAuth();
  const [lastRagInfo, setLastRagInfo] = useState<any>(null);

  // check if system is ready for high-quality responses
  const isSystemReady = profileEmbedded && embeddedCount > 0 && embeddingCount === 0;
  const hasEmbeddingErrors = !!profileError || errorCount > 0;

  // send message with automatic backend rag - single api call!
  const sendMessage = useCallback(async (messageContent: string, conversationId?: string) => {
    if (!profile || !user) {
      throw new Error('profile not loaded or user not authenticated');
    }

    try {
      setSending(true);
      setError(null);

      console.log('🤖 sending message with automatic backend rag...');

      // single api call - backend handles everything internally
      const response = await apiClient.post('/messaging/send-message/', {
        message: messageContent,
        conversation_id: conversationId,
        use_rag: true, // let backend decide based on available context
        metadata: {
          frontend_context: {
            profile_embedded: profileEmbedded,
            documents_embedded: embeddedCount,
            documents_embedding: embeddingCount,
            system_ready: isSystemReady
          },
          timestamp: Date.now()
        }
      });

      const { conversation_id, user_message, ai_message, conversation, rag_info } = response.data;

      // store rag info for debugging/ui
      setLastRagInfo(rag_info);

      console.log('📤 message sent successfully');
      console.log('📊 rag info:', rag_info);

      // update current conversation if it matches
      if (currentConversation && currentConversation.id === conversation_id) {
        setCurrentConversation(prev => {
          if (!prev) return prev;

          return {
            ...prev,
            messages: [...prev.messages, user_message, ai_message],
            message_count: conversation.message_count
          };
        });
      } else {
        // set as current conversation if it's new
        const updatedConversation = {
          ...conversation,
          messages: [user_message, ai_message]
        };
        setCurrentConversation(updatedConversation);

        // add to conversations list if not already there
        setConversations(prev => {
          const existing = prev.find(c => c.id === conversation_id);
          if (existing) {
            return prev.map(c => c.id === conversation_id ? updatedConversation : c);
          } else {
            return [updatedConversation, ...prev];
          }
        });
      }

      return response.data;

    } catch (err: any) {
      console.log('❌ failed to send message:', err);

      let errorMessage = 'failed to send message';

      if (err.response?.status === 429) {
        errorMessage = 'too many requests. please wait a moment.';
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (err.message?.includes('network')) {
        errorMessage = 'network error. please check your connection.';
      }

      setError(errorMessage);
      throw err;
    } finally {
      setSending(false);
    }
  }, [profile, user, currentConversation, profileEmbedded, embeddedCount, embeddingCount, isSystemReady]);

  // start new conversation
  const startNewConversation = useCallback(async (initialMessage?: string) => {
    if (!profile) return;

    try {
      setLoading(true);
      setError(null);

      if (initialMessage) {
        // start with a message - backend will create conversation automatically
        const response = await sendMessage(initialMessage);
        return response.conversation;
      } else {
        // start empty conversation
        const response = await apiClient.post('/messaging/start-conversation/', {
          metadata: {
            context_ready: isSystemReady,
            profile_embedded: profileEmbedded,
            documents_embedded: embeddedCount
          }
        });

        const conversation = response.data.conversation || response.data;
        setCurrentConversation(conversation);
        setConversations(prev => [conversation, ...prev]);

        return conversation;
      }

    } catch (err: any) {
      console.log('❌ failed to start conversation:', err);
      setError(err.response?.data?.error || 'failed to start conversation');
    } finally {
      setLoading(false);
    }
  }, [profile, sendMessage, isSystemReady, profileEmbedded, embeddedCount]);

  // load conversations
  const loadConversations = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/messaging/conversations/');
      setConversations(response.data.conversations || response.data);
    } catch (err: any) {
      console.log('❌ failed to load conversations:', err);
      setError('failed to load conversations');
    } finally {
      setLoading(false);
    }
  }, []);

  // load specific conversation
  const loadConversation = useCallback(async (conversationId: string) => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/messaging/conversations/${conversationId}/`);
      setCurrentConversation(response.data);
    } catch (err: any) {
      console.log('❌ failed to load conversation:', err);
      setError('failed to load conversation');
    } finally {
      setLoading(false);
    }
  }, []);

  // get system status for debugging
  const getSystemStatus = useCallback(async () => {
    try {
      const response = await apiClient.get('/messaging/rag/stats/');
      const { user_stats, embedding_stats, system_ready } = response.data;

      return {
        // frontend status
        profileStatus,
        profileError,
        documentsEmbedded: embeddedCount,
        documentsEmbedding: embeddingCount,
        documentsErrors: errorCount,
        allDocumentsEmbedded,
        isSystemReady,
        hasEmbeddingErrors,

        // backend status
        backendStats: {
          user_stats,
          embedding_stats,
          system_ready
        },

        // last interaction
        lastRagInfo
      };
    } catch (error) {
      console.log('failed to get system status:', error);
      return {
        profileStatus,
        profileError,
        documentsEmbedded: embeddedCount,
        documentsEmbedding: embeddingCount,
        documentsErrors: errorCount,
        allDocumentsEmbedded,
        isSystemReady,
        hasEmbeddingErrors,
        lastRagInfo
      };
    }
  }, [profileStatus, profileError, embeddedCount, embeddingCount, errorCount, allDocumentsEmbedded, isSystemReady, hasEmbeddingErrors, lastRagInfo]);

  return {
    // conversation state
    conversations,
    currentConversation,
    loading,
    sending,
    error,

    // actions - now simplified!
    sendMessage, // single call handles everything
    startNewConversation,
    loadConversations,
    loadConversation,

    // status & debugging
    getSystemStatus,
    lastRagInfo, // info about last rag usage

    // status indicators
    isSystemReady,
    hasEmbeddingErrors,
    profileEmbedded,
    documentsEmbedded: embeddedCount,
    allDocumentsEmbedded
  };
};

// example usage in a component:
/*
const ChatComponent = () => {
  const { sendMessage, sending, lastRagInfo, isSystemReady } = useRAGMessaging();

  const handleSendMessage = async (message: string) => {
    try {
      await sendMessage(message);
      // that's it! backend handles rag automatically
    } catch (error) {
      console.error('failed to send:', error);
    }
  };

  return (
    <div>
      {isSystemReady && <div>✅ rag context ready</div>}
      {lastRagInfo?.rag_used && (
        <div>🎯 last message used {lastRagInfo.contexts_used} contexts</div>
      )}
      <button onClick={() => handleSendMessage("what are my chances at mit?")}>
        Send Message
      </button>
    </div>
  );
};
*/