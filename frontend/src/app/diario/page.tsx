import { redirect } from 'next/navigation';

interface DiarioPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export default function DiarioRedirectPage({ searchParams }: DiarioPageProps) {
  const classIdParam = searchParams?.class_id;
  const classId = Array.isArray(classIdParam) ? classIdParam[0] : classIdParam;

  if (classId) {
    redirect(`/turmas/${classId}/diario`);
  }

  redirect('/classes');
}
