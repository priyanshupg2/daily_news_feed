export default function FeedPage() {
  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">Daily News Feed</h1>
      <p className="text-gray-500 mb-8">Your personalized AI & tech intelligence briefing</p>

      <div className="mb-6">
        {/* PromptInput will go here */}
      </div>

      <div className="space-y-6">
        <div className="border border-dashed border-gray-300 rounded-xl p-8 text-center text-gray-400">
          No feed items yet. Run the discovery pipeline to get started.
        </div>
      </div>
    </main>
  );
}
