// src/hooks/useRAGDocuments.ts - enhanced documents hook with detailed status tracking
import { useEffect, useRef, useState } from 'react';
import { useDocuments } from '@/hooks/useDocuments';
import { useAuth} from '@/context/AuthContext';
import { ragClient } from '@/lib/ragClient';

interface DocumentEmbeddingStatus {
    [documentId: string]: {
        status: 'pending' | 'embedding' | 'success' | 'error';
        error?: string;
        embeddedAt?: Date;
    };
}

export const useRAGDocuments = () => {
    const documentsHook = useDocuments();
    const { documents, loading, error } = documentsHook;
    const { user } = useAuth();
    const [embeddingStatuses, setEmbeddingStatuses] = useState<DocumentEmbeddingStatus>({});

    // auto-embed new documents
    useEffect(() => {
        if (!documents || loading || documents.length === 0) return;
        if (!user || !user.id) return;

        const userId = user.id.toString();
        if (!userId) return;

        // find new documents that haven't been embedded
        const newDocuments = documents.filter(doc =>
            doc.status === 'completed' && // only embed processed documents
            !embeddingStatuses[doc.id.toString()] // not yet tracked
        );

        if (newDocuments.length === 0) return;

        console.log(`🔄 embedding ${newDocuments.length} new documents...`);

        // mark documents as pending
        const newStatuses = { ...embeddingStatuses };
        newDocuments.forEach(doc => {
            newStatuses[doc.id.toString()] = { status: 'pending' };
        });
        setEmbeddingStatuses(newStatuses);

        // embed each new document
        newDocuments.forEach(async (doc) => {
            const docId = doc.id.toString();

            try {
                // update status to embedding
                setEmbeddingStatuses(prev => ({
                    ...prev,
                    [docId]: { status: 'embedding' }
                }));

                await ragClient.embedDocument(docId);

                // update status to success
                setEmbeddingStatuses(prev => ({
                    ...prev,
                    [docId]: {
                        status: 'success',
                        embeddedAt: new Date()
                    }
                }));

                console.log(`✅ document ${docId} embedded successfully`);

            } catch (error) {
                console.log(`❌ failed to embed document ${docId}:`, error);

                // update status to error
                setEmbeddingStatuses(prev => ({
                    ...prev,
                    [docId]: {
                        status: 'error',
                        error: (error as Error).message || 'embedding failed'
                    }
                }));
            }
        });
    }, [documents, loading, embeddingStatuses]);

    const embeddedCount = Object.values(embeddingStatuses).filter(
        status => status.status === 'success'
    ).length;

    const embeddingCount = Object.values(embeddingStatuses).filter(
        status => status.status === 'embedding'
    ).length;

    const errorCount = Object.values(embeddingStatuses).filter(
        status => status.status === 'error'
    ).length;

    return {
        ...documentsHook,
        embeddedCount,
        embeddingCount,
        errorCount,
        embeddingStatuses,
        allDocumentsEmbedded: documents.length > 0 && embeddedCount === documents.filter(d => d.status === 'completed').length
    };
};