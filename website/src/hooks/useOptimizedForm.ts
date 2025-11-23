// src/hooks/useOptimizedForm.ts
import { useState, useCallback, useMemo } from 'react';

interface UseOptimizedFormOptions<T> {
    initialValues: T;
    onSubmit: (values: T) => Promise<void>;
    validate?: (values: T) => Partial<Record<keyof T, string>>;
}

export const useOptimizedForm = <T extends Record<string, any>>({
                                                                    initialValues,
                                                                    onSubmit,
                                                                    validate
                                                                }: UseOptimizedFormOptions<T>) => {
    const [values, setValues] = useState<T>(initialValues);
    const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [touched, setTouched] = useState<Set<keyof T>>(new Set());

    // validate form values
    type ValidationErrors<T> = Partial<Record<keyof T, string>>;
    const validationErrors = useMemo<ValidationErrors<typeof values>>(() => {
        return validate ? validate(values) : {};
    }, [values, validate]);


    // check if form is valid
    const isValid = useMemo(() => {
        return Object.keys(validationErrors).length === 0;
    }, [validationErrors]);

    // handle field changes
    const handleChange = useCallback((field: keyof T) => (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
    ) => {
        const value = e.target.type === 'checkbox'
            ? (e.target as HTMLInputElement).checked
            : e.target.value;

        setValues(prev => ({ ...prev, [field]: value }));

        // clear error when user starts typing
        if (errors[field]) {
            setErrors(prev => {
                const newErrors = { ...prev };
                delete newErrors[field];
                return newErrors;
            });
        }
    }, [errors]);

    // handle field blur
    const handleBlur = useCallback((field: keyof T) => () => {
        setTouched(prev => new Set(prev).add(field));

        // show validation error for this field
        if (validationErrors[field]) {
            setErrors(prev => ({ ...prev, [field]: validationErrors[field] }));
        }
    }, [validationErrors]);

    // handle form submission
    const handleSubmit = useCallback(async (e: React.FormEvent) => {
        e.preventDefault();

        // mark all fields as touched
        setTouched(new Set(Object.keys(values) as Array<keyof T>));

        // show all validation errors
        setErrors(validationErrors);

        if (!isValid) return;

        setIsSubmitting(true);
        try {
            await onSubmit(values);
        } finally {
            setIsSubmitting(false);
        }
    }, [values, validationErrors, isValid, onSubmit]);

    // reset form
    const reset = useCallback(() => {
        setValues(initialValues);
        setErrors({});
        setTouched(new Set());
    }, [initialValues]);

    return {
        values,
        errors,
        touched,
        isSubmitting,
        isValid,
        handleChange,
        handleBlur,
        handleSubmit,
        reset,
    };
};
