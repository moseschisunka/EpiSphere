import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center bg-white p-10 rounded-xl shadow-lg border border-gray-100">
        <div>
          <h2 className="mt-6 text-6xl font-extrabold text-indigo-600">404</h2>
          <h3 className="mt-4 text-2xl font-bold text-gray-900">Page Not Found</h3>
          <p className="mt-2 text-sm text-gray-600">
            The page you are looking for doesn&apos;t exist or has been moved.
          </p>
        </div>
        <div className="mt-8">
          <Link
            href="/dashboard/global"
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
