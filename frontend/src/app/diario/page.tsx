import { redirect } from 'next/navigation';

export default async function DiarioRedirectPage({
  searchParams,
}: {
  // Next 15 can provide searchParams as a Promise during RSC evaluation
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) || undefined;
  const classIdParam = sp?.class_id;
  const classId = Array.isArray(classIdParam) ? classIdParam[0] : classIdParam;

  if (classId) {
    redirect(`/turmas/${classId}/diario`);
  }

  redirect('/classes');
}
