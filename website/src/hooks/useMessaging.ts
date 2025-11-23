// ===== website/src/hooks/useMessaging.ts (UPDATED FOR BACKEND) =====
import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api';

interface Message {
    id: string;
    sender: 'user' | 'assistant';
    content: string;
    response_time?: number;
    model_used?: string;
    created_at: string;
}

interface Conversation {
    id: string;
    title: string;
    message_count: number;
    messages: Message[];
    created_at: string;
    updated_at: string;
}

export const useMessaging = () => {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
    const [loading, setLoading] = useState(false);
    const [sending, setSending] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // fetch all conversations
    const fetchConversations = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('📱 fetching conversations...');
            const response = await apiClient.get('/messaging/conversations/');

            setConversations(response.data.results || response.data || []);
            console.log('✅ conversations loaded:', response.data.results?.length || response.data?.length || 0);
        } catch (err: any) {
            console.log('❌ failed to fetch conversations:', err);
            // don't show error for now - conversations might not exist yet
            setConversations([]);
        } finally {
            setLoading(false);
        }
    }, []);

    // fetch specific conversation with messages
    const fetchConversation = useCallback(async (conversationId: string) => {
        try {
            setLoading(true);
            setError(null);

            console.log('💬 fetching conversation:', conversationId);
            const response = await apiClient.get(`/messaging/conversations/${conversationId}/`);

            setCurrentConversation(response.data);
            console.log('✅ conversation loaded with', response.data.messages?.length || 0, 'messages');
        } catch (err: any) {
            console.log('❌ failed to fetch conversation:', err);
            setError(err.response?.data?.detail || 'failed to load conversation');
        } finally {
            setLoading(false);
        }
    }, []);

    // send a message
    const sendMessage = useCallback(async (
        messageContent: string,
        conversationId?: string
    ): Promise<{ conversation_id: string; user_message: Message; ai_message: Message }> => {
        try {
            setSending(true);
            setError(null);

            console.log('📤 sending message...');
            const response = await apiClient.post('/messaging/send-message/', {
                message: messageContent,
                conversation_id: conversationId
            });

            const { conversation_id, user_message, ai_message } = response.data;

            // update current conversation if it matches
            if (currentConversation && currentConversation.id === conversation_id) {
                setCurrentConversation(prev => ({
                    ...prev!,
                    messages: [...prev!.messages, user_message, ai_message],
                    message_count: prev!.message_count + 2
                }));
            } else if (!currentConversation) {
                // new conversation created
                setCurrentConversation({
                    id: conversation_id,
                    title: user_message.content.substring(0, 50),
                    message_count: 2,
                    messages: [user_message, ai_message],
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                });
            }

            // update conversations list
            setConversations(prev => {
                const existingIndex = prev.findIndex(conv => conv.id === conversation_id);
                if (existingIndex >= 0) {
                    // update existing conversation
                    const updated = [...prev];
                    updated[existingIndex] = {
                        ...updated[existingIndex],
                        message_count: updated[existingIndex].message_count + 2,
                        updated_at: new Date().toISOString()
                    };
                    return updated;
                } else {
                    // add new conversation
                    const newConv = {
                        id: conversation_id,
                        title: user_message.content.substring(0, 50),
                        message_count: 2,
                        messages: [],
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString()
                    };
                    return [newConv, ...prev];
                }
            });

            console.log('✅ message sent successfully');
            return response.data;

        } catch (err: any) {
            console.log('❌ failed to send message:', err);
            setError(err.response?.data?.error || 'failed to send message');
            throw err;
        } finally {
            setSending(false);
        }
    }, [currentConversation]);

    // start new conversation
    const startNewConversation = useCallback(() => {
        setCurrentConversation(null);
        setError(null);
    }, []);

    // delete conversation
    const deleteConversation = useCallback(async (conversationId: string) => {
        try {
            await apiClient.delete(`/messaging/conversations/${conversationId}/`);

            setConversations(prev => prev.filter(conv => conv.id !== conversationId));

            if (currentConversation?.id === conversationId) {
                setCurrentConversation(null);
            }

            console.log('✅ conversation deleted');
        } catch (err: any) {
            console.log('❌ failed to delete conversation:', err);
            setError(err.response?.data?.detail || 'failed to delete conversation');
            throw err;
        }
    }, [currentConversation]);

    // load conversations on mount
    useEffect(() => {
        fetchConversations();
    }, [fetchConversations]);

    return {
        // state
        conversations,
        currentConversation,
        loading,
        sending,
        error,

        // actions
        fetchConversations,
        fetchConversation,
        sendMessage,
        startNewConversation,
        deleteConversation,
        setError,

        // computed
        hasConversations: conversations.length > 0,
        currentMessages: currentConversation?.messages || []
    };
};