// src/hooks/useDocuments.ts - Updated for S3 pre-signed URLs
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api';
import { BackendDocument, Document } from '@/types';
import {backdropClasses} from "@mui/material";

// transform backend document to frontend format (same as before)
const transformDocument = (backendDoc: BackendDocument): Document => ({
    id: backendDoc.id,
    title: backendDoc.title,
    documentType: backendDoc.document_type,
    fileUrl: backendDoc.file,
    fileSize: backendDoc.file_size_display,
    status: backendDoc.status,
    extractedData: backendDoc.extracted_data,
    uploadedAt: backendDoc.uploaded_at,
    processedAt: backendDoc.processed_at,
    validationPassed: backendDoc.validation_passed,
    validationConfidence: backendDoc.validation_confidence,
    validationNotes: backendDoc.validation_notes,
    validationCompleted_at: backendDoc.validation_completed_at,
});

// client-side title sanitization (same as before)
const sanitizeTitle = (title: string) => {
    return title
        .replace(/[<>]/g, '') // remove html tags
        .replace(/[\/\\]/g, '-') // replace path separators
        .replace(/['"]/g, '') // remove quotes
        .replace(/\.\./g, '') // remove parent directory references
        .trim()
        .substring(0, 50); // limit length
};

// client-side filename validation
const validateFileClient = (file: File): string | null => {
    // file size validation
    const maxSize = 25 * 1024 * 1024; // 25MB
    if (file.size > maxSize) {
        return `file size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds maximum allowed size (25MB)`;
    }

    // file extension validation
    const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.rtf', '.gif', '.bmp', '.tiff', '.tif'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExtensions.includes(fileExtension)) {
        return `file type "${fileExtension}" not allowed. allowed types: ${allowedExtensions.join(', ')}`;
    }

    return null; // no errors
};

export const useDocuments = () => {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchDocuments = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('📄 fetching documents from api...');
            const response = await apiClient.get('/documents/');

            // console.log("backend docs", response.data.results)

            const transformedDocuments = response.data.results.map((doc: BackendDocument) => transformDocument(doc));

            console.log('✅ documents loaded:', transformedDocuments);
            setDocuments(transformedDocuments);
        } catch (err: any) {
            console.log('❌ error fetching documents:', err);
            setError(err.response?.data?.detail || 'failed to load documents');
        } finally {
            setLoading(false);
        }
    };

    // upload using s3 pre-signed urls
    const uploadDocument = async (
        file: File,
        title: string,
        documentType: string,
        onProgress?: (progress: number) => void
    ): Promise<Document> => {
        try {
            setUploading(true);
            setError(null);

            // client-side validation first
            const validationError = validateFileClient(file);
            if (validationError) {
                throw new Error(validationError);
            }

            // sanitize title on client side
            const sanitizedTitle = sanitizeTitle(title);
            if (!sanitizedTitle) {
                throw new Error('document title is required');
            }

            console.log('🔄 requesting upload url...');

            // step 1: request pre-signed upload url
            const uploadUrlResponse = await apiClient.post('/documents/request_upload_url/', {
                title: sanitizedTitle,
                document_type: documentType,
                filename: file.name,
                file_size: file.size
            });

            const {
                document_id,
                upload_url,
                upload_fields,
                s3_key
            } = uploadUrlResponse.data;

            console.log('✅ got upload url, uploading to s3...');

            // step 2: upload file directly to s3
            const formData = new FormData();

            // add all the required fields from pre-signed post
            Object.keys(upload_fields).forEach(key => {
                formData.append(key, upload_fields[key]);
            });

            // add the file last
            formData.append('file', file);

            // upload to s3 with progress tracking
            await new Promise<void>((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.upload.addEventListener('progress', (event) => {
                    if (event.lengthComputable && onProgress) {
                        const progress = Math.round((event.loaded * 100) / event.total);
                        onProgress(progress);
                    }
                });

                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve();
                    } else {
                        reject(new Error(`s3 upload failed with status ${xhr.status}`));
                    }
                });

                xhr.addEventListener('error', () => {
                    reject(new Error('s3 upload failed'));
                });

                xhr.open('POST', upload_url);
                xhr.send(formData);
            });

            console.log('✅ file uploaded to s3, confirming...');

            // step 3: confirm upload with our backend
            const confirmResponse = await apiClient.post(`/documents/${document_id}/confirm_upload/`);

            const newDocument = transformDocument(confirmResponse.data);
            console.log('✅ upload confirmed:', newDocument);

            // add to documents list
            setDocuments(prev => [newDocument, ...prev]);

            return newDocument;

        } catch (err: any) {
            console.log('❌ upload failed:', err);

            let errorMessage = 'failed to upload document';

            if (err.message) {
                // client-side validation or network error
                errorMessage = err.message;
            } else if (err.response?.data?.details) {
                // server-side validation errors
                const details = err.response.data.details;
                if (typeof details === 'string') {
                    errorMessage = details;
                } else if (typeof details === 'object') {
                    // extract first error message
                    const firstError = Object.values(details)[0];
                    if (Array.isArray(firstError)) {
                        errorMessage = firstError[0];
                    } else {
                        errorMessage = String(firstError);
                    }
                }
            } else if (err.response?.data?.error) {
                errorMessage = err.response.data.error;
            }

            setError(errorMessage);
            throw new Error(errorMessage);
        } finally {
            setUploading(false);
        }
    };

    // fallback: direct upload for legacy support
    const uploadDocumentDirect = async (
        file: File,
        title: string,
        documentType: string,
        onProgress?: (progress: number) => void
    ): Promise<Document> => {
        try {
            setUploading(true);
            setError(null);

            // client-side validation
            const validationError = validateFileClient(file);
            if (validationError) {
                throw new Error(validationError);
            }

            const sanitizedTitle = sanitizeTitle(title);

            console.log('📝 uploading document directly (legacy mode)...');

            // create form data for direct upload
            const formData = new FormData();
            formData.append('file', file);
            formData.append('title', sanitizedTitle);
            formData.append('document_type', documentType);

            const response = await apiClient.post('/documents/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.total && onProgress) {
                        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        onProgress(progress);
                    }
                }
            });

            const newDocument = transformDocument(response.data);
            console.log('✅ direct upload completed:', newDocument);

            setDocuments(prev => [newDocument, ...prev]);
            return newDocument;

        } catch (err: any) {
            console.log('❌ direct upload failed:', err);

            let errorMessage = 'failed to upload document';
            if (err.response?.data?.details?.file) {
                errorMessage = Array.isArray(err.response.data.details.file)
                    ? err.response.data.details.file[0]
                    : err.response.data.details.file;
            } else if (err.message) {
                errorMessage = err.message;
            }

            setError(errorMessage);
            throw new Error(errorMessage);
        } finally {
            setUploading(false);
        }
    };

    // delete a document
    const deleteDocument = async (documentId: string) => {
        try {
            await apiClient.delete(`/documents/${documentId}/`);
            setDocuments(prev => prev.filter(doc => doc.id !== documentId));
            console.log('✅ document deleted:', documentId);
        } catch (err: any) {
            console.log('❌ failed to delete document:', err);
            throw err;
        }
    };

    // download a document (now with s3 pre-signed urls)
    const downloadDocument = async (documentId: string) => {
        try {
            console.log('🔗 getting download url...');
            const response = await apiClient.get(`/documents/${documentId}/download/`);

            if (response.data.download_url) {
                console.log('✅ got download url, opening...');
                // open download url in new tab
                window.open(response.data.download_url, '_blank');
            } else {
                throw new Error('no download url received');
            }
        } catch (err: any) {
            console.log('❌ failed to download document:', err);
            throw err;
        }
    };

    // get storage statistics
    const getStorageStats = async () => {
        try {
            const response = await apiClient.get('/documents/storage_stats/');
            return response.data;
        } catch (err: any) {
            console.log('❌ failed to get storage stats:', err);
            throw err;
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    return {
        documents,
        loading,
        uploading,
        error,
        uploadDocument, // primary s3 upload method
        uploadDocumentDirect, // fallback direct upload
        deleteDocument,
        downloadDocument,
        getStorageStats,
        refetch: fetchDocuments,
        setError,
    };
};