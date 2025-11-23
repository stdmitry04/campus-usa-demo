// src/types/index.ts

// ==========================================
// UNIVERSITY TYPES
// ==========================================

// backend university type (matches django serializer)
import {string} from "prop-types";

export interface BackendUniversity {
    id: number;
    name: string;
    location: string;
    city: string;
    state: string;
    rank: number;
    admission_chance: number;
    admission_chance_display: string;
    acceptance_rate: number;
    acceptance_rate_display: string;
    avg_sat_score: number;
    avg_gpa: number;
    annual_tuition: number;
    tuition_display: string;
    has_financial_aid: boolean;
    website_url: string;
    logo: string | undefined;
    created_at: string;
    updated_at: string;
}

// frontend university type (what components expect)
export interface University {
    id: number;
    name: string;
    location: string;
    rank: number;
    admissionChance: string;
    acceptanceRate: string;
    avgSAT: number;
    avgGPA: number;
    annualTuition: string;
    hasFinancialAid: boolean;
    websiteUrl?: string;
    logo?: string;
}

// ==========================================
// DOCUMENT TYPES
// ==========================================

export interface BackendDocument {
    id: string;
    title: string;
    document_type: string;
    file: string;
    file_size_display: string;
    extracted_data: any;
    uploaded_at: string;
    processed_at: string | null;

    status: 'pending' | 'processing' | 'completed' | 'successful' | 'validation_failed' | 'failed' | 'error';

    // validation fields
    validation_passed?: boolean | null;
    validation_confidence?: number | null;
    validation_notes?: string;
    validation_completed_at?: string | null;
}

export interface Document {
    id: string;
    title: string;
    documentType: string;
    fileUrl: string;
    fileSize: string;
    status: 'pending' | 'processing' | 'completed' | 'successful' | 'validation_failed' | 'failed' | 'error';
    extractedData: any;
    uploadedAt: string;
    processedAt: string | null;

    // validation fields
    validationPassed?: boolean | null;
    validationConfidence?: number | null;
    validationNotes?: string;
    validationCompleted_at?: string | null;
}

// ==========================================
// ESSAY TYPES
// ==========================================

export interface Essay {
    id: string;
    title: string;
    createdOn: string;
    content: string;
}

// ==========================================
// PROFILE TYPES (ENHANCED STRUCTURE)
// ==========================================

export enum AidLevel {
    None = 0,
    Partial = 1,
    Full = 2,
}

export enum DegreeType {
    Bachelor = 'bachelor',
    Master = 'master',
    PhD = 'phd',
}

// 🔹 Backend types (what Django sends)

export interface BackendUser {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    phone_number?: string; // ✅ Add this
}


export interface BackendAcademicInfo {
    high_school_name: string;
    graduation_year: number;
    gpa: number;
    gpa_scale: string;
    sat_score?: number;
    act_score?: number;
    toefl_score?: number;
    ielts_score?: number;
    class_rank?: number;
    class_size?: number;
    created_at: string;
    updated_at: string;
}

export interface BackendPreferences {
    applying_for: string; // bachelor, master, phd
    fields_of_interest: string[];
    preferred_ranking_min: number;
    preferred_ranking_max: number;
    need_financial_aid: AidLevel; // 0=none, 1=partial, 2=full
}

export interface BackendUserProfile {
    user: BackendUser;
    avatar?: string;
    phone_number?: string;
    preferences?: BackendPreferences | null; // allow null
    academic_info?: BackendAcademicInfo | null;
    saved_universities?: number[];
    full_name: string;
    initials: string;
    created_at: string;
    updated_at: string;
}

// 🔹 Frontend types (what components use)

export interface FrontendUser {
    id: number;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    fullName: string;
    initials: string;
    phoneNumber: string;
}

export interface AcademicInfo {
    highSchoolName: string;
    graduationYear: number;
    gpa: number;
    gpaScale: string;
    satScore?: number;
    actScore?: number;
    toeflScore?: number;
    ieltsScore?: number;
    classRank?: number;
    classSize?: number;
}

export interface Preferences {
    applyingFor: DegreeType;
    fieldsOfInterest: string[];
    universityRankingMin: number;
    universityRankingMax: number;
    needFinancialAid: AidLevel;
}

export interface UserProfile {
    user: FrontendUser;
    avatar?: string;
    phoneNumber: string;
    preferences: Preferences;
    academic?: AcademicInfo;
    savedUniversityIds: number[];
    createdAt: string;
    updatedAt: string;
}

// 🔹 Update types for forms

export interface UserUpdateData {
    firstName?: string;
    lastName?: string;
    email?: string;
}

export interface ProfileUpdateData {
    phoneNumber?: string;
    avatar?: File;
}

export interface PreferencesUpdateData {
    applyingFor?: DegreeType;
    fieldsOfInterest?: string[];
    universityRankingMin?: number;
    universityRankingMax?: number;
    needFinancialAid?: AidLevel;
}

export interface AcademicUpdateData {
    highSchoolName?: string;
    graduationYear?: number;
    gpa?: number;
    gpaScale?: string;
    satScore?: number;
    actScore?: number;
    toeflScore?: number;
    ieltsScore?: number;
    classRank?: number;
    classSize?: number;
}

// 🔹 API response types

export interface ProfileResponse {
    profile: BackendUserProfile;
    completion_percentage: number;
}

export interface AcademicResponse {
    academic_info: BackendAcademicInfo;
}

export interface PreferencesResponse {
    preferences: BackendPreferences;
}

// 🔹 Utility types

export interface ProfileCompletion {
    overall: number;
    sections: {
        basic: number;
        academic: number;
        preferences: number;
    };
    missing_fields: string[];
}

export interface ProfileStats {
    saved_universities: number;
    documents_uploaded: number;
    essays_written: number;
    chat_conversations: number;
    profile_completion: ProfileCompletion;
}

// 🔹 Transform functions

export const transformBackendUser = (backendUser: BackendUser): FrontendUser => ({
    id: backendUser.id,
    username: backendUser.username,
    email: backendUser.email,
    firstName: backendUser.first_name || '',
    lastName: backendUser.last_name || '',
    fullName: `${backendUser.first_name || ''} ${backendUser.last_name || ''}`.trim() || backendUser.username,
    initials: backendUser.first_name && backendUser.last_name
        ? `${backendUser.first_name[0]}${backendUser.last_name[0]}`.toUpperCase()
        : backendUser.username.slice(0, 2).toUpperCase(),
    phoneNumber: backendUser.phone_number || '',
});


export const transformBackendAcademic = (backendAcademic: BackendAcademicInfo): AcademicInfo => ({
    highSchoolName: backendAcademic.high_school_name,
    graduationYear: backendAcademic.graduation_year,
    gpa: backendAcademic.gpa,
    gpaScale: backendAcademic.gpa_scale,
    satScore: backendAcademic.sat_score,
    actScore: backendAcademic.act_score,
    toeflScore: backendAcademic.toefl_score,
    ieltsScore: backendAcademic.ielts_score,
    classRank: backendAcademic.class_rank,
    classSize: backendAcademic.class_size,
});

export const transformBackendPreferences = (backendPreferences: BackendPreferences | null | undefined): Preferences => {
    // provide default values if preferences are null/undefined
    if (!backendPreferences) {
        return {
            applyingFor: DegreeType.Bachelor,
            fieldsOfInterest: [],
            universityRankingMin: 0,
            universityRankingMax: 500,
            needFinancialAid: AidLevel.None,
        };
    }

    return {
        applyingFor: backendPreferences.applying_for as DegreeType,
        fieldsOfInterest: backendPreferences.fields_of_interest || [],
        universityRankingMin: backendPreferences.preferred_ranking_min || 0,
        universityRankingMax: backendPreferences.preferred_ranking_max || 500,
        needFinancialAid: backendPreferences.need_financial_aid || AidLevel.None,
    };
};

export const transformBackendProfile = (backendProfile: BackendUserProfile): UserProfile => ({
    user: transformBackendUser(backendProfile.user),
    avatar: backendProfile.avatar,
    phoneNumber: backendProfile.phone_number || '',
    preferences: transformBackendPreferences(backendProfile.preferences),
    academic: backendProfile.academic_info ? transformBackendAcademic(backendProfile.academic_info) : undefined,
    savedUniversityIds: backendProfile.saved_universities || [],
    createdAt: backendProfile.created_at,
    updatedAt: backendProfile.updated_at,
});

// 🔹 Reverse transform functions (for API calls)

export const transformFrontendUser = (frontendUser: Partial<FrontendUser>): Partial<BackendUser> => {
    const result: Partial<BackendUser> & { phone_number?: string } = {
        first_name: frontendUser.firstName,
        last_name: frontendUser.lastName,
        email: frontendUser.email,
    };

    if (frontendUser.phoneNumber) {
        result.phone_number = frontendUser.phoneNumber;
    }

    return result;
};

export const transformFrontendAcademic = (frontendAcademic: Partial<AcademicInfo>): Partial<BackendAcademicInfo> => ({
    high_school_name: frontendAcademic.highSchoolName,
    graduation_year: frontendAcademic.graduationYear,
    gpa: frontendAcademic.gpa,
    gpa_scale: frontendAcademic.gpaScale,
    sat_score: frontendAcademic.satScore,
    act_score: frontendAcademic.actScore,
    toefl_score: frontendAcademic.toeflScore,
    ielts_score: frontendAcademic.ieltsScore,
    class_rank: frontendAcademic.classRank,
    class_size: frontendAcademic.classSize,
});

export const transformFrontendPreferences = (frontendPreferences: Partial<Preferences>): Partial<BackendPreferences> => ({
    applying_for: frontendPreferences.applyingFor,
    fields_of_interest: frontendPreferences.fieldsOfInterest,
    preferred_ranking_min: frontendPreferences.universityRankingMin,
    preferred_ranking_max: frontendPreferences.universityRankingMax,
    need_financial_aid: frontendPreferences.needFinancialAid,
});

// 🔹 Validation helpers

export const validateAcademicInfo = (academic: Partial<AcademicInfo>): string[] => {
    const errors: string[] = [];

    if (!academic.highSchoolName?.trim()) {
        errors.push('high school name is required');
    }

    if (!academic.graduationYear || academic.graduationYear < 2000 || academic.graduationYear > 2030) {
        errors.push('graduation year must be between 2000 and 2030');
    }

    if (!academic.gpa || academic.gpa < 0 || academic.gpa > 4) {
        errors.push('gpa must be between 0 and 4');
    }

    if (academic.satScore && (academic.satScore < 400 || academic.satScore > 1600)) {
        errors.push('sat score must be between 400 and 1600');
    }

    if (academic.actScore && (academic.actScore < 1 || academic.actScore > 36)) {
        errors.push('act score must be between 1 and 36');
    }

    return errors;
};

export const validatePreferences = (preferences: Partial<Preferences>): string[] => {
    const errors: string[] = [];

    if (!preferences.applyingFor) {
        errors.push('degree type is required');
    }

    if (!preferences.fieldsOfInterest || preferences.fieldsOfInterest.length === 0) {
        errors.push('at least one field of interest is required');
    }

    if (preferences.universityRankingMin !== undefined && preferences.universityRankingMax !== undefined) {
        if (preferences.universityRankingMin > preferences.universityRankingMax) {
            errors.push('minimum ranking cannot be greater than maximum ranking');
        }
    }

    return errors;
};

// 🔹 User stats type
export interface UserStats {
    saved_universities: number;
    documents_uploaded: number;
    essays_written: number;
    chat_conversations: number;
    profile_completion: number;
}

export interface ChecklistItem {
    id: string;
    label: string;
    completed: boolean;
    required: boolean;
    description?: string;
}

export interface ChecklistSection {
    id: string;
    title: string;
    icon: React.ReactNode;
    items: ChecklistItem[];
    completedCount: number;
    totalRequired: number;
    totalItems: number;
    status: 'complete' | 'partial' | 'incomplete';
}

export interface ContactInfoFormProps {
    profile: UserProfile;
    onSave: (data: ProfileUpdateData) => Promise<void>;
    onCancel: () => void;
    updating: boolean;
}

export interface ContextQuality {
    hasProfile: boolean;
    hasDocuments: boolean;
    contextCount: number;
    averageSimilarity: number;
    usedSources: string[];
}

export interface Message {
    id: string;
    sender: 'user' | 'assistant';
    content: string;
    response_time?: number;
    model_used?: string;
    created_at: string;
    metadata?: {
        context_quality?: ContextQuality;
        used_sources?: string[];
        embedding_status?: {
            profile_status: string;
            documents_embedded: number;
            documents_embedding: number;
            documents_errors: number;
        };
        rag_version?: string;
        [key: string]: any;
    };
}

export interface Conversation {
    id: string;
    title: string;
    message_count: number;
    messages: Message[];
    created_at: string;
    updated_at: string;
    metadata?: {
        context_ready?: boolean;
        profile_embedded?: boolean;
        documents_embedded?: number;
        [key: string]: any;
    };
}