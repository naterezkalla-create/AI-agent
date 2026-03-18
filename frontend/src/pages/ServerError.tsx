import React from "react";
import { useNavigate } from "react-router-dom";
import { Home, RefreshCw } from "lucide-react";

export const ServerError: React.FC = () => {
  const navigate = useNavigate();

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="text-center">
        {/* 500 Large Text */}
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-pink-600">
            500
          </h1>
        </div>

        {/* Message */}
        <h2 className="text-4xl font-bold text-white mb-4">Server Error</h2>
        <p className="text-xl text-gray-400 mb-8 max-w-md mx-auto">
          Something went wrong on our end. Our team has been notified, and we're working to fix it.
        </p>

        {/* Error Details */}
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mb-8 max-w-md mx-auto text-left">
          <p className="text-sm text-red-400">
            <strong>Error Code:</strong> Internal Server Error
          </p>
          <p className="text-sm text-red-400 mt-2">
            Please try again in a few moments. If the problem persists, contact support.
          </p>
        </div>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={handleRefresh}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-lg font-medium hover:from-purple-700 hover:to-purple-600 transition"
          >
            <RefreshCw size={20} />
            Try Again
          </button>
          <button
            onClick={() => navigate("/")}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition"
          >
            <Home size={20} />
            Go Home
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServerError;
