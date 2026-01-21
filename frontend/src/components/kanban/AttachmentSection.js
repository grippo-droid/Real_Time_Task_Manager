import React, { useState, useEffect, useRef } from 'react';
import { tasksAPI } from '../../services/api';
import { Paperclip, File as FileIcon, Download, Trash2, Image as ImageIcon } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

export const AttachmentSection = ({ taskId }) => {
    const [attachments, setAttachments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef(null);

    useEffect(() => {
        loadAttachments();
    }, [taskId]);

    const loadAttachments = async () => {
        try {
            const response = await tasksAPI.getAttachments(taskId);
            setAttachments(response.data);
        } catch (error) {
            console.error('Failed to load attachments:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileSelect = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        setUploading(true);
        try {
            const response = await tasksAPI.uploadAttachment(taskId, formData);
            setAttachments([response.data, ...attachments]);
            toast.success('File uploaded');
        } catch (error) {
            console.error('Upload failed:', error);
            toast.error('Failed to upload file');
        } finally {
            setUploading(false);
            // Reset input
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const isImage = (fileType) => fileType.startsWith('image/');

    return (
        <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
                    <Paperclip className="w-4 h-4" />
                    Attachments ({attachments.length})
                </h4>
                <div>
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        className="hidden"
                    // accept="image/*,.pdf,.doc,.docx" // Optional: restrict types
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploading}
                        className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium disabled:opacity-50"
                    >
                        {uploading ? 'Uploading...' : '+ Add File'}
                    </button>
                </div>
            </div>

            {/* Attachments List */}
            <div className="space-y-3">
                {loading ? (
                    <div className="text-center py-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600 mx-auto"></div>
                    </div>
                ) : attachments.length === 0 ? (
                    <p className="text-sm text-gray-500 text-center italic py-2">No attachments yet</p>
                ) : (
                    attachments.map((file) => (
                        <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg group">
                            <div className="flex items-center gap-3 overflow-hidden">
                                <div className="flex-shrink-0 w-10 h-10 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center text-gray-500 dark:text-gray-300">
                                    {isImage(file.file_type) ? (
                                        <ImageIcon className="w-5 h-5" />
                                    ) : (
                                        <FileIcon className="w-5 h-5" />
                                    )}
                                </div>
                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                        <a
                                            href={`http://localhost:8000${file.file_path}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="hover:underline"
                                        >
                                            {file.filename}
                                        </a>
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                        {formatFileSize(file.file_size)} • {formatDistanceToNow(new Date(file.created_at), { addSuffix: true })} • by {file.username}
                                    </p>
                                </div>
                            </div>
                            <div className="flex-shrink-0 ml-2">
                                <a
                                    href={`http://localhost:8000${file.file_path}`}
                                    download={file.filename} // 'download' attribute only works for same-origin or if headers allow
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 block"
                                >
                                    <Download className="w-4 h-4" />
                                </a>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
