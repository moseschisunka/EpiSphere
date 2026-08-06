export default function Loading() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
      <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-600"></div>
      <p className="text-gray-500 font-medium">Loading Dashboard Data...</p>
    </div>
  );
}
