// fetch validation statuses for documents - REMOVED since it's already in document data
// useEffect(() => {
//     const fetchValidationStatuses = async () => {
//         // src/app/(dashboard)/documents_essays/documents/page.tsx
'use client';

import {useState, useCallback, useEffect} from 'react';
import { useDocuments } from '@/hooks/useDocuments';
import DocumentList from '@/components/documents/DocumentList';
import DocumentUploadModal from '@/components/documents/DocumentUploadModal';
import { BsLightbulb, BsFileEarmarkText, BsExclamationTriangle, BsX, BsShieldExclamation } from 'react-icons/bs';

export default function DocumentsPage() {
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
    const {
        documents,
        loading,
        uploading,
        error,
        uploadDocument,
        deleteDocument,
        downloadDocument,
        setError,
        refetch
    } = useDocuments();

    // log validation data from documents for debugging
    useEffect(() => {
        if (documents.length > 0) {
            console.log('📊 documents with validation data:', documents.map(doc => ({
                id: doc.id,
                title: doc.title,
                document_type: doc.documentType,
                validation_passed: doc.validationPassed,
                validation_confidence: doc.validationConfidence,
                validation_notes: doc.validationNotes
            })));
        }
    }, [documents]);

    useEffect(() => {
        let interval: NodeJS.Timeout;

        if (!uploading && documents.some(doc =>
            ['processing', 'pending'].includes(doc.status)
        )) {
            interval = setInterval(() => {
                refetch();
            }, 3000); // poll every 3s
        }

        return () => clearInterval(interval); // cleanup
    }, [documents, uploading, refetch]);

    // show upload modal
    const handleShowUploadModal = useCallback(() => {
        setShowUploadModal(true);
    }, []);

    // hide upload modal
    const handleCloseUploadModal = useCallback(() => {
        setShowUploadModal(false);
        setUploadProgress(0);
    }, []);

    // handle document upload
    const handleUpload = useCallback(async (
        file: File,
        title: string,
        documentType: string
    ) => {
        try {
            await uploadDocument(file, title, documentType, setUploadProgress);
        } catch (error) {
            console.log('upload failed:', error);
            throw error;
        }
    }, [uploadDocument]);

    // handle document deletion with optimistic updates
    const handleDelete = useCallback(async (documentId: string) => {
        setDeletingIds(prev => new Set(prev).add(documentId));
        try {
            await deleteDocument(documentId);
        } catch (error) {
            console.log('delete failed:', error);
        } finally {
            setDeletingIds(prev => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
            });
        }
    }, [deleteDocument]);

    // handle document download
    const handleDownload = useCallback(async (documentId: string) => {
        try {
            await downloadDocument(documentId);
        } catch (error) {
            console.log('download failed:', error);
        }
    }, [downloadDocument]);

    // clear error
    const handleClearError = useCallback(() => {
        setError(null);
    }, [setError]);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-gray-500">loading documents...</div>
            </div>
        );
    };

    // count validation issues - use document data directly
    const validationIssues = documents.filter(doc => {
        return doc.validationPassed === false || (doc.validationConfidence != null && doc.validationConfidence < 0.3);
    });

    return (
        <>
            {/* tip banner */}
            <div className="bg-blue-100 rounded-xl p-4 mb-6 flex items-center">
                <div className="h-8 w-8 bg-yellow-400 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                    <BsLightbulb className="text-white h-4 w-4" />
                </div>
                <div className="text-sm text-blue-900">
                    <div className="font-medium">upload your documents</div>
                    <div>we'll extract key information to improve recommendations</div>
                </div>
            </div>

            {/* validation warning banner */}
            {validationIssues.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 flex items-start">
                    <BsShieldExclamation className="text-amber-600 h-5 w-5 mr-3 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <div className="text-amber-800 font-medium">
                            {validationIssues.length} document{validationIssues.length > 1 ? 's' : ''} may not match the declared type
                        </div>
                        <div className="text-amber-700 text-sm mt-1">
                            These documents were processed but may not contain the expected content patterns.
                            Consider checking if you selected the correct document type.
                        </div>
                        <div className="mt-2 text-xs text-amber-600">
                            {validationIssues.map(doc => (
                                <div key={doc.id} className="flex justify-between">
                                    <span>"{doc.title}" (declared: {doc.documentType})</span>
                                    <span>
                                      confidence: {doc.validationConfidence != null ? (doc.validationConfidence * 100).toFixed(1) + '%' : 'N/A'}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* error display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-start">
                    <BsExclamationTriangle className="text-red-500 h-5 w-5 mr-3 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <div className="text-red-800 font-medium">upload failed</div>
                        <div className="text-red-600 text-sm">{error}</div>
                    </div>
                    <button
                        onClick={handleClearError}
                        className="ml-auto text-red-400 hover:text-red-600"
                    >
                        <BsX className="h-5 w-5" />
                    </button>
                </div>
            )}

            <DocumentList
                documents={documents}
                onDelete={handleDelete}
                onDownload={handleDownload}
                deletingIds={deletingIds}
                // validation data is already in documents
            />

            {/* upload area */}
            <div
                className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center bg-white cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
                onClick={handleShowUploadModal}
            >
                <div className="mx-auto h-12 w-12 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
                    <BsFileEarmarkText className="h-6 w-6 text-gray-500" />
                </div>
                <h3 className="text-base font-medium text-gray-900 mb-1">upload a document</h3>
                <p className="text-sm text-gray-500 mb-4">transcripts, test scores, etc.</p>
                <button className="inline-flex items-center px-4 py-2 bg-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-300 focus:outline-none transition-colors">
                    choose file
                </button>
            </div>

            <DocumentUploadModal
                isOpen={showUploadModal}
                onClose={handleCloseUploadModal}
                onUpload={handleUpload}
                uploading={uploading}
                uploadProgress={uploadProgress}
            />
        </>
    );
}