// src/components/documents/DocumentList.tsx
import { memo, useCallback } from 'react';
import { Document } from '@/types';
import DocumentCard from './DocumentCard';

interface DocumentListProps {
    documents: Document[];
    onDelete: (documentId: string) => void;
    onDownload: (documentId: string) => void;
    deletingIds: Set<string>;
    // embeddingStatuses?: {[documentId: string]: any};
}

const DocumentList = memo(({
                               documents,
                               onDelete,
                               onDownload,
                               deletingIds,
                               // embeddingStatuses
                           }: DocumentListProps) => {
    if (documents.length === 0) {
        return (
            <div className="text-center py-8">
                <div className="text-gray-500">no documents uploaded yet</div>
            </div>
        );
    }

    return (
        <div className="space-y-3 mb-6">
            {documents.map((document) => (
                <DocumentCard
                    key={document.id}
                    document={document}
                    onDelete={onDelete}
                    onDownload={onDownload}
                    isDeleting={deletingIds.has(document.id)}
                    // embeddingStatuses={embeddingStatuses}
                />
            ))}
        </div>
    );
});

export default DocumentList;