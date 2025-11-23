// src/components/profile/ProfileAvatar.tsx
import { memo, useCallback, useState } from 'react';
import { UserProfile } from '@/types';
import { BsCamera } from 'react-icons/bs';

interface ProfileAvatarProps {
    profile: UserProfile;
    onAvatarUpload: (file: File) => Promise<void>;
    updating: boolean;
}

const ProfileAvatar = memo(({
                                profile,
                                onAvatarUpload,
                                updating
                            }: ProfileAvatarProps) => {
    const [uploading, setUploading] = useState(false);

    const handleFileChange = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setUploading(true);
        try {
            await onAvatarUpload(file);
        } catch (error) {
            console.log('avatar upload failed:', error);
        } finally {
            setUploading(false);
        }
    }, [onAvatarUpload]);

    return (
        <div className="relative">
            {profile.avatar ? (
                <img
                    src={profile.avatar}
                    alt="profile avatar"
                    className="h-24 w-24 rounded-full object-cover"
                />
            ) : (
                <div className="h-24 w-24 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 text-3xl font-medium">
                    {profile.user.initials}
                </div>
            )}

            <label className={`absolute bottom-0 right-0 bg-blue-600 text-white p-2 rounded-full cursor-pointer hover:bg-blue-700 transition-colors ${
                (updating || uploading) ? 'opacity-50 cursor-not-allowed' : ''
            }`}>
                <BsCamera className="h-3 w-3" />
                <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="hidden"
                    disabled={updating || uploading}
                />
            </label>

            {uploading && (
                <div className="absolute inset-0 bg-black bg-opacity-50 rounded-full flex items-center justify-center">
                    <div className="h-6 w-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                </div>
            )}
        </div>
    );
});

export default ProfileAvatar;