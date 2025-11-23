// src/app/(dashboard)/page.tsx - redirect to dashboard
import { redirect } from 'next/navigation';

export default function DashboardIndexPage() {
    redirect('/checklist');
}