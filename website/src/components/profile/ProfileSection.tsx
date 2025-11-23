// src/components/profile/ProfileSection.tsx
import { memo } from 'react';
import { BsPencil, BsTrash } from 'react-icons/bs';

interface ProfileSectionProps {
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
    isEditing: boolean;
    onEdit: () => void;
    onCancel: () => void;
    showDelete?: boolean;
    onDelete?: () => void;
}

const ProfileSection = memo(({
                                 title,
                                 icon,
                                 children,
                                 isEditing,
                                 onEdit,
                                 showDelete = false,
                                 onDelete
                             }: ProfileSectionProps) => {
    return (
        <div className="mb-8 last:mb-0">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                    {icon}
                    <span className="ml-2">{title}</span>
                </h3>
                {!isEditing && (
                    <div className="flex space-x-2">
                        <button
                            onClick={onEdit}
                            className="text-blue-600 text-sm font-medium hover:text-blue-700 flex items-center"
                        >
                            <BsPencil className="h-3 w-3 mr-1" />
                            edit
                        </button>
                        {showDelete && onDelete && (
                            <button
                                onClick={onDelete}
                                className="text-red-600 text-sm font-medium hover:text-red-700 flex items-center"
                            >
                                <BsTrash className="h-3 w-3 mr-1" />
                                delete
                            </button>
                        )}
                    </div>
                )}
            </div>
            {children}
        </div>
    );
});

ProfileSection.displayName = 'ProfileSection';
export default ProfileSection;