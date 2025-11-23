// src/components/documents/DocumentCard.tsx
import { memo, useCallback, useMemo } from 'react';
import { Document } from '@/types';
import { BsFilePdf, BsFileEarmarkText, BsFileEarmarkImage, BsTrash, BsCheckCircle, BsExclamationTriangle, BsInfoCircle } from 'react-icons/bs';

interface DocumentCardProps {
    document: Document;
    onDelete: (documentId: string) => void;
    onDownload: (documentId: string) => void;
    isDeleting?: boolean;
}

const DocumentCard = memo(({
                               document,
                               onDelete,
                               onDownload,
                               isDeleting = false,
                           }: DocumentCardProps) => {
    // handle delete with confirmation
    const handleDelete = useCallback(() => {
        if (confirm('are you sure you want to delete this document?')) {
            onDelete(document.id);
        }
    }, [onDelete, document.id]);

    const handleDownload = useCallback(() => {
        onDownload(document.id);
    }, [onDownload, document.id]);

    // memoize file icon to prevent recreation
    const fileIcon = useMemo(() => {
        const extension = document.title.split('.').pop()?.toLowerCase();
        switch (extension) {
            case 'pdf':
                return <BsFilePdf className="h-6 w-6 text-red-500" />;
            case 'doc':
            case 'docx':
            case 'txt':
                return <BsFileEarmarkText className="h-6 w-6 text-blue-500" />;
            case 'jpg':
            case 'jpeg':
            case 'png':
            case 'gif':
                return <BsFileEarmarkImage className="h-6 w-6 text-green-500" />;
            default:
                return <BsFileEarmarkText className="h-6 w-6 text-gray-500" />;
        }
    }, [document.title]);

    const formattedDate = useMemo(() => {
        const raw = document.uploadedAt;
        if (!raw) return 'N/A';

        const safe = raw.replace(' ', 'T').replace(/\+\d{2}:\d{2}$/, 'Z');
        const date = new Date(safe);

        return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString('en-US', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }, [document.uploadedAt]);


    // determine validation status display
    const validationStatus = useMemo(() => {
        const status = document.status;
        const validationPassed = document.validationPassed;
        const confidence = document.validationConfidence;

        if (status === 'validation_failed' && validationPassed === false) {
            return {
                type: 'warning',
                icon: <BsExclamationTriangle className="h-4 w-4" />,
                text: `might not be ${document.documentType}`,
                bgColor: 'bg-yellow-100',
                textColor: 'text-yellow-800',
                showConfidence: true,
                actionText: 'please verify contents'
            };
        }

        if (status === 'error') {
            return {
                type: 'error',
                icon: <BsExclamationTriangle className="h-4 w-4" />,
                text: 'validation failed',
                bgColor: 'bg-red-100',
                textColor: 'text-red-800',
                showConfidence: false
            };
        }

        // processing states
        if (status === 'pending' || status === 'processing') {
            return {
                type: 'processing',
                icon: <div className="h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />,
                text: 'processing...',
                bgColor: 'bg-blue-100',
                textColor: 'text-blue-800',
                showConfidence: false
            };
        }

        if (status === 'successful') {
            return {
                type: 'completed',
                icon: <BsCheckCircle className="h-4 w-4" />,
                text: 'uploaded successfully',
                bgColor: 'bg-green-100',
                textColor: 'text-green-800',
                showConfidence: false
            };
        }

        return null;
    }, [document.status, document.validationPassed, document.validationConfidence, document.documentType]);

    return (
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
            <div className="flex items-center">
                <div className="h-12 w-12 bg-red-50 rounded-lg flex items-center justify-center mr-4 flex-shrink-0">
                    {fileIcon}
                </div>

                <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate mb-1">{document.title}</h3>
                    <div className="text-xs text-gray-500 mb-2">
                        uploaded on {formattedDate} • {document.documentType.replace('_', ' ')}
                    </div>

                    {/* status badge */}
                    {validationStatus && (
                        <div className="space-y-1">
                            <div className={`inline-flex items-center ${validationStatus.bgColor} ${validationStatus.textColor} text-xs font-medium px-2 py-1 rounded`}>
                                {/*{validationStatus.icon}*/}
                                <span className="ml-1">{validationStatus.text}</span>
                                {validationStatus.showConfidence && document.validationConfidence != null && (
                                    <span className="ml-1 opacity-75">
                                        ({Math.round(document.validationConfidence * 100)}%)
                                    </span>
                                )}
                            </div>
                            {/*<span>{document.documentType}</span>*/}
                            {/*<span>{validationStatus.text}</span>*/}

                            {/* validation warning message */}
                            {validationStatus.actionText && (
                                <div className="flex items-center text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded">
                                    <BsInfoCircle className="h-3 w-3 mr-1 flex-shrink-0" />
                                    <span>{validationStatus.actionText}</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="flex space-x-2 ml-4">
                    <button
                        onClick={handleDownload}
                        className="text-sm text-gray-600 bg-gray-100 px-3 py-1.5 rounded-md hover:bg-gray-200"
                    >
                        view
                    </button>
                    <button
                        onClick={handleDelete}
                        disabled={isDeleting}
                        className="text-sm text-red-600 bg-red-50 px-3 py-1.5 rounded-md hover:bg-red-100 disabled:opacity-50"
                    >
                        {isDeleting ? (
                            <div className="h-3 w-3 border border-red-600 border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <BsTrash className="h-3 w-3" />
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
});

export default DocumentCard;