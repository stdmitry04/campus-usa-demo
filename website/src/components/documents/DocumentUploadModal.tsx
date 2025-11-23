// src/components/documents/DocumentUploadModal.tsx
import { memo, useCallback, useState, useMemo } from 'react';
import { BsX } from 'react-icons/bs';

interface DocumentUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUpload: (file: File, title: string, type: string) => Promise<void>;
    uploading: boolean;
    uploadProgress: number;
}

const DOCUMENT_TYPES = [
    { value: 'transcript', label: 'high school transcript' },
    { value: 'sat_score', label: 'sat score report' },
    { value: 'act_score', label: 'act score report' },
    { value: 'toefl_score', label: 'toefl score report' },
    { value: 'ielts_score', label: 'ielts score report' },
    { value: 'recommendation', label: 'letter of recommendation' },
    { value: 'personal_statement', label: 'personal statement' },
    { value: 'bank_statement', label: 'bank statement' },
    { value: 'i20', label: 'i-20 form' },
    { value: 'passport', label: 'passport copy' },
    { value: 'visa', label: 'visa document' },
    { value: 'other', label: 'other' },
];

const DocumentUploadModal = memo(({
                                      isOpen,
                                      onClose,
                                      onUpload,
                                      uploading,
                                      uploadProgress
                                  }: DocumentUploadModalProps) => {
    const [formData, setFormData] = useState({
        title: '',
        documentType: 'transcript',
        file: null as File | null
    });

    // file validation with useMemo to prevent recalculation
    const validationError = useMemo(() => {
        if (!formData.file) return null;

        const maxSize = 25 * 1024 * 1024; // 25MB
        if (formData.file.size > maxSize) {
            return `file size (${(formData.file.size / 1024 / 1024).toFixed(1)}MB) exceeds 25MB limit`;
        }

        const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png'];
        const extension = '.' + formData.file.name.split('.').pop()?.toLowerCase();
        if (!allowedExtensions.includes(extension)) {
            return `file type ${extension} not allowed`;
        }

        return null;
    }, [formData.file]);

    const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setFormData(prev => ({
                ...prev,
                file,
                // autofill title if empty
                title: prev.title || file.name.split('.')[0]
            }));
        }
    }, []);

    const handleInputChange = useCallback((field: string) => (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
        setFormData(prev => ({ ...prev, [field]: e.target.value }));
    }, []);

    const handleSubmit = useCallback(async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.file || validationError) return;

        try {
            await onUpload(formData.file, formData.title, formData.documentType);
            // reset form
            setFormData({ title: '', documentType: 'transcript', file: null });
            onClose();
        } catch (error) {
            console.log('upload failed:', error);
        }
    }, [formData, validationError, onUpload, onClose]);

    const handleClose = useCallback(() => {
        if (!uploading) {
            setFormData({ title: '', documentType: 'transcript', file: null });
            onClose();
        }
    }, [uploading, onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-semibold text-gray-900">upload document</h3>
                    <button
                        onClick={handleClose}
                        disabled={uploading}
                        className="text-gray-400 hover:text-gray-600 p-1 disabled:opacity-50"
                    >
                        <BsX className="h-6 w-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            document type
                        </label>
                        <select
                            value={formData.documentType}
                            onChange={handleInputChange('documentType')}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            disabled={uploading}
                            required
                        >
                            {DOCUMENT_TYPES.map(type => (
                                <option key={type.value} value={type.value}>
                                    {type.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            title
                        </label>
                        <input
                            type="text"
                            value={formData.title}
                            onChange={handleInputChange('title')}
                            placeholder="enter a descriptive title"
                            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            disabled={uploading}
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            file
                        </label>
                        <input
                            type="file"
                            onChange={handleFileSelect}
                            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
                            disabled={uploading}
                            required
                        />
                        {validationError && (
                            <p className="text-xs text-red-500 mt-1">{validationError}</p>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                            max 25mb. supports: pdf, doc, docx, txt, jpg, png
                        </p>
                    </div>

                    {uploading && (
                        <div className="bg-gray-50 rounded-lg p-3">
                            <div className="flex justify-between text-sm text-gray-700 mb-2">
                                <span>uploading...</span>
                                <span>{uploadProgress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                    style={{ width: `${uploadProgress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    <div className="flex space-x-3 pt-2">
                        <button
                            type="button"
                            onClick={handleClose}
                            disabled={uploading}
                            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors"
                        >
                            cancel
                        </button>
                        <button
                            type="submit"
                            disabled={uploading || !formData.file || !!validationError}
                            className="flex-1 px-4 py-2.5 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                            {uploading ? 'uploading...' : 'upload'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
});

export default DocumentUploadModal;