import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold mb-4">EpiSphere AI</h1>
          <p className="text-xl mb-8">
            AI-Powered Global Disease Surveillance and Outbreak Intelligence Platform
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/dashboard/global"
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
            >
              View Dashboard
            </Link>
            <Link
              href="/auth/login"
              className="bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">🌍 Global Surveillance</h3>
            <p className="text-gray-600">
              Monitor disease cases worldwide with real-time data visualization and interactive maps.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">🤖 AI Outbreak Detection</h3>
            <p className="text-gray-600">
              Early outbreak signals detected using machine learning and statistical epidemiology.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">📊 Advanced Analytics</h3>
            <p className="text-gray-600">
              Deep epidemiological dashboards with forecasting and trend analysis.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">📤 Data Upload</h3>
            <p className="text-gray-600">
              Countries can upload and share surveillance data via CSV, Excel, or API.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">🔔 Automated Alerts</h3>
            <p className="text-gray-600">
              Receive automated outbreak alerts with severity levels and probability scores.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-3">📈 Forecasting</h3>
            <p className="text-gray-600">
              Short-term forecasts using ARIMA, Prophet, and LSTM models with confidence intervals.
            </p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-gray-100 py-16">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">150+</div>
              <div className="text-gray-600">Countries Monitored</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">7+</div>
              <div className="text-gray-600">Diseases Tracked</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">24/7</div>
              <div className="text-gray-600">Surveillance</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">AI</div>
              <div className="text-gray-600">Powered Detection</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
