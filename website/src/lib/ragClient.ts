// src/lib/ragClient.ts - focused only on RAG functionality

import apiClient from './api';
import React from "react";

interface RAGContext {
    content: string;
    type: 'profile' | 'document';
    source: string;
    similarity: number;
    metadata?: any;
}

interface RAGStats {
    total_chunks: number;
    profile_chunks: number;
    document_chunks: number;
    unique_documents: number;
    last_update?: string;
}

class BackendRAGClient {
    // embed user profile - NO PARAMETERS (backend builds text from user's database data)
    async embedProfile(): Promise<{success: boolean; message?: string; error?: string}> {
        try {
            console.log('📝 embedding user profile via backend...');
            const response = await apiClient.post('/messaging/rag/profile/');
            console.log('✅ profile embedded successfully');
            return { success: true, message: response.data.message };
        } catch (error: any) {
            console.error('❌ profile embedding failed:', error);
            return {
                success: false,
                error: error.response?.data?.error || error.message
            };
        }
    }

    // embed document - only document ID needed (backend extracts text via OCR)
    async embedDocument(documentId: string): Promise<{success: boolean; message?: string; error?: string}> {
        try {
            console.log(`📄 embedding document ${documentId} via backend...`);
            const response = await apiClient.post('/messaging/rag/document/', {
                document_id: documentId
            });
            console.log(`✅ document ${documentId} embedded: ${response.data.chunks_created} chunks created`);
            return {
                success: true,
                message: `document embedded successfully (${response.data.chunks_created} chunks)`
            };
        } catch (error: any) {
            console.error(`❌ document embedding failed:`, error);
            return {
                success: false,
                error: error.response?.data?.error || error.message
            };
        }
    }

    // embed raw text directly (for custom text embedding)
    async embedText(text: string): Promise<{success: boolean; embedding?: number[]; error?: string}> {
        try {
            console.log(`🔤 embedding raw text via backend (${text.length} chars)...`);
            const response = await apiClient.post('/messaging/embed/', { text });
            console.log('✅ text embedded successfully');
            return { success: true, embedding: response.data.embedding };
        } catch (error: any) {
            console.error('❌ text embedding failed:', error);
            return {
                success: false,
                error: error.response?.data?.error || error.message
            };
        }
    }

    // retrieve context for query
    async retrieveContext(query: string, topK: number = 5): Promise<{
        contexts: RAGContext[];
        hasContext: boolean;
        error?: string;
    }> {
        try {
            console.log(`🔍 retrieving context for query: "${query}"`);
            const response = await apiClient.post('/messaging/rag/retrieve/', {
                query,
                top_k: topK
            });
            console.log(`📊 found ${response.data.contexts.length} relevant contexts`);
            return {
                contexts: response.data.contexts,
                hasContext: response.data.has_context
            };
        } catch (error: any) {
            console.error('❌ context retrieval failed:', error);
            return {
                contexts: [],
                hasContext: false,
                error: error.response?.data?.error || error.message
            };
        }
    }

    // build contextual prompt
    async buildContextualPrompt(query: string, maxContextLength: number = 3000): Promise<{
        systemPrompt: string;
        userPrompt: string;
        contextsUsed: any[];
        hasContext: boolean;
        error?: string;
    }> {
        try {
            console.log(`🔄 building contextual prompt for: "${query}"`);
            const response = await apiClient.post('/messaging/rag/prompt/', {
                query,
                max_context_length: maxContextLength
            });
            console.log(`📝 contextual prompt built (${response.data.contexts_used.length} contexts used)`);
            return {
                systemPrompt: response.data.system_prompt,
                userPrompt: response.data.user_prompt,
                contextsUsed: response.data.contexts_used,
                hasContext: response.data.has_context
            };
        } catch (error: any) {
            console.error('❌ contextual prompt building failed:', error);
            return {
                systemPrompt: "you are a college application advisor. the user hasn't provided much information yet.",
                userPrompt: query,
                contextsUsed: [],
                hasContext: false,
                error: error.response?.data?.error || error.message
            };
        }
    }

    // get rag stats
    async getStats(): Promise<{stats: RAGStats; ready: boolean; error?: string}> {
        try {
            const response = await apiClient.get('/messaging/rag/stats/');
            return {
                stats: response.data.user_stats,
                ready: response.data.system_ready
            };
        } catch (error: any) {
            console.error('❌ failed to get rag stats:', error);
            return {
                stats: {
                    total_chunks: 0,
                    profile_chunks: 0,
                    document_chunks: 0,
                    unique_documents: 0
                },
                ready: false,
                error: error.response?.data?.error || error.message
            };
        }
    }

    // check if profile is embedded
    async hasProfileEmbedding(): Promise<boolean> {
        try {
            const response = await apiClient.get('/messaging/rag/profile/');
            return response.data.has_profile_embedding;
        } catch (error) {
            console.error('❌ failed to check profile embedding status:', error);
            return false;
        }
    }

    // clear all rag data
    async clearData(): Promise<{success: boolean; message: string}> {
        try {
            const response = await apiClient.delete('/messaging/rag/stats/');
            return {
                success: response.data.cleared,
                message: response.data.message
            };
        } catch (error: any) {
            console.error('❌ failed to clear rag data:', error);
            return {
                success: false,
                message: error.response?.data?.error || error.message
            };
        }
    }

    // check if rag is ready
    async isRAGReady(): Promise<boolean> {
        const { ready } = await this.getStats();
        return ready;
    }

    // get document embedding stats
    async getEmbeddingStats(): Promise<any> {
        try {
            const response = await apiClient.get('/documents/embedding_stats/');
            return response.data;
        } catch (error: any) {
            console.error('❌ failed to get embedding stats:', error);
            return { error: error.response?.data?.error || error.message };
        }
    }

    // initialize rag for new users
    async initializeRAGForUser(): Promise<{success: boolean; message: string}> {
        try {
            console.log('🚀 initializing rag for user...');

            // embed profile first
            const profileResult = await this.embedProfile();
            if (!profileResult.success) {
                return {
                    success: false,
                    message: `profile embedding failed: ${profileResult.error}`
                };
            }

            // get user's documents and embed them
            const documentsResponse = await apiClient.get('/documents/');
            const documents = documentsResponse.data.results || [];

            let embeddedCount = 0;
            for (const doc of documents) {
                if (doc.status === 'completed') {
                    const docResult = await this.embedDocument(doc.id);
                    if (docResult.success) {
                        embeddedCount++;
                    }
                }
            }

            return {
                success: true,
                message: `rag initialized: profile + ${embeddedCount} documents embedded`
            };
        } catch (error: any) {
            console.error('❌ rag initialization failed:', error);
            return {
                success: false,
                message: error.response?.data?.error || error.message
            };
        }
    }
}

// create singleton instance
export const ragClient = new BackendRAGClient();

// helper hook for react components
export function useRAG() {
    const [stats, setStats] = React.useState<RAGStats | null>(null);
    const [isReady, setIsReady] = React.useState(false);
    const [loading, setLoading] = React.useState(true);

    const refreshStats = async () => {
        setLoading(true);
        const result = await ragClient.getStats();
        setStats(result.stats);
        setIsReady(result.ready);
        setLoading(false);
    };

    React.useEffect(() => {
        refreshStats();
    }, []);

    return {
        stats,
        isReady,
        loading,
        refreshStats,

        // RAG-specific methods only
        embedProfile: ragClient.embedProfile.bind(ragClient),
        embedDocument: ragClient.embedDocument.bind(ragClient),
        embedText: ragClient.embedText.bind(ragClient),
        retrieveContext: ragClient.retrieveContext.bind(ragClient),
        buildContextualPrompt: ragClient.buildContextualPrompt.bind(ragClient),
        clearData: ragClient.clearData.bind(ragClient),
        initializeRAG: ragClient.initializeRAGForUser.bind(ragClient),
        getEmbeddingStats: ragClient.getEmbeddingStats.bind(ragClient),
        hasProfileEmbedding: ragClient.hasProfileEmbedding.bind(ragClient)
    };
}