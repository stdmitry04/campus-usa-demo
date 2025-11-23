interface PageHeaderProps {
    title: string;
}

export default function PageHeader({ title }: PageHeaderProps) {
    return (
        <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        </div>
    );
}