// src/components/documents/DocumentEmbeddingStatus.tsx
import { BsCheckCircle, BsArrowClockwise, BsExclamationTriangle, BsClock, BsRobot } from 'react-icons/bs';

interface DocumentEmbeddingStatusProps {
    documentId: string;
    embeddingStatus?: {
        status: 'pending' | 'embedding' | 'success' | 'error' | 'auto_processing';
        error?: string;
        embeddedAt?: Date;
        chunks?: number;
    };
    onManualEmbed?: (documentId: string) => void;
    compact?: boolean;
}

export default function DocumentEmbeddingStatus({
                                                    documentId,
                                                    embeddingStatus,
                                                    compact = false
                                                }: DocumentEmbeddingStatusProps) {
    if (!embeddingStatus) {
        return null;
    }

    const { status, error, embeddedAt, chunks } = embeddingStatus;

    const getStatusInfo = () => {
        switch (status) {
            case 'success':
                return {
                    icon: <BsCheckCircle className="h-4 w-4 text-green-500" />,
                    text: compact ? 'embedded' : `embedded${chunks ? ` (${chunks} chunks)` : ''}`,
                    subtext: embeddedAt ? `embedded ${embeddedAt.toLocaleDateString()}` : '',
                    className: 'text-green-600',
                    bgClassName: 'bg-green-50'
                };
            case 'embedding':
                return {
                    icon: <BsArrowClockwise className="h-4 w-4 text-blue-500 animate-spin" />,
                    text: 'embedding...',
                    subtext: 'processing for AI chat',
                    className: 'text-blue-600',
                    bgClassName: 'bg-blue-50'
                };
            case 'auto_processing':
                return {
                    icon: <BsRobot className="h-4 w-4 text-blue-500" />,
                    text: 'processing...',
                    subtext: 'OCR + auto-embedding',
                    className: 'text-blue-600',
                    bgClassName: 'bg-blue-50'
                };
            case 'pending':
                return {
                    icon: <BsClock className="h-4 w-4 text-yellow-500" />,
                    text: 'pending',
                    subtext: 'ready to embed',
                    className: 'text-yellow-600',
                    bgClassName: 'bg-yellow-50'
                };
            case 'error':
                return {
                    icon: <BsExclamationTriangle className="h-4 w-4 text-red-500" />,
                    text: 'failed',
                    subtext: error || 'embedding failed',
                    className: 'text-red-600',
                    bgClassName: 'bg-red-50'
                };
            default:
                return null;
        }
    };

    const statusInfo = getStatusInfo();
    if (!statusInfo) return null;

    if (compact) {
        return (
            <div className="flex items-center">
                {statusInfo.icon}
                <span className={`text-xs ml-1 ${statusInfo.className}`}>
                    {statusInfo.text}
                </span>
            </div>
        );
    }
}
